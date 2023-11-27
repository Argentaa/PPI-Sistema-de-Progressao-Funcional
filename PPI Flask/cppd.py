from flask import render_template, request, redirect, url_for, Blueprint, flash
from flask_login import  login_required, current_user
from flask_mail import Message
from . import db, mail

cppd = Blueprint('cppd', __name__, template_folder='templates\\cppd')

@cppd.route('/cppd')
@login_required

def cppd_home():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))

    return render_template('home_cppd.html')

@cppd.route('/gerenciar_professores')
@login_required

def gerenciar_professores():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()
    
    cursor.execute("""SELECT nome, foto, SIAPE, CPPD, id, CPF FROM docente WHERE id <> %s ORDER BY CPPD DESC""", (current_user.id,))
    docentes = cursor.fetchall()
    
    return render_template('gerenciar_professores.html', docentes=docentes)

@cppd.route('/tornar_cppd/<int:id>')
@login_required

def tornar_cppd(id):
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()
    
    cursor.execute("""UPDATE docente SET CPPD=%s WHERE id=%s""", (1, id))
    db.commit()
    
    return redirect(url_for('cppd.gerenciar_professores'))
    
@cppd.route('/remover_cppd/<int:id>')
@login_required

def remover_cppd(id):
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()
    
    cursor.execute("""UPDATE docente SET CPPD=%s WHERE id=%s""", (0, id))
    db.commit()
    
    return redirect(url_for('cppd.gerenciar_professores'))

@cppd.route('/listar_requerimentos')
@login_required

def listar_requerimentos():
    
    if current_user.cppd == 0:
        return redirect(url_for('main.principal'))
    
    cursor = db.cursor()
    
    cursor.execute("""SELECT * FROM requerimentos""")
    requerimentos = cursor.fetchall()

    return render_template('listar_requerimentos.html', requerimentos=reversed(requerimentos))

@cppd.route('/corrigir_requerimentos/<int:id>')
@login_required

def corrigir_requerimentos_id(id):
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()
    cursor.execute("""SELECT docente_id FROM requerimentos WHERE id=%s""", (id,))
    Docente_id = cursor.fetchone() 
    
    cursor.execute("""SELECT CPF, nome, SIAPE, email, nivelCapacitacao, foto, escolaridade, aperfeicoamento, especializacao, mestrado, doutorado, lotacao, diretoria, coordenacao, cargo, chefiaImediata FROM docente WHERE id = %s""", (*Docente_id,))
    docente = cursor.fetchone()
    
    criteriosdict = {}
    arquivosdict = {}

    cursor = db.cursor()
    cursor.execute("""SELECT descricao FROM partes WHERE status='ativo'""")
    dados_p = cursor.fetchall()
    partes = [item for t in dados_p for item in t]

    for parte in partes:
        cursor.execute("""SELECT id FROM partes WHERE descricao=%s AND status='ativo'""", (parte,))
        idPartelist = cursor.fetchall()
        idParte, *x = idPartelist

        cursor.execute("""SELECT descricao FROM categorias WHERE parte_id=%s AND status='ativo'""", (*idParte,))
        categoriastuple = cursor.fetchall()
        categoriaslist = [item for t in categoriastuple for item in t]

        for categoria in categoriaslist:
            cursor.execute("""SELECT id FROM categorias WHERE descricao=%s AND status='ativo'""", (categoria,))
            idCategorialist = cursor.fetchall()
            idCategoria, *x = idCategorialist

            cursor.execute("""SELECT descricao, pontos_string, pontos, tipo_pontos, id FROM criterios WHERE categoria_id=%s AND status='ativo'""", (*idCategoria,))
            criterios = cursor.fetchall()

            cursor.execute("""SELECT id, criterio_id, pontos_obtidos FROM avaliacoes WHERE requerimento_id=%s""", (id,))
            avaliacoes = cursor.fetchall()

            ids_avaliacao = []
            for avaliacao in avaliacoes:
                ids_avaliacao.append(avaliacao[1])

            if parte not in criteriosdict:
                criteriosdict[parte] = {}
            criteriosdict[parte][categoria] = criterios

    cursor.execute("""SELECT criterio_id, nome_arquivo FROM avaliacoes WHERE requerimento_id=%s""", (id,))
    arquivos = cursor.fetchall()
    
    for arquivo in arquivos:
        if arquivo[1] != None and arquivo[1] != '':
            arquivosdict[arquivo[0]] = arquivo[1]
    
    cursor.execute("""SELECT doc_requerimento, doc_comprobatorio FROM requerimentos WHERE id=%s""", (id,))
    arquivos_comprob = cursor.fetchall()
    print(arquivos_comprob)
    
    return render_template('corrigir_requerimento_id.html', arquivos_comprob=arquivos_comprob, criteriosdict=criteriosdict, cppd=current_user.cppd, avaliacoes=avaliacoes, ids_avaliacao=ids_avaliacao, arquivosdict=arquivosdict, docente=docente, id=id)

