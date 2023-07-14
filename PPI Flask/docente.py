from flask import render_template, request, redirect, url_for, Blueprint, flash
from flask_login import login_required, current_user
from . import db
import os

docente = Blueprint('docente', __name__, template_folder='templates\docente')

@docente.route('/home_docente')
@login_required
def home_docente():
    cppd = current_user.cppd

    cursor = db.cursor()
    cursor.execute("""SELECT * FROM docente WHERE CPF=%s""", (current_user.cpf,))
    record = cursor.fetchone()
    
    if record[6] == 1:
        return redirect(url_for('cppd.cppd_home'))

    return render_template('home_docente.html', cppd=cppd)

@docente.route('/minha_conta')
@login_required
def minha_conta():

    nome = current_user.nome
    cpf = current_user.cpf
    siape = current_user.siape
    email = current_user.email
    senha = current_user.senha
    cppd = current_user.cppd
    nivelcap = current_user.nivelcap

    if os.path.exists(f'D:\PPIFlask\static\{current_user.id}.jpg'):
        foto = f'{current_user.id}.jpg'
    else:
        foto = f'foto_padrao.jpg'

    return render_template('minha_conta.html', nome=nome, cpf=cpf, siape=siape, email=email, senha=senha, cppd=cppd, foto=foto, nivelcap=nivelcap)

@docente.route('/minha_conta', methods=["GET", "POST"])
@login_required
def minha_conta_post():
    cursor = db.cursor()
    
    if request.method == 'POST':
        CPF = request.form['CPF']
        SIAPE = request.form['SIAPE']
        Nome = request.form['Nome']
        Email = request.form['Email']
        Foto = request.files['Foto']
        
        if request.files['Foto'].filename == '':
            pass
        else:
            Foto.save(f'D:\\PPIFlask\\static\\{current_user.id}.jpg')
        
        print(f'CPF: {CPF} SIAPE: {SIAPE} Nome:{Nome}')

        cursor.execute("""UPDATE docente SET CPF=%s, Nome=%s, SIAPE=%s, Email=%s WHERE id=%s""", (CPF, Nome, SIAPE, Email, current_user.id))
        db.commit()
        return redirect(url_for('docente.minha_conta'))

@docente.route('/ajuda_docente')
@login_required
def ajuda_docente():

    return render_template('ajuda_docente.html', nome=current_user.nome, cppd=current_user.cppd)


