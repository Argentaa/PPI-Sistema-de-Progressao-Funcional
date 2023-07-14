from flask import render_template, request, redirect, url_for, Blueprint, flash, session
from flask_login import login_required, current_user
from . import db

requerimentos = Blueprint('requerimentos', __name__, template_folder='templates\\requerimentos')

@requerimentos.route('/meus_requerimentos')
@login_required
def meus_requerimentos():
    cursor = db.cursor()
    
    cursor.execute("""SELECT id, status FROM requerimentos WHERE docente_id=%s""", (current_user.id,))
    requerimentos = cursor.fetchall()
    
    cursor.execute("""SELECT nome, SIAPE, nivelCapacitacao, escolaridade, aperfeicoamento, especializacao, mestrado, doutorado, lotacao, diretoria, coordenacao, cargo, chefiaImediata FROM docente WHERE id = %s""", (current_user.id,))
    professor = cursor.fetchone()

    niveisCap = ['D I - 1', 'D I - 2', 'D II - 1', 'D II - 2', 
                 'D III - 1', 'D III - 2', 'D III - 3', 'D III - 4', 
                 'D IV - 1', 'D IV - 2', 'D IV - 3', 'D IV - 4', 'TITULAR']
    
    return render_template('meus_requerimentos.html', professor=professor, requerimentos=requerimentos, niveisCap=niveisCap, cppd=current_user.cppd)


@requerimentos.route('/meus_requerimentos', methods=["GET", "POST"])
@login_required
def meus_requerimentos_post():
    cursor = db.cursor()
    
    if request.method == 'POST':
        nome = request.form['Nome']
        siape = request.form['SIAPE']
        nivel_capacitacao = request.form['NivelCapacitacao']
        escolaridade = request.form['Escolaridade']
        aperfeicoamento = request.form['Aperfeiçoamento']
        especializacao = request.form['Especialização']
        mestrado = request.form['Mestrado']
        doutorado = request.form['Doutorado']
        lotacao = request.form['Lotacao']
        diretoria = request.form['Diretoria']
        coordenacao = request.form['Coordenacao']
        cargo = request.form['Cargo']
        chefia = request.form['Chefia']

        cursor.execute("""UPDATE docente SET nome = %s, SIAPE = %s, nivelCapacitacao = %s, escolaridade = %s, aperfeicoamento = %s, especializacao = %s, mestrado = %s, doutorado = %s, lotacao = %s, diretoria = %s, coordenacao = %s, cargo = %s, chefiaImediata = %s WHERE id = %s""", (nome, siape, nivel_capacitacao, escolaridade, aperfeicoamento, especializacao, mestrado, doutorado, lotacao, diretoria, coordenacao, cargo, chefia, current_user.id))
        cursor.execute("""INSERT INTO requerimentos (docente_id, titulo) VALUES (%s, %s)""", (current_user.id, f"Progressão do Professor(a) {nome}"))
        db.commit()
        
        id_requerimento = cursor.lastrowid
        session['novo_requerimento'] = id_requerimento
        
        return redirect(url_for('requerimentos.novo_requerimento'))

@requerimentos.route('/excluir_requerimento/<int:id>')
@login_required

def excluir_requerimento(id):
    cursor = db.cursor()

    cursor.execute("""DELETE FROM requerimentos WHERE id=%s""",(id,))
    db.commit()

    return redirect(url_for('requerimentos.meus_requerimentos'))

@requerimentos.route('/novo_requerimento')
@login_required

def novo_requerimento():
    
    criteriosdict = {}

    cursor = db.cursor()
    cursor.execute("""SELECT descricao FROM partes""")
    dados_p = cursor.fetchall()
    partes = [item for t in dados_p for item in t]

    for parte in partes:
        cursor.execute("""SELECT id FROM partes WHERE descricao=%s""", (parte,))
        idPartelist = cursor.fetchall()
        idParte, *x = idPartelist

        cursor.execute("""SELECT descricao FROM categorias WHERE parte_id=%s""", (*idParte,))

        categoriastuple = cursor.fetchall()
        categoriaslist = [item for t in categoriastuple for item in t]

        for categoria in categoriaslist:
            cursor.execute("""SELECT id FROM categorias WHERE descricao=%s""", (categoria,))
            idCategorialist = cursor.fetchall()
            idCategoria, *x = idCategorialist

            cursor.execute("""SELECT descricao, pontos_string, pontos FROM criterios WHERE categoria_id=%s""", (*idCategoria,))
            criterios = cursor.fetchall()
           
            if parte not in criteriosdict:
                criteriosdict[parte] = {}
            criteriosdict[parte][categoria] = criterios

    return render_template('novo_requerimento.html', criteriosdict=criteriosdict, cppd = current_user.cppd)

@requerimentos.route('/novo_requerimento', methods=["GET", "POST"])
@login_required

def novo_requerimento_post():
    
    requerimento_id = session.get('novo_requerimento')
    
    if request.method == 'POST':

        for campo in request.files:
            arquivo = request.files[campo]
            if arquivo.filename != '':
                print(arquivo)

        for key, val in request.form.items():
            if key.startswith("criterio"):
                if val != '':
                    print(key, val)
    
    return redirect(url_for('requerimentos.meus_requerimentos'))

def salvar_novo_requerimento():
    
    requerimento_id = session.get('novo_requerimento')
    
    return redirect(url_for('requerimentos.meus_requerimentos'))

@requerimentos.route('/requerimento/<int:id>')
@login_required

def requerimento(id):
    criteriosdict = {}

    cursor = db.cursor()
    cursor.execute("""SELECT descricao FROM partes""")
    dados_p = cursor.fetchall()
    partes = [item for t in dados_p for item in t]

    for parte in partes:
        cursor.execute("""SELECT id FROM partes WHERE descricao=%s""", (parte,))
        idPartelist = cursor.fetchall()
        idParte, *x = idPartelist

        cursor.execute("""SELECT descricao FROM categorias WHERE parte_id=%s""", (*idParte,))

        categoriastuple = cursor.fetchall()
        categoriaslist = [item for t in categoriastuple for item in t]

        for categoria in categoriaslist:
            cursor.execute("""SELECT id FROM categorias WHERE descricao=%s""", (categoria,))
            idCategorialist = cursor.fetchall()
            idCategoria, *x = idCategorialist

            cursor.execute("""SELECT descricao, pontos_string, pontos FROM criterios WHERE categoria_id=%s""", (*idCategoria,))
            criterios = cursor.fetchall()
           
            if parte not in criteriosdict:
                criteriosdict[parte] = {}
            criteriosdict[parte][categoria] = criterios

    return render_template('requerimento.html', criteriosdict=criteriosdict, cppd = current_user.cppd, id=id)

@requerimentos.route('/requerimento', methods=["GET", "POST"])
@login_required

def requerimento_post():
    if request.method == 'POST':
        for key, val in request.form.items():
            if key.startswith("criterio"):
                print(key, val)
    
    return redirect(url_for('requerimentos.meus_requerimentos'))

def salvar_requerimento():
    
    for campo in request.files:
        arquivo = request.files[campo]
        if arquivo.filename != '':
            print(arquivo)

    for key, val in request.form.items():
        if key.startswith("criterio"):
            if val != '':
                print(key, val)
    
    return redirect(url_for('requerimentos.meus_requerimentos'))