@cppd.route('/corrigir_requerimentos/<int:id>', methods=["GET", "POST"])
@login_required

def corrigir_requerimentos_post(id):
    
    cursor = db.cursor()
    
    cursor.execute("""SELECT docente_id FROM requerimentos WHERE id=%s""", (id,))
    docente_id = cursor.fetchone()
    
    cursor.execute("""SELECT email FROM docente WHERE id=%s""", (*docente_id,))
    Email = cursor.fetchone()
    '''
    msg = Message('Ativação de Conta', recipients=[*Email], sender='noreply@app.com')
        
    data = {
        'app_name' : "Sistema de Progressão Funcional",
        'title' : 'Requerimento Corrigido',
        'body' : request.form['Mensagem'],
    }
    
    msg.html = render_template("email_ativar.html", data=data)
    
    try:
        mail.send(msg)
        flash("Foi enviado um email para o professor notificando a correação do requerimento")
    except Exception as e:
        return render_template("erro_email.html")'''

    acao = request.form.get('acao')
    
    if acao == 'Aprovar':
        cursor.execute("""UPDATE requerimentos SET status=%s WHERE id=%s""", ('Aprovado', id))
        db.commit()
    elif acao == 'Reprovar':
        cursor.execute("""UPDATE requerimentos SET status=%s WHERE id=%s""", ('Reprovado', id))
        db.commit()
        
    return redirect(url_for('cppd.listar_requerimentos'))

@cppd.route('/alterar_requerimentos')
@login_required

def alterar_requerimentos():
    
    if current_user.cppd == 0:
        return redirect(url_for('main.principal'))
    
    criteriosdict = {}

    cursor = db.cursor()
    cursor.execute("""SELECT descricao FROM partes WHERE status='ativo'""")
    dados_p = cursor.fetchall()
    partes = [item for t in dados_p for item in t]

    cursor.execute("""SELECT descricao FROM categorias WHERE status='ativo'""")
    dados_p = cursor.fetchall()
    categoriasalt = [item for t in dados_p for item in t]

    for parte in partes:
        cursor.execute("""SELECT id FROM partes WHERE descricao=%s AND status='ativo'""", (parte,))
        idPartelist = cursor.fetchall()
        idParte, *x = idPartelist

        cursor.execute("""SELECT descricao FROM categorias WHERE parte_id=%s AND status='ativo'""", (*idParte,))
        categoriastuple = cursor.fetchall()
        categoriaslist = [item for t in categoriastuple for item in t]

        for categoria in categoriaslist:
            cursor.execute("""SELECT id FROM categorias WHERE descricao=%s AND status='ativo'""", (categoria,))
            idCategorialist = cursor.fetchall()
            idCategoria, *x = idCategorialist

            cursor.execute("""SELECT descricao, pontos_string, pontos, tipo_pontos FROM criterios WHERE categoria_id=%s AND status='ativo'""", (*idCategoria,))
            criterios = cursor.fetchall()

            if parte not in criteriosdict:
                criteriosdict[parte] = {}
            criteriosdict[parte][categoria] = criterios

    return render_template('alterar_requerimentos.html', partesalt=partes, categoriasalt=categoriasalt, criteriosdict=criteriosdict)


@cppd.route('/adicionar_parte', methods=["GET", "POST"])
@login_required

def adicionar_parte():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    if request.method=='POST':
        parte = request.form['Parte']

        cursor = db.cursor()
        cursor.execute("""INSERT INTO partes (descricao) VALUES (%s)""", (parte,))
        db.commit()

        flash(f"Nova {parte} adicionada!")
        
        return redirect(url_for('cppd.alterar_requerimentos'))

@cppd.route('/adicionar_categoria', methods=["GET", "POST"])
@login_required

def adicionar_categoria():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    if request.method=='POST':
        categoria = request.form['Categoria']
        parte = request.form['Parte']

        cursor = db.cursor()
        cursor.execute("""SELECT id FROM partes WHERE descricao=%s""", (parte,))
        parteid = cursor.fetchone()

        cursor.execute("""INSERT INTO categorias (parte_id, descricao) VALUES (%s, %s)""", (parteid[0], categoria))
        db.commit()
        
        flash(f"Nova Categoria {categoria} adicionada!")

        return redirect(url_for('cppd.alterar_requerimentos'))
    
@cppd.route('/adicionar_criterio', methods=["GET", "POST"])
@login_required

