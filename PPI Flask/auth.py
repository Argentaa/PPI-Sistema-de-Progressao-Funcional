from flask import render_template, request, redirect, url_for, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from . import db, serializer, mail      
from .models import User

auth = Blueprint('auth', __name__, template_folder='templates\home')

@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('docente.home_docente'))
    else:
        return render_template("login.html")

@auth.route('/login', methods=["GET", "POST"])
def login_post():
    cursor = db.cursor()

    if request.method=='POST':
        CPF = request.form['CPF']
        Senha = request.form['Senha']
        lembrar = True if request.form.get('lembrarSenha') else False

        cursor.execute("""SELECT * FROM docente WHERE CPF=%s""", (CPF,))
        record = cursor.fetchone()
        
        if record and check_password_hash(record[5], Senha):
            if record[20] == 'Inativo':
                flash('Você deve ativar sua conta, verifique seu email!')
            else:
                if record[6] == 1:
                    flash('Logado com sucesso!')
                    login_user(User(record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7]))
                    return redirect(url_for('cppd.cppd_home'))
                
                login_user(User(record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7]))
                flash('Logado com sucesso!')
                return redirect(url_for('docente.home_docente'))
        
        else:
            flash('Dados Incorretos, Verifique seus dados.')
            return redirect(url_for('auth.login'))

    return render_template("login.html")

@auth.route('/ativar_conta/<token>')
def ativar_conta(token):
    
    cursor = db.cursor()
    
    cursor.execute("""SELECT token_reset FROM docente WHERE token_reset=%s""", (token,))
    TokenDocente = cursor.fetchone()
    
    try:
        if TokenDocente:
            cursor.execute("""SELECT id FROM docente WHERE token_reset=%s""", (token,))
            idDocente = cursor.fetchone()
                
            cursor.execute("""UPDATE docente SET status=%s WHERE id=%s""", ('Ativo', *idDocente))
            cursor.execute("""UPDATE docente SET token_reset=NULL WHERE id=%s""", (*idDocente,))
            db.commit()
                
            return render_template("ativar_conta.html")
        else:
            return render_template('token_expirado.html')
    except:
        return render_template('token_expirado.html')
    

@auth.route('/registrar')
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for('docente.home_docente'))
    else:
        return render_template("registrar.html")

@auth.route('/registrar', methods=["GET", "POST"])
def registrar_post():
    cursor = db.cursor()
    if request.method == 'POST':
        CPF = request.form['CPF']
        SIAPE = request.form['SIAPE']
        Nome = request.form['Nome']
        Email = request.form['Email']
        Senha = request.form['Senha']
        CPPD = 0

    cursor.execute("""SELECT * FROM docente WHERE CPF=%s""", (CPF,))
    info = cursor.fetchone()
    
    token = serializer.dumps(Email, salt='activate-account')

    if info is None:
        cursor.execute("""INSERT INTO docente (CPF, SIAPE, Nome, Email, Senha, CPPD, token_reset, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", 
                        (CPF,SIAPE,Nome,Email,generate_password_hash(Senha, method='sha256'),CPPD, token, 'Inativo'))
        db.commit()
        
        reset_link = request.host_url + 'ativar_conta/' + token

        msg = Message('Ativação de Conta', recipients=[Email], sender='noreply@app.com')
        
        data = {
            'app_name' : "CPPD",
            'title' : 'Ativação de Conta',
            'body' : f'Para ativar sua conta, clique no botão abaixo',
            'reset_link' : reset_link
        }
        
        msg.html = render_template("email_ativar.html", data=data)
        
        try:
            mail.send(msg)
            flash("Foi enviado um email de confirmação no seu email para a ativação da sua conta")
        except Exception as e:
            return render_template("erro_email.html")
        
        return redirect(url_for('auth.login'))
    else:
        flash('CPF ja cadastrado!')
        return redirect(url_for('auth.registrar'))

@auth.route('/esqueci_senha')
def esqueci_senha():
    return render_template("esqueci_senha.html")

@auth.route('/esqueci_senha', methods=["GET", "POST"])
def esqueci_senha_post():
    cursor = db.cursor()
    
    if request.method == 'POST':
        emailPost = request.form['Email']
    
    cursor.execute("""SELECT Email FROM docente WHERE Email=%s""", (emailPost,))
    email = cursor.fetchone()

    if email is None:
        flash('Email não cadastrado!')
        return redirect(url_for('auth.esqueci_senha'))
    else:
        token = serializer.dumps(*email, salt='reset-password')
        cursor.execute("""UPDATE docente SET token_reset=%s WHERE Email=%s""", (token, *email))
        db.commit()

        reset_link = request.host_url + 'resetar_senha/' + token

        msg = Message('Redefinição de Senha', recipients=[*email], sender='noreply@app.com')
        
        data = {
            'app_name' : "CPPD",
            'title' : 'Redefinição de Senha',
            'body' : f'Para redefinir sua senha, clique no botão abaixo (O Link tem validade de 2 horas)',
            'reset_link' : reset_link
        }
        msg.html = render_template("email.html", data=data)
        
        try:
            mail.send(msg)
        except Exception as e:
            return render_template("erro_email.html")

        return render_template("email_enviado.html")

@auth.route('/resetar_senha/<token>')
def resetar_senha(token):
    cursor = db.cursor()
    
    cursor.execute("""SELECT token_reset FROM docente WHERE token_reset=%s""", (token,))
    TokenDocente = cursor.fetchone()
    
    try:
        if TokenDocente:
            email = serializer.loads(token, salt='reset-password', max_age=7200)
        else:
            return render_template('token_expirado.html')
    except:
        return render_template('token_expirado.html')
    
    return render_template('resetar_senha.html')

@auth.route('/resetar_senha/<token>', methods=["GET", "POST"])
def resetar_senha_post(token):
    cursor = db.cursor()
    
    cursor.execute("""SELECT id FROM docente WHERE token_reset=%s""", (token,))
    idDocente = cursor.fetchone()
    
    print(idDocente)
    
    if request.method == 'POST':
        senha = request.form['Senha']
        
        cursor.execute("""UPDATE docente SET Senha=%s WHERE id=%s""", (generate_password_hash(senha, method='sha256'), *idDocente))
        cursor.execute("""UPDATE docente SET token_reset=NULL WHERE id=%s""", (*idDocente,))
        db.commit()
        
        return render_template('sucesso_senha.html')

    return render_template('resetar_senha.html')

@auth.route('/logout')
def logout():
    logout_user()
    flash("Conta deslogada com sucesso!")
    return redirect(url_for('main.principal'))