from flask import render_template, request, redirect, url_for, Blueprint, flash
from flask_login import login_required, current_user
import os, pdfkit
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename
from . import db
import uuid

requerimentos = Blueprint('requerimentos', __name__, template_folder='templates\\requerimentos')

def generate_unique_filename(original_filename):
    
    unique_id = uuid.uuid4().hex
    unique_filename = f"{unique_id}_{original_filename}"

    while os.path.exists(unique_filename):
        unique_id = uuid.uuid4().hex
        unique_filename = f"{unique_id}_{original_filename}"

    return unique_filename


@requerimentos.route('/meus_requerimentos')
@login_required
def meus_requerimentos():
    cursor = db.cursor()
    
    cursor.execute("""SELECT id, status FROM requerimentos WHERE docente_id=%s ORDER BY id DESC""", (current_user.id,))

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
        arquivo_req = request.files['Arquivos_req']
        arquivo_comp = request.files['Arquivos_comp']
        
        filename_req = secure_filename(arquivo_req.filename)
        new_filename_req = generate_unique_filename(filename_req)
        
        filename_comp = secure_filename(arquivo_comp.filename)
        new_filename_comp = generate_unique_filename(filename_comp)

        arquivo_req.save(f"PPIFlask/static/{new_filename_req}")
        arquivo_comp.save(f"PPIFlask/static/{new_filename_comp}")
        
        cursor.execute("""UPDATE docente SET nome = %s, SIAPE = %s, nivelCapacitacao = %s, escolaridade = %s, aperfeicoamento = %s, especializacao = %s, mestrado = %s, doutorado = %s, lotacao = %s, diretoria = %s, coordenacao = %s, cargo = %s, chefiaImediata = %s WHERE id = %s""", (nome, siape, nivel_capacitacao, escolaridade, aperfeicoamento, especializacao, mestrado, doutorado, lotacao, diretoria, coordenacao, cargo, chefia, current_user.id))
        cursor.execute("""INSERT INTO requerimentos (docente_id, titulo, doc_requerimento, doc_comprobatorio) VALUES (%s, %s, %s, %s)""", (current_user.id, f"Progressão do Professor(a) {nome}", new_filename_req, new_filename_comp))
        db.commit()
        
        flash("Novo requerimento criado!")
        
        return redirect(url_for('requerimentos.meus_requerimentos'))

@requerimentos.route('/excluir_requerimento/<int:id>')
@login_required

def excluir_requerimento(id):
    cursor = db.cursor()

    cursor.execute("""SELECT id FROM avaliacoes WHERE requerimento_id=%s""",(id,))
    avaliacoes = cursor.fetchall()
    
    for avaliacao in avaliacoes:
        cursor.execute("""DELETE FROM avaliacoes WHERE id=%s""", (*avaliacao,))

    cursor.execute("""DELETE FROM requerimentos WHERE id=%s""",(id,))
    db.commit()

    return redirect(url_for('requerimentos.meus_requerimentos'))


@requerimentos.route('/requerimento/<int:id>')
@login_required

def requerimento(id):
    criteriosdict = {}

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
            
            if parte not in criteriosdict:
                criteriosdict[parte] = {}
            criteriosdict[parte][categoria] = criterios
    
    cursor.execute("""SELECT criterio_id, pontos_obtidos, nome_arquivo FROM avaliacoes WHERE requerimento_id=%s""", (id,))
    avaliacoes = cursor.fetchall()

    avaliacoes_dict = {}
    
    for avaliacao in avaliacoes:
        if avaliacao[2] == None:
            avaliacoes_dict[avaliacao[0]] = (avaliacao[1], '')
        else:
            avaliacoes_dict[avaliacao[0]] = (avaliacao[1], avaliacao[2])
    
    return render_template('requerimento.html', criteriosdict=criteriosdict, cppd=current_user.cppd, avaliacoes_dict=avaliacoes_dict, id=id)


@requerimentos.route('/requerimento/<int:id>', methods=["GET", "POST"])
@login_required

def requerimento_post(id):
    
    cursor = db.cursor()
    
    acao = request.form.get('acao')
    
    if acao == 'Salvar':
        pass
    elif acao == 'Enviar':
        cursor.execute("""UPDATE requerimentos SET status=%s WHERE id=%s""", ('Pendente', id))
        db.commit()
    
    if request.method == 'POST':
        
        criterio_values = {}
        
        for criterio in request.form:
            if 'criterio' in criterio:
                posicao = criterio.find('criterio')
                criterio_name = criterio[:posicao]
                
                if request.form[criterio] != '':
                    criterio_values[criterio_name] = request.form[criterio]
                    
        uploaded_files = {}
        
        for criterio in request.files:
            if 'arquivo' in criterio:
                posicao = criterio.find('arquivo')
                criterio_name = criterio[:posicao]
                
                uploaded_file = request.files[criterio]
                if uploaded_file.filename:
                    filename = secure_filename(uploaded_file.filename)
                    new_filename = generate_unique_filename(filename)

                    file_path = os.path.join('PPIFlask/static/', new_filename)

                    if filename.endswith('.pdf'):
                        pdf_reader = PdfReader(uploaded_file)
                        pdf_writer = PdfWriter()

                        for page_num in range(len(pdf_reader.pages)):
                            pdf_writer.add_page(pdf_reader.pages[page_num])
                            
                        with open(file_path, 'wb') as f:
                            pdf_writer.write(f)
                    else:
                        uploaded_file.save(file_path)

                    uploaded_files[criterio_name] = new_filename 
        
        for key, value in criterio_values.items():
            
            cursor.execute("""SELECT id FROM avaliacoes WHERE criterio_id=%s AND requerimento_id=%s""", (key, id))
            idAvaliacao = cursor.fetchone()
            
            if idAvaliacao:
                if key in uploaded_files:
                    cursor.execute("""UPDATE avaliacoes SET pontos_obtidos=%s, nome_arquivo=%s WHERE requerimento_id=%s AND criterio_id=%s""", (value, uploaded_files[key], id, key))
                else:
                    cursor.execute("""UPDATE avaliacoes SET pontos_obtidos=%s WHERE requerimento_id=%s AND criterio_id=%s""", (value, id, key))
            else:
                if value != 0:
                    if key in uploaded_files:
                        cursor.execute("""INSERT INTO avaliacoes (requerimento_id, criterio_id, pontos_obtidos, nome_arquivo) VALUES (%s, %s, %s, %s)""", (id, key, value, uploaded_files[key]))
                    else:
                        cursor.execute("""INSERT INTO avaliacoes (requerimento_id, criterio_id, pontos_obtidos) VALUES (%s, %s, %s)""", (id, key, value))
        
            db.commit()
                    
    return redirect(url_for('requerimentos.meus_requerimentos'))

@requerimentos.route('/visualizar_requerimento/<int:id>')
@login_required

def visualizar_requerimento(id):
    
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
    
    return render_template('visualizar_requerimento.html', criteriosdict=criteriosdict, cppd=current_user.cppd, avaliacoes=avaliacoes, ids_avaliacao=ids_avaliacao, arquivosdict=arquivosdict, docente=docente, id=id)


@requerimentos.route('/excluir_arquivo/<id>/<nome_arquivo>')
def excluir_arquivo(nome_arquivo, id):
    cursor = db.cursor()
    
    file_path = url_for('static', filename=nome_arquivo)

    cursor.execute("""UPDATE avaliacoes SET nome_arquivo = '' WHERE nome_arquivo=%s""", (nome_arquivo,))
    db.commit()

    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print("The file does not exist:", file_path)

    return redirect(url_for('requerimentos.requerimento', id=id))