def adicionar_criterio():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    if request.method=='POST':
        pontos = request.form['Pontos']
        criterio = request.form['Criterio']
        categoria = request.form['Categoria']
        pontosMult = request.form['PontosMult']
        tipo_pontos = request.form.get('pontos')

        cursor = db.cursor()
        cursor.execute("""SELECT id FROM categorias WHERE descricao=%s""", (categoria,))
        catid = cursor.fetchone()
        
        print(criterio, int(pontosMult), pontos, tipo_pontos, catid[0])
        
        try:
            cursor.execute("""INSERT INTO criterios (categoria_id, descricao, pontos, pontos_string, tipo_pontos) 
                            VALUES (%s, %s, %s, %s, %s)""", (catid[0], criterio, int(pontosMult), pontos, tipo_pontos))
            db.commit()
            
        except:
            flash('Somente é permetido números nos pontos de multiplicação!')
            return redirect(url_for('cppd.alterar_requerimentos'))

        flash(f"Novo Critério {criterio} adicionado!")

        return redirect(url_for('cppd.alterar_requerimentos'))
    
@cppd.route('/alterar_parte', methods=['GET','POST'])
@login_required

def alterar_parte():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    if request.method=='POST':
        cursor = db.cursor()
        parte_mudar = request.form['Parte']
        parte = request.form['id']

        cursor.execute("""UPDATE partes SET descricao=%s WHERE descricao=%s""", (parte_mudar, parte))
        db.commit()
        
        flash(f"{parte} alterada!")

        return redirect(url_for('cppd.alterar_requerimentos'))

@cppd.route('/alterar_categoria', methods=['GET','POST'])
@login_required

def alterar_categoria():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    if request.method=='POST':
        cursor = db.cursor()
        categoria_mudar = request.form['Categoria']
        categoria = request.form['id']

        cursor.execute("""UPDATE categorias SET descricao=%s WHERE descricao=%s""", (categoria_mudar, categoria))
        db.commit()
        
        flash(f"Categoria {categoria} alterada!")

        return redirect(url_for('cppd.alterar_requerimentos'))
    
@cppd.route('/alterar_criterio', methods=['GET','POST'])
@login_required

def alterar_criterio():
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    if request.method=='POST':
        cursor = db.cursor()
        criterio = request.form['id']
        pontos = request.form['Pontos']
        criterio_mudar = request.form['Criterio']
        pontosMult = request.form['PontosMult']
        tipo_pontos = request.form.get('pontos')
        
        cursor.execute("""UPDATE criterios SET descricao=%s, pontos=%s, pontos_string=%s, tipo_pontos=%s WHERE descricao=%s""", (criterio_mudar,int(pontosMult),pontos,tipo_pontos,criterio))
        db.commit()
        
        flash(f"Critério {criterio} alterado!")

        return redirect(url_for('cppd.alterar_requerimentos'))

@cppd.route('/desativar_parte/<string:Parte>')
@login_required

def desativar_parte(Parte):
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()

    cursor.execute("""UPDATE partes SET status='inativo' WHERE descricao=%s""", (Parte,))
    
    cursor.execute("""SELECT id FROM partes WHERE descricao=%s""",(Parte,))
    idparte = cursor.fetchone()

    cursor.execute("""SELECT id FROM categorias WHERE parte_id=%s""", (*idparte,))
    idcat = cursor.fetchall()

    for cat in idcat:
        cursor.execute("""UPDATE categorias SET status='inativo' WHERE id=%s""", (cat,))
        cursor.execute("""UPDATE criterios SET status='inativo' WHERE categoria_id=%s""", (cat,))
    
    db.commit()
    
    flash(f"{Parte} desativada!")

    return redirect(url_for('cppd.alterar_requerimentos'))


@cppd.route('/desativar_categoria/<string:Categoria>')
@login_required

def desativar_categoria(Categoria):
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()

    cursor.execute("""UPDATE categorias SET status='inativo' WHERE descricao=%s""", (Categoria,))
    
    cursor.execute("""SELECT id FROM categorias WHERE descricao=%s""", (Categoria,))
    idcat = cursor.fetchone()

    cursor.execute("""UPDATE criterios SET status='inativo' WHERE categoria_id=%s""", (*idcat,))
    
    db.commit()
    
    flash(f"Categoria {Categoria} desativada!")

    return redirect(url_for('cppd.alterar_requerimentos'))


@cppd.route('/desativar_criterio/<string:Criterio>')
@login_required

def desativar_criterio(Criterio):
    
    if current_user.cppd == 0:
        return redirect(url_for('docente.home_docente'))
    
    cursor = db.cursor()
    
    cursor.execute("""UPDATE criterios SET status='inativo' WHERE descricao=%s""", (Criterio,))
    
    flash(f"Criterio {Criterio} desativado!")

    db.commit()

    return redirect(url_for('cppd.alterar_requerimentos'))



