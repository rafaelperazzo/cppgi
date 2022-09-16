# -*- coding: utf-8 -*-
from fileinput import filename
import re
from urllib.parse import urlencode
from flask import Flask
from flask import render_template
from flask import request,url_for,send_from_directory,redirect,flash,Markup,session
from flask_httpauth import HTTPBasicAuth
import datetime
import MySQLdb
import os
from ezodf import newdoc
import zipfile
import tempfile
import string
import random
import logging
import sys
import numpy as np
import pdfkit
from flask_mail import Mail
from flask_mail import Message
from flask_uploads import *
from PIL import Image, ImageDraw, ImageFont
import threading
import iniconfig
import base64
import pyqrcode
from flask_restful import Api
from flask_cors import CORS


WORKING_DIR='/home/perazzo/cppgi/'
config = iniconfig.IniConfig(WORKING_DIR + 'config.ini')
SERVER_URL = config['DEFAULT']['server']
PRODUCAO = 1
try:
    PRODUCAO = config['DEFAULT']['producao']
    PRODUCAO = int(PRODUCAO)
except:
    PRODUCAO = 1

from waitress import serve
UPLOAD_FOLDER = WORKING_DIR + 'uploads/'
ALLOWED_EXTENSIONS = set(['pdf','xml'])
PLOTS_DIR = WORKING_DIR + 'static/plots/'
CURRICULOS_DIR=WORKING_DIR + 'static/files/'
SITE = SERVER_URL + "/cppgi/uploads/"
IMAGENS_URL = SERVER_URL + "/cppgi/static/"
DECLARACOES_DIR = WORKING_DIR + 'pdfs/'
ROOT_SITE = SERVER_URL
CPPGI_SITE = ROOT_SITE + '/cppgi/'
USUARIO_SITE = ROOT_SITE + "/cppgi/usuario"
ATTACHMENTS_DIR = WORKING_DIR + 'uploads/'
CERTIFICADOS_TEMP_DIR = WORKING_DIR + 'temp/'
CERTIFICADOS_TEMPLATE_DIR = WORKING_DIR + 'documentos/'
FONT_PATH = "/fonts/Times_New_Roman_Bold.ttf"
LINK_AVALIACAO = ROOT_SITE + "/cppgi/avaliacao"

app = Flask(__name__)

api = Api(app)
CORS(app)

auth = HTTPBasicAuth()
mail = Mail(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'pesquisa.prpi@ufca.edu.br'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'pesquisa.prpi@ufca.edu.br'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CURRICULOS_FOLDER'] = CURRICULOS_DIR
app.config['DECLARACOES_FOLDER'] = DECLARACOES_DIR
app.config['TEMP_FOLDER'] = DECLARACOES_DIR
app.config['DOCUMENTS_FOLDER'] = WORKING_DIR + 'documentos/'
app.config['CERTIFICADOS_FOLDER'] = WORKING_DIR + 'certificados/'

logging.basicConfig(filename=WORKING_DIR + 'app.log', filemode='w', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',level=logging.ERROR)

#Obtendo senhas
lines = [line.rstrip('\n') for line in open(WORKING_DIR + 'senhas.pass')]
PASSWORD = lines[0]
GMAIL_PASSWORD = lines[1]
SESSION_SECRET_KEY = lines[2]
app.config['SECRET_KEY'] = SESSION_SECRET_KEY
app.config['MAIL_PASSWORD'] = GMAIL_PASSWORD
mail = Mail(app)

#Flask-flask_uploads
app.config['UPLOADED_DOCUMENTS_DEST'] = ATTACHMENTS_DIR
app.config['UPLOADS_DEFAULT_DEST'] = ATTACHMENTS_DIR
anexos = UploadSet('documents',ALL)

certificados = UploadSet('certificados', ALL, default_dest=lambda x: CERTIFICADOS_TEMPLATE_DIR)
configure_uploads(app, (anexos,certificados))
#patch_request_class(app)

class TextWrapper(object):
    """ Helper class to wrap text in lines, based on given text, font
        and max allowed line width.
    """

    def __init__(self, text, font, max_width):
        self.text = text
        self.text_lines = [
            ' '.join([w.strip() for w in l.split(' ') if w])
            for l in text.split('\n')
            if l
        ]
        self.font = font
        self.max_width = max_width

        self.draw = ImageDraw.Draw(
            Image.new(
                mode='RGB',
                size=(100, 100)
            )
        )

        self.space_width = self.draw.textsize(
            text=' ',
            font=self.font
        )[0]

    def get_text_width(self, text):
        return self.draw.textsize(
            text=text,
            font=self.font
        )[0]

    def wrapped_text(self):
        wrapped_lines = []
        buf = []
        buf_width = 0

        for line in self.text_lines:
            for word in line.split(' '):
                word_width = self.get_text_width(word)

                expected_width = word_width if not buf else \
                    buf_width + self.space_width + word_width

                if expected_width <= self.max_width:
                    # word fits in line
                    buf_width = expected_width
                    buf.append(word)
                else:
                    # word doesn't fit in line
                    wrapped_lines.append(' '.join(buf))
                    buf = [word]
                    buf_width = word_width

            if buf:
                wrapped_lines.append(' '.join(buf))
                buf = []
                buf_width = 0

        return '\n'.join(wrapped_lines)

def removerAspas(texto):
    resultado = texto.replace('"',' ')
    resultado = resultado.replace("'"," ")
    return(resultado)

def enviar_email(msg):
    with app.app_context():
        if PRODUCAO==1:
            mail.send(msg)

def atualizar(consulta):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.autocommit(True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    try:
        cursor.execute(consulta)
        conn.commit()
    except MySQLdb.Error as e:
        
        logging.error(e)
        logging.error(consulta)
        
    finally:
        cursor.close()
        conn.close()

def inserir(consulta,valores):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.autocommit(True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    try:
        cursor.execute(consulta,valores)
        conn.commit()
    except MySQLdb.Error as e:
        logging.error(e)
        logging.error(consulta)
    finally:
        cursor.close()
        conn.close()


def id_generator(size=20, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        return ''.join(random.choice(chars) for _ in range(size))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getData():
    Meses=('janeiro','fevereiro',u'março','abril','maio','junho',
       'julho','agosto','setembro','outubro','novembro','dezembro')
    agora = datetime.date.today()
    dia = agora.day
    mes=(agora.month-1)
    mesExtenso = Meses[mes]
    ano = agora.year
    resultado = str(dia) + " de " + mesExtenso + " de " + str(ano) + "."
    return resultado

def getEditaisAbertos():
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = """SELECT id,nome,DATE_FORMAT(deadline,'%d/%m/%Y - %H:%i') FROM editais WHERE now()<deadline ORDER BY id DESC"""
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return(linhas)

'''
INÍCIO AUTENTICAÇÃO
**************************************************************
'''
@auth.verify_password
def verify_password(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    try:
        conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
        conn.select_db('cppgi')
        cursor  = conn.cursor()
        consulta = """SELECT id,username,permission,roles,nome FROM users WHERE username='""" + username + """' AND password=('""" + password + """')"""
        cursor.execute(consulta)
        total = cursor.rowcount
        if (total==0):
            return (False)
        else:
            linha = cursor.fetchone()
            session['username'] = str(linha[1])
            session['permissao'] = int(linha[2])
            roles = str(linha[3])
            roles = roles.split(',')
            session['roles'] = roles
            session['nome'] = str(linha[4])
            #return (True)
            return username
    except:
        e = sys.exc_info()[0]
        logging.error(e)
        logging.error("ERRO Na função check_auth. Ver consulta abaixo.")
        logging.error(consulta)
    finally:
        cursor.close()
        conn.close()

def autenticado():
    if ('username') in session:
        return (True)
    else:
        return (False)

def logout():
    session.clear()

'''
Retorna uma coluna de uma linha única dado uma chave primária
'''
def obterColunaUnica(tabela,coluna,colunaId,valorId):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT " + coluna + " FROM " + tabela + " WHERE " + colunaId + "=" + valorId
    resultado = "0"
    try:
        cursor.execute(consulta)
        linhas = cursor.fetchall()
        for linha in linhas:
            resultado = str(linha[0])
        return(resultado)
    except:
        e = sys.exc_info()[0]
        logging.error(e)
        logging.error("ERRO Na função obtercolunaUnica. Ver consulta abaixo.")
        logging.error(consulta)
    finally:
        cursor.close()
        conn.close()
        

@auth.get_user_roles
def get_user_roles(user):
    consulta = """SELECT roles FROM users WHERE username='""" + auth.username() + """'"""
    linhas,total = executarSelect(consulta)
    if total>0:
        for linha in linhas:
            roles = str(linha[0])
            roles = roles.split(',')
            session['roles'] = roles
            return (roles)
    else:
        return (['user'])

def avaliadorTemPermissao(edital, data,sala):
    consulta = """SELECT id FROM usuarios_salas WHERE username='""" + auth.username() + """' and data='""" + data + """' and sala='""" + sala + """'"""
    linhas,total = executarSelect(consulta)
    if total>0:
        return (True)
    else:
        return (False)

'''
FIM AUTENTICAÇÃO
**************************************************************
'''

@app.before_first_request
def iniciar_sessao():
    session['PRODUCAO'] = PRODUCAO

@app.route("/")
def home():
    editaisAbertos = getEditaisAbertos()
    return (render_template('menu.html',editais=editaisAbertos))

@app.route("/submissao")
def submissao():
    editaisAbertos = getEditaisAbertos()
    return (render_template('cadastrarProjeto.html',abertos=editaisAbertos,PRODUCAO=PRODUCAO))

@app.route("/declaracao", methods=['GET', 'POST'])
def declaracao():
    if request.method == "GET":
        if 'idProjeto' in request.args:
            texto_declaracao = gerarDeclaracao(str(request.args['idProjeto']))
            data_agora = getData()
            try:
                options = {
                    'page-size': 'A4',
                    'margin-top': '20mm',
                    'margin-right': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '20mm',
}
                arquivoDeclaracao = app.config['DECLARACOES_FOLDER'] + 'declaracao.pdf'
                #pdfkit.from_string(render_template('a4.html',texto=texto_declaracao,data=data_agora,identificador=texto_declaracao[7],raiz=ROOT_SITE),arquivoDeclaracao)
                #return send_from_directory(app.config['DECLARACOES_FOLDER'], 'declaracao.pdf')
                #return send_file(arquivoDeclaracao, attachment_filename='arquivo.pdf')
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                logging.error(arquivoDeclaracao)
                logging.error("Nao foi possivel gerar o PDF da declaração.")
            finally:
                return render_template('a4.html',texto=texto_declaracao,data=data_agora,identificador=texto_declaracao[7],raiz=ROOT_SITE)
        else:
            logging.debug("Tentativa de gerar declaração, sem o id do projeto!")
            return("OK")

@app.route("/orientadorDeclaracao", methods=['GET', 'POST'])
def declaracaoOrientador():
    resultados = gerarDeclaracaoOrientador(str(request.args['idProjeto']))
    texto_declaracao = resultados[0]
    bolsistas = resultados[1]
    data_agora = getData()
    return render_template('orientador.html',texto=texto_declaracao,data=data_agora,identificador=texto_declaracao[0],bolsistas=bolsistas)



@app.route("/cadastrarProjeto", methods=['GET', 'POST'])
def cadastrarProjeto():

    #CADASTRAR DADOS DO PROPONENTE
    destino = int(request.form['destino'])
    tipo = int(request.form['tipo_apresentacao'])
    tipo_trabalho = int(request.form['tipo_trabalho'])
    nome = str(request.form['autores'])
    nome = nome.upper()
    identificacao = str(request.form['identificacao'])
    identificacao = identificacao.replace('.','')
    identificacao = identificacao.replace('-','')
    email = str(request.form['email'])
    grande_area = str(request.form['grande_area'])
    titulo = str(request.form['titulo'])
    titulo = removerAspas(titulo)
    titulo = titulo.upper()
    palavras = str(request.form['palavras'])
    palavras = removerAspas(palavras)
    resumo = str(request.form['resumo'])
    resumo = removerAspas(resumo)

    nomeDoArquivoTrabalho = ""
    if 'arquivo_trabalho' in request.files:
        token = id_generator()
        nomeDoArquivoTrabalho = "TRABALHO" + "." + token + ".pdf"
        filename = anexos.save(request.files['arquivo_trabalho'],name=nomeDoArquivoTrabalho)

    nomeDoArquivoSuplementar1 = ""
    if 'arquivo_suplementar1' in request.files:
        token = id_generator()
        nomeDoArquivoSuplementar1 = "SUPLEMENTAR1" + "." + token + ".pdf"
        filename = anexos.save(request.files['arquivo_suplementar1'],name=nomeDoArquivoSuplementar1)

    nomeDoArquivoSuplementar2 = ""
    if 'arquivo_suplementar2' in request.files:
        token = id_generator()
        nomeDoArquivoSuplementar2 = "SUPLEMENTAR2" + "." + token + ".pdf"
        filename = anexos.save(request.files['arquivo_suplementar2'],name=nomeDoArquivoSuplementar2)

    #VERIFICANDO SE O TRABALHO JÁ FOI ENVIADO
    consulta = """
    SELECT tipo,nome,titulo FROM editalProjeto WHERE tipo=""" + str(destino) + """ 
    AND titulo='""" + titulo + """' AND siape='""" + identificacao + """'"""
    linhas,total = executarSelect(consulta)
    if (total>0):
        return(u"Um trabalho com este mesmo título, CPF e edital já foi enviado ao sistema! Favor entrar em contato com a coordenação do evento!")

    consulta = """INSERT INTO editalProjeto
    (tipo,categoria,modalidade,nome,siape,email,ua,titulo,palavras,resumo,arquivo_projeto,arquivo_plano1,arquivo_plano2)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """

    valores = (destino,tipo,tipo_trabalho,nome,identificacao,email,grande_area,titulo,palavras,resumo,nomeDoArquivoTrabalho,nomeDoArquivoSuplementar1,nomeDoArquivoSuplementar2)
    inserir(consulta,valores)

    #CRIANDO SENHA DE ACESSO
    consulta = """SELECT username,password FROM users WHERE username='""" + identificacao + """'"""
    resultados,total = executarSelect(consulta)
    usuario,senha = ('','')
    if (total==0): #Se o usuário ainda não for cadastrado
        usuario = identificacao
        senha = id_generator(size=8)
        consulta = """INSERT INTO users (username,password,nome,email) VALUES (%s,%s,%s,%s) """
        valores = (usuario,senha,nome,email)
        inserir(consulta,valores)
    else:
        usuario = str(resultados[0][0])
        senha = str(resultados[0][1])

    getID = "SELECT MAX(id) FROM editalProjeto"
    ultimo_id,total = executarSelect(getID,1)
    idTrabalho = int(ultimo_id[0])
    nome_curto = obterColunaUnica('editais','nome_curto','id',str(destino))
    nome_longo = obterColunaUnica('editais','nome_longo','id',str(destino))
    email2 = "pesquisa.prpi@ufca.edu.br"
    texto_email = render_template('confirmacao_submissao.html',email_proponente=email,id_projeto=idTrabalho,proponente=nome,titulo_projeto=titulo,resumo_projeto=resumo,tipo_apresentacao=tipo,evento=nome_longo,usuario=usuario,senha=senha,link=CPPGI_SITE + 'meusProjetos')
    msg = Message(reply_to="NAO-RESPONDA@ufca.edu.br",subject = u"Plataforma Yoko - [" + nome_curto + u"] COMPROVANTE DE SUBMISSÃO DE TRABALHO",recipients=[email,email2],html=texto_email)
    t = threading.Thread(target=enviar_email,args=(msg,))
    t.start()
    return (render_template('confirmacao_submissao.html',email_proponente=email,id_projeto=idTrabalho,proponente=nome,titulo_projeto=titulo,resumo_projeto=resumo,tipo_apresentacao=tipo,evento=nome_longo,usuario=usuario,senha=senha,link=CPPGI_SITE + 'meusProjetos'))

#Devolve os nomes dos arquivos do projeto e dos planos, caso existam
def getFiles(idProjeto):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT arquivo_projeto,arquivo_plano1,arquivo_plano2 FROM editalProjeto WHERE id=" + idProjeto
    cursor.execute(consulta)
    linha = cursor.fetchone()
    conn.close()
    return(linha)

def naoEstaFinalizado(token):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT finalizado FROM avaliacoes WHERE token=\"" + token + "\""
    cursor.execute(consulta)
    linha = cursor.fetchone()
    finalizado = int(linha[0])
    conn.close()
    if finalizado==0:
        return (True)
    else:
        return (False)

def podeAvaliar(idProjeto):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    #consulta = "SELECT deadline_avaliacao,CURRENT_TIMESTAMP() FROM editais WHERE CURRENT_TIMESTAMP()<deadline_avaliacao AND id=" + codigoEdital
    consulta = "SELECT e.id as codigoEdital,e.deadline_avaliacao,p.id FROM editais e, editalProjeto p WHERE p.tipo=e.id and deadline_avaliacao>CURRENT_TIMESTAMP() AND p.id=" + idProjeto
    cursor.execute(consulta)
    total = cursor.rowcount
    cursor.close()
    conn.close()
    if (total==0): #Edital com avaliacoes encerradas
        return(False)
    else: #Edital com avaliacoes em andamento
        return(True)

#Gerar pagina de avaliacao para o avaliador
@app.route("/avaliacao", methods=['GET', 'POST'])
def getPaginaAvaliacao():
    if request.method == "GET":
        idProjeto = str(request.args.get('id'))
        if podeAvaliar(idProjeto): #Se ainda está no prazo para receber avaliações
            tokenAvaliacao = str(request.args.get('token'))
            arquivos = getFiles(idProjeto)
            if str(arquivos[0])!="0":
                link_projeto = url_for('enviar_arquivo',filename=str(arquivos[0]))
            if str(arquivos[1])!="0":
                link_plano1 = url_for('enviar_arquivo',filename=str(arquivos[1]))
            if str(arquivos[2])!="0":
                link_plano2 = url_for('enviar_arquivo',filename=str(arquivos[2]))
            links = ""
            if 'link_projeto' in locals():
                links = links + "<a href=\"" + link_projeto + "\">TRABALHO</a><BR>"
            '''
            if 'link_plano1' in locals():
                links = links + "<a href=\"" + link_plano1 + "\">ARQUIVO SUPLEMENTAR 1</a><BR>"
            if 'link_plano2' in locals():
                links = links + "<a href=\"" + link_plano2 + "\">ARQUIVO SUPLEMENTAR 2</a><BR>"
            '''
            links = links + "<input type=\"hidden\" id=\"token\" name=\"token\" value=\"" + tokenAvaliacao + "\">"
            links = Markup(links)
            if naoEstaFinalizado(tokenAvaliacao):
                consulta = "UPDATE avaliacoes SET aceitou=1 WHERE token=\"" + tokenAvaliacao + "\""
                atualizar(consulta)
                return render_template('avaliacao.html',arquivos=links)
            else:
                logging.debug("[AVALIACAO] Tentativa de reavaliar projeto")
                return("Projeto já foi avaliado! Não é possível modificar a avaliação!")
        else:
            return("Prazo de avaliação expirado!")
#Gravar avaliacao gerada pelo avaliador
@app.route("/avaliar", methods=['GET', 'POST'])
def enviarAvaliacao():
    if request.method == "POST":
        comentarios = str(request.form['txtComentarios'])
        recomendacao = str(request.form['txtRecomendacao'])
        nome_avaliador = str(request.form['txtNome'])
        token = str(request.form['token'])
        c1 = str(request.form['c1'])
        c2 = str(request.form['c2'])
        c3 = str(request.form['c3'])
        c4 = str(request.form['c4'])
        c5 = str(request.form['c5'])
        c6 = str(request.form['c6'])
        c7 = str(request.form['c7'])
        c8 = str(request.form['c8'])
        c9 = str(request.form['c9'])
        consulta = """
        SELECT id FROM avaliacoes WHERE token="%s"
        """ %(token)
        ids,total = executarSelect(consulta)
        id_avaliacao = str(ids[0][0])
        id_projeto = obterColunaUnica('avaliacoes','idProjeto','id',id_avaliacao)
        titulo = obterColunaUnica('editalProjeto','titulo','id',id_projeto)
        avaliador = obterColunaUnica('avaliacoes','avaliador','id',id_avaliacao)
        edital = obterColunaUnica('editalProjeto','tipo','id',id_projeto)
        nome_curto = obterColunaUnica('editais','nome_curto','id',edital)
        nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
        link_declaracao = url_for("getDeclaracaoAvaliador",token=token,_external=True)

        try:
            consulta = "UPDATE avaliacoes SET recomendacao=" + recomendacao + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET finalizado=1" + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET data_avaliacao=CURRENT_TIMESTAMP()" + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET nome_avaliador=\"" + nome_avaliador + "\"" + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            comentarios = comentarios.replace('"',' ')
            comentarios = comentarios.replace("'"," ")
            consulta = "UPDATE avaliacoes SET comentario=\"" + comentarios + "\"" + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c1=" + c1 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c2=" + c2 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c3=" + c3 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c4=" + c4 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c5=" + c5 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c6=" + c6 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c7=" + c7 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c8=" + c8 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
            consulta = "UPDATE avaliacoes SET c9=" + c9 + " WHERE token=\"" + token + "\""
            atualizar(consulta)
        except:
            e = sys.exc_info()[0]
            logging.error(e)
            logging.error("[AVALIACAO] ERRO ao gravar a avaliação: " + token)
            return("Não foi possível gravar a avaliação. Favor entrar contactar pesquisa.prpi@ufca.edu.br.")
        data_agora = getData()
        consulta = "SELECT editais.id,editais.nome_longo FROM editais,avaliacoes,editalProjeto WHERE avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=editais.id AND avaliacoes.token=\"" + token + "\""
        linhas = consultar(consulta)
        for linha in linhas:
            descricaoEdital = str(linha[1])
        #Enviando e-mail para o avaliador com o link
        texto_email = render_template('confirmacao_avaliacao.html',titulo=titulo,evento=nome_longo,link=link_declaracao)
        msg = Message(reply_to="NAO-RESPONDA@ufca.edu.br",subject = u"Plataforma Yoko - [" + nome_curto + u"] COMPROVANTE AVALIAÇÃO DE TRABALHO",recipients=[avaliador],html=texto_email)
        t = threading.Thread(target=enviar_email,args=(msg,))
        t.start()
        return(redirect(url_for('getDeclaracaoAvaliador',token=token)))
        #return(render_template('declaracao_avaliador.html',nome=nome_avaliador,data=data_agora,congresso=descricaoEdital,raiz=ROOT_SITE,titulo=titulo))
    else:
        return("OK")

def descricaoEdital(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT id,nome FROM editais WHERE id=" + codigoEdital
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    nomeEdital = "EDITAL NAO DEFINIDO"
    for linha in linhas:
        nomeEdital = str(linha[1])
    conn.close()
    return (nomeEdital)

#Gerar declaração do avaliador
@app.route("/declaracaoAvaliador", methods=['GET'])
def getDeclaracaoAvaliador():
    if request.method == "GET":
        tokenAvaliacao = str(request.args.get('token'))
        consulta = "SELECT nome_avaliador FROM avaliacoes WHERE token=\"" + tokenAvaliacao + "\""
        linhas = consultar(consulta)
        nome_avaliador = "NAO INFORMADO"
        for linha in linhas:
            nome_avaliador = str(linha[0])
        data_agora = getData()
        #Recuperando descrição do edital
        consulta = "SELECT editais.id,editais.nome_longo FROM editais,avaliacoes,editalProjeto WHERE avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=editais.id AND avaliacoes.token=\"" + tokenAvaliacao + "\""
        linhas = consultar(consulta)
        for linha in linhas:
            descricaoEdital = str(linha[1])
            edital = str(linha[0])
        
        #Gerando declaração e enviando ao navegador
        token=tokenAvaliacao
        consulta = "SELECT id FROM avaliacoes WHERE token=\"" + tokenAvaliacao + "\""
        ids,total = executarSelect(consulta)
        id_avaliacao = str(ids[0][0])
        id_projeto = obterColunaUnica('avaliacoes','idProjeto','id',id_avaliacao)
        titulo = obterColunaUnica('editalProjeto','titulo','id',id_projeto)
        template = obterColunaUnica('editais','declaracao_avaliador','id',edital)
        periodo = obterColunaUnica('editais','periodo','id',edital)
        local = obterColunaUnica('editais','local','id',edital)
        arquivoCertificado = app.config['CERTIFICADOS_FOLDER'] + 'certificado.pdf'
        options = {
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0cm',
            'margin-right': '0cm',
            'margin-bottom': '0cm',
            'margin-left': '0cm',
        }
        
        #Gerando QrCode
        qrcode_url = url_for('autenticar_certificado',tipo=4,codigo=token,id_projeto=id_projeto,_external=True)
        qrcode = pyqrcode.create(qrcode_url)
        qrcode.png(CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png',scale=3)
        qr_code = get_image_file_as_base64_data(CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png')

        #Recuperando template
        background = get_image_file_as_base64_data(CERTIFICADOS_TEMPLATE_DIR + template)
        
        #Gerando certificado em PDF
        try:
            app.logger.error(CERTIFICADOS_TEMPLATE_DIR + template)
            pdfkit.from_string(render_template('certificado_avaliador.html',nome=nome_avaliador,titulo=titulo,periodo=periodo,evento=descricaoEdital,identificador=id_projeto,local=local,arquivo=template,background=background,qrcode=qr_code,token=token,tipo=4,data="Juazeiro do Norte, " + getData()),arquivoCertificado,options=options)
        except Exception as e:
            app.logger.error('Erro gerando certificado avaliador')
            app.logger.error(str(e))
        finally:
            return send_from_directory(app.config['CERTIFICADOS_FOLDER'], 'certificado.pdf')

def consultar(consulta):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    conn.close()
    return (linhas)

@app.route("/recusarConvite", methods=['GET', 'POST'])
def recusarConvite():
    if request.method == "GET":
        tokenAvaliacao = str(request.args.get('token'))
        consulta = "UPDATE avaliacoes SET aceitou=0 WHERE token=\"" + tokenAvaliacao + "\""
        atualizar(consulta)
        return("Avaliação cancelada com sucesso. Agradecemos a atenção.")
    else:
        return("OK")

@app.route("/avaliacoesNegadas", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def avaliacoesNegadas():
    if request.method == "GET":
        conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
        conn.select_db('cppgi')
        cursor  = conn.cursor()
        if 'edital' in request.args:
            codigoEdital = str(request.args.get('edital'))
            if 'id' in request.args:
                idProjeto = str(request.args.get('id'))
                consulta = "SELECT id,titulo FROM editalProjeto WHERE tipo=" + codigoEdital + " AND id=" + idProjeto
                identificador = obterColunaUnica('editalProjeto','siape','id',idProjeto)
                area = obterColunaUnica('editalProjeto','ua','id',idProjeto)
                possiveis_avaliadores = """
                SELECT DISTINCT avaliacoes.avaliador,avaliacoes.nome_avaliador FROM avaliacoes 
                INNER JOIN editalProjeto ON editalProjeto.id=avaliacoes.idProjeto
                WHERE editalProjeto.siape="%s"
                AND avaliacoes.finalizado=1 ORDER BY avaliacoes.nome_avaliador
                """ % (identificador)
                avaliadores_sugeridos,total = executarSelect(possiveis_avaliadores)
                avaliadores_area = """
                SELECT DISTINCT avaliacoes.avaliador,UPPER(avaliacoes.nome_avaliador) FROM avaliacoes 
                INNER JOIN editalProjeto ON editalProjeto.id=avaliacoes.idProjeto
                WHERE editalProjeto.ua="%s"
                AND avaliacoes.finalizado=1 ORDER BY avaliacoes.nome_avaliador
                """ % (area)
                lista_area,total = executarSelect(avaliadores_area)
            else:
                consulta = "SELECT resumoGeralAvaliacoes.id,CONCAT(SUBSTRING(resumoGeralAvaliacoes.titulo,1,80),\" - (\",resumoGeralAvaliacoes.nome,\" )\"),(resumoGeralAvaliacoes.aceites+resumoGeralAvaliacoes.rejeicoes) as resultado,resumoGeralAvaliacoes.indefinido FROM resumoGeralAvaliacoes WHERE ((aceites+rejeicoes<2) OR (aceites=rejeicoes)) AND tipo=" + codigoEdital + " ORDER BY aceites+rejeicoes, id"
            try:
                cursor.execute(consulta)
                linha = cursor.fetchall()
                total = cursor.rowcount
                return(render_template('inserirAvaliador.html',listaProjetos=linha,totalDeLinhas=total,codigoEdital=codigoEdital,avaliadores=avaliadores_sugeridos,avaliadores_area=lista_area,area=area))
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                logging.error(consulta)
                return(consulta)
        else:
            return ("OK")
    else:
        return("OK")

@app.route("/inserirAvaliador", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def inserirAvaliador():
    if request.method == "POST":
        token = id_generator(40)
        idProjeto = int(request.form['txtProjeto'])
        avaliadores = []
        if (request.form.getlist('avaliador_sugerido')==[]):
            if (request.form.getlist('avaliador_area')==[]):
                avaliador1_email = str(request.form['txtEmail'])
                avaliadores.append(avaliador1_email)
            else:
                #avaliador1_email = str(request.form['avaliador_area'])
                avaliadores = request.form.getlist('avaliador_area')
        else:
            #avaliador1_email = str(request.form['avaliador_sugerido']);
            avaliadores = request.form.getlist('avaliador_sugerido')
        
        for avaliador1_email in avaliadores:
            token = id_generator(40)
            edital = obterColunaUnica('editalProjeto','tipo','id',str(idProjeto))
            
            deadline = obterColunaUnica('editais','deadline_avaliacao','id',str(edital))
            agora = datetime.datetime.now().strftime('%Y-%m-%d')
            if agora>deadline:
                flash(u"Prazo de avaliação expirado!")
                return(redirect(url_for('listar_consultores',id_projeto=idProjeto)))

            consulta = "INSERT INTO avaliacoes (aceitou,avaliador,token,idProjeto) VALUES (-1,\"" + avaliador1_email + "\", \"" + token + "\", " + str(idProjeto) + ")"
            #Verificando se existe avaliador para o ID
            consulta2 = """
            SELECT * from avaliacoes WHERE avaliador='""" + avaliador1_email +"""' AND 
            idProjeto=""" + str(idProjeto)
            linhas,total=executarSelect(consulta2)
            if total==0:
                atualizar(consulta)
            
            update = """UPDATE avaliacoes SET enviado=enviado+1,data_envio=NOW() WHERE avaliador='""" + avaliador1_email +"""' AND 
            idProjeto=""" + str(idProjeto)
            atualizar(update)
            flash(u"Avaliador incluído com sucesso: " + avaliador1_email)
        t = threading.Thread(target=enviarPedidoAvaliacao,args=(idProjeto,))
        t.start()
        return(redirect(url_for('listar_consultores',id_projeto=idProjeto)))
        
    else:
        return("OK")

#Retorna a quantidade de linhas da consulta
def quantidades(consulta):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    cursor.execute(consulta)
    total = cursor.rowcount
    conn.close()
    return (total)


def executarSelect(consulta,tipo=0):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    try:
        cursor.execute("SET SESSION group_concat_max_len = 6000")
        cursor.execute(consulta)
        total = cursor.rowcount
        if (tipo==0): #Retorna todas as linhas
            resultado = cursor.fetchall()
        else: #Retorna uma única linha
            resultado = cursor.fetchone()
        return (resultado,total)
    except:
        e = sys.exc_info()[0]
        logging.error(e)
        logging.error("ERRO Na função executarSelect. Ver consulta abaixo.")
        logging.error(consulta)
    finally:
        cursor.close()
        conn.close()


def avaliacoesEncerradas(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT deadline_avaliacao,CURRENT_TIMESTAMP() FROM editais WHERE CURRENT_TIMESTAMP()<deadline_avaliacao AND id=" + codigoEdital
    cursor.execute(consulta)
    total = cursor.rowcount
    conn.close()
    if (total>0): #Edital com avaliacoes encerradas
        return(False)
    else: #Edital com avaliacoes em andamento
        return(True)

def gerarPDF(template):
    
    try:
        arquivoDeclaracao = app.config['TEMP_FOLDER'] + 'resultados.pdf'
        options = {
            'page-size': 'A4',
            'margin-top': '2cm',
            'margin-right': '2cm',
            'margin-bottom': '1cm',
            'margin-left': '2cm',
        }
        pdfkit.from_string(template,arquivoDeclaracao,options=options)
    except:
        e = sys.exc_info()[0]
        logging.error(e)
        logging.error("ERRO Na função gerarPDF")
    #return send_from_directory(app.config['TEMP_FOLDER'], 'resultados.pdf')

@app.route("/editalProjeto/<edital>", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def editalProjeto(edital):

    if (autenticado() and int(session['permissao'])==0):
        codigoEdital = str(edital)
        conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
        conn.select_db('cppgi')
        cursor  = conn.cursor()

        consulta = """SELECT id,tipo,categoria,modalidade,nome,email,ua,titulo,arquivo_projeto,arquivo_plano1,arquivo_plano2
        ,DATE_FORMAT(data,'%d/%m/%Y - %H:%i') as data,situacao FROM editalProjeto
        WHERE tipo=""" + codigoEdital + """ AND valendo=1 ORDER BY ua,nome"""
        
        consulta_novos = """SELECT editalProjeto.id,nome,ua,titulo,arquivo_projeto,
        GROUP_CONCAT(avaliacoes.avaliador ORDER BY avaliador SEPARATOR '<BR>') as avaliadores,
        GROUP_CONCAT(avaliacoes.recomendacao ORDER BY avaliador SEPARATOR '<BR>') as recomendacoes,
        GROUP_CONCAT(avaliacoes.enviado ORDER BY avaliador SEPARATOR '<BR>') as enviado,
        GROUP_CONCAT(avaliacoes.aceitou ORDER BY avaliador SEPARATOR '<BR>') as aceitou,
        sum(avaliacoes.finalizado) as finalizados,
        sum(if(recomendacao=-1,1,0)), 
        sum(if(recomendacao=0,1,0)),
        sum(if(recomendacao=1,1,0)),
        palavras,editalProjeto.situacao,
        IF(editalProjeto.modalidade=0,'RESUMO SIMPLES',IF(editalProjeto.modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO'))"""
        consulta_novos = consulta_novos + """ FROM editalProjeto LEFT JOIN avaliacoes on editalProjeto.id=avaliacoes.idProjeto WHERE tipo=""" + codigoEdital + """ AND valendo=1
        GROUP BY editalProjeto.id ORDER BY finalizados,editalProjeto.ua,editalProjeto.modalidade,editalProjeto.id"""

        demanda = """SELECT ua,count(id) FROM editalProjeto WHERE valendo=1 and tipo=""" + codigoEdital + """ GROUP BY ua ORDER BY ua"""

        dadosAvaliacoes = """SELECT if(finalizado=1,"FINALIZADO","EM AVALIAÇÃO/NÃO SINALIZOU") as finalizados,count(avaliacoes.id) FROM avaliacoes,editalProjeto WHERE editalProjeto.id=avaliacoes.idProjeto AND
        tipo=""" + codigoEdital + """ AND valendo=1 AND aceitou!=0 GROUP BY finalizado"""

        tempoAvaliacao = """SELECT TIMESTAMPDIFF(DAY,data_envio,data_avaliacao) as tempo,count(avaliacoes.id) total FROM avaliacoes,editalProjeto WHERE editalProjeto.id=avaliacoes.idProjeto AND valendo=1 and
        tipo=""" + codigoEdital + """ and finalizado=1 GROUP BY TIMESTAMPDIFF(DAY,data_envio,data_avaliacao)"""

        descricao = descricaoEdital(codigoEdital)

        cursor.execute(consulta)
        total = cursor.rowcount
        linhas = cursor.fetchall()

        cursor.execute(consulta_novos)
        total_novos = cursor.rowcount
        linhas_novos = cursor.fetchall()

        cursor.execute(demanda)
        linhas_demanda = cursor.fetchall()
        cursor.close()
        conn.close()
        if 'resultado' in request.args:
            if 'pdf' in request.args:
                mensagem = str(obterColunaUnica("editais","mensagem","id",codigoEdital))
                gerarPDF(render_template('editalProjeto.html',listaProjetos=linhas,descricao=descricao,total=total,novos=linhas_novos,total_novos=total_novos,linhas_demanda=linhas_demanda,codigoEdital=codigoEdital,resultado=1,mensagem=mensagem,tabela="editalProjeto"))
                return(send_from_directory(app.config['TEMP_FOLDER'], 'resultados.pdf'))
            else:
                mensagem = str(obterColunaUnica("editais","mensagem","id",codigoEdital))
                return(render_template('editalProjeto.html',listaProjetos=linhas,descricao=descricao,total=total,novos=linhas_novos,total_novos=total_novos,linhas_demanda=linhas_demanda,codigoEdital=codigoEdital,resultado=1,mensagem=mensagem,tabela="editalProjeto"))
        else:
            mensagem = ""
            return(render_template('editalProjeto.html',listaProjetos=linhas,descricao=descricao,total=total,novos=linhas_novos,total_novos=total_novos,linhas_demanda=linhas_demanda,codigoEdital=codigoEdital,resultado=0,todos=0,mensagem=mensagem,tabela="editalProjeto"))
    
    else:
        return(render_template('login.html',mensagem=u"É necessário autenticação para acessar a página solicitada"))

@app.route("/declaracoesPorServidor", methods=['GET', 'POST'])
def declaracoesServidor():
    if request.method == "POST":
        if 'txtSiape' in request.form:
            siape = str(request.form['txtSiape'])
            consulta = ""
            try:
                consulta = "SELECT id,nome,evento,modalidade FROM declaracoes WHERE siape=" + siape
                declaracoes,total = executarSelect(consulta)
                return(render_template('declaracoes_servidor.html',listaDeclaracoes=declaracoes))
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                logging.error("ERRO Na função /declaracoesPorServidor. Ver consulta abaixo.")
                logging.error(consulta)
                return("ERRO!")
        else:
            return("OK")
    else:
        return("OK")

@app.route("/declaracaoEvento", methods=['GET', 'POST'])
def declaracaoEvento():
    if request.method == "GET":
        #Recuperando o código da declaração
        if 'id' in request.args:
            idDeclaracao = str(request.args.get('id'))
            consulta = "SELECT nome,siape,participacao,evento,modalidade,periodo,local FROM declaracoes WHERE id=" + idDeclaracao
            linhas,total = executarSelect(consulta)
            if (total>0):
                texto = linhas[0]
                data_agora = getData()
                return(render_template('declaracao_evento.html',texto=texto,data=data_agora,identificador=idDeclaracao))
            else:
                return(u"Nenhuma declaração encontrada.")
        else:
            return ("OK")

@app.route("/meusProjetos", methods=['GET', 'POST'])
def meusProjetos():
    if autenticado():

        consulta_outros = """SELECT editalProjeto.id,editais.nome,editalProjeto.nome,ua,titulo,modalidade,arquivo_projeto,
        (SELECT COUNT(recomendacao) FROM `avaliacoes` WHERE finalizado=1 AND recomendacao=1 AND idProjeto=editalProjeto.id) as aprovados,
        (SELECT COUNT(recomendacao) FROM `avaliacoes` WHERE finalizado=1 AND recomendacao=0 AND idProjeto=editalProjeto.id) as reprovados,
        categoria,editais.situacao,editais.id, editalProjeto.arquivo_projeto_final,
        editalProjeto.situacao, editalProjeto.obs,editalProjeto.link_apresentacao,
        editalProjeto.local_apresentacao,DATE_FORMAT(editalProjeto.data_apresentacao,'%d/%m/%Y %H:%i')  
         FROM editalProjeto,editais WHERE valendo=1 AND editalProjeto.tipo=editais.id AND siape='""" + str(session['username']) + """' ORDER BY editalProjeto.data """
        projetos2019,total2019 = executarSelect(consulta_outros)

        return(render_template('meusProjetos.html',projetos2019=projetos2019,total2019=total2019,permissao=session['permissao'],SITE=CPPGI_SITE))
    else:
        return(render_template('login.html',mensagem=u"É necessário autenticação para acessar a página solicitada"))

@app.route("/meusPareceres", methods=['GET', 'POST'])
def meusPareceres():
    if request.method == "GET":
        #Recuperando o id do Projeto
        if 'id' in request.args:
            idProjeto = str(request.args.get('id'))
            if autenticado():
                tituloProjeto = str(obterColunaUnica("editalProjeto","titulo","id",idProjeto))
                if ('todos' in request.args) and (session['permissao']==0):
                    consulta = """SELECT avaliacoes.id,c1,c2,c3,c4,c5,c6,c7,c8,c9,(c1+c2+c3+c4+c5+c6+c7+c8+c9) as pontuacaoTotal, comentario, if(recomendacao=1,'RECOMENDADO','NÃO RECOMENDADO') as recomendacao, DATE_FORMAT(data_avaliacao,'%d/%m/%Y') FROM avaliacoes WHERE finalizado=1 AND idProjeto=""" + idProjeto + """ ORDER BY data_avaliacao"""
                else:
                    consulta = """SELECT avaliacoes.id,c1,c2,c3,c4,c5,c6,c7,c8,c9,(c1+c2+c3+c4+c5+c6+c7+c8+c9) as pontuacaoTotal, comentario, if(recomendacao=1,'RECOMENDADO','NÃO RECOMENDADO') as recomendacao, DATE_FORMAT(data_avaliacao,'%d/%m/%Y') FROM avaliacoes,editalProjeto WHERE editalProjeto.id=avaliacoes.idProjeto AND finalizado=1 AND idProjeto=""" + idProjeto + """ AND siape='""" + str(session['username']) + """' ORDER BY data_avaliacao"""
                pareceres,total = executarSelect(consulta)
                return(render_template('meusPareceres.html',linhas=pareceres,total=total,titulo=tituloProjeto))
            else:
                return(render_template('login.html',mensagem=u"É necessário autenticação para acessar a página solicitada"))
        else:
            return("OK")
    else:
        return("OK")

@app.route("/usuario", methods=['GET', 'POST'])
def usuario():
    if autenticado():
        if ('admin' in session['roles']):
            return(redirect(url_for('root')))
        if ('avaliador' in session['roles']):
            return(redirect(url_for('home')))
        return(redirect(url_for('meusProjetos')))
    else:
        return(render_template('login.html',mensagem=''))

def getNome(username):
    consulta = """SELECT nome FROM users WHERE username='""" + username + """'"""
    linhas,total = executarSelect(consulta)
    for linha in linhas:
        return (str(linha[0]))
    return("INDEFINIDO")

@app.route("/avaliador/<edital>", methods=['GET'])
@auth.login_required(role=['avaliador','admin'])
def avaliador(edital):
    session['edital'] = edital
    nome_edital = obterColunaUnica('editais','nome','id',edital)
    consulta = """SELECT sala,data FROM usuarios_salas WHERE edital=""" + edital + """ and username='""" + str(session['username']) + """' ORDER BY data,sala"""
    linhas,total = executarSelect(consulta)
    nome_usuario = getNome(str(session['username']))
    return(render_template('avaliador.html',linhas=linhas,nome_edital=nome_edital,root=CPPGI_SITE,edital=edital,usuario=session['username'],nome_usuario=nome_usuario,titulo=u'MÓDULO AVALIADOR'))

'''
Método que ativa a sessão com os dados do usuário
'''
@app.route("/login", methods=['POST'])
def login():
    if request.method == "POST":
        if (('siape' in request.form) and ('senha' in request.form)):
            siape = str(request.form['siape'])
            senha = str(request.form['senha'])
            if verify_password(siape,senha)!=False:
                return(redirect(url_for('usuario')))
            else:
                return(render_template('login.html',mensagem='Problemas com o usuario/senha.'))
        else:
            return(render_template('login.html',mensagem='Problemas com o usuario/senha.'))
    else:
        return(render_template('login.html',mensagem=''))

@app.route("/esqueciMinhaSenha", methods=['GET', 'POST'])
def esqueciMinhaSenha():
    return(render_template('esqueciMinhaSenha.html'))

@app.route("/enviarMinhaSenha", methods=['GET', 'POST'])
def enviarMinhaSenha():
    if request.method == "POST":
        if ('email' in request.form):
            email = str(request.form['email'])
            #ENVIAR E-MAIL
            consulta = """SELECT username,password FROM users WHERE email='""" + email + """' """
            linhas,total = executarSelect(consulta,1)

            if (total>0):
                usuario = str(linhas[0])
                senha = str(linhas[1])
                texto_mensagem = "Usuario: " + usuario + "\nSenha: " + senha + "\n" + USUARIO_SITE
                msg = Message(reply_to="NAO-RESPONDA@ufca.edu.br",subject = "Plataforma Yoko - Lembrete de senha",recipients=[email],body=texto_mensagem)
                if PRODUCAO==1:
                    mail.send(msg)
                return(render_template('login.html',mensagem='Senha enviada para o email: ' + email))
            else:
                return(render_template('login.html',mensagem=u'E-mail não cadastrado. Envie e-mail para atendimento.prpi@ufca.edu.br para solicitar sua senha.'))
        else:
            return("OK")
    else:
        return("OK")

@app.route("/logout", methods=['GET', 'POST'])
def encerrarSessao():
    logout()
    return(render_template('login.html',mensagem=''))

def projetoAprovado(idProjeto):

    categoria = int(obterColunaUnica("editalProjeto","categoria","id",str(idProjeto)))

    if categoria==0:
        return (True)
    else:
        consulta = """SELECT sum(if(recomendacao=0,1,0)) as rejeitados, sum(if(recomendacao=1,1,0)) as aprovados FROM avaliacoes WHERE idProjeto=""" + str(idProjeto)
        resultado,total = executarSelect(consulta,1)
        avaliacoes = int(resultado[0]) + int(resultado[1])
        if avaliacoes>1:
            if (resultado[1]>resultado[0]):
                return (True)
            else:
                return (False)
        else:
            return(False)

def tuplaDeEditais(ano):
    inicio = ano + "-04-01"
    fim = ano + "-12-31"
    consulta = """SELECT id FROM editais WHERE DATE(deadline)>'""" + inicio + """' AND DATE(deadline)<'""" + fim + """' AND nome not like '%contínuo%'"""
    editais,total = executarSelect(consulta)
    codigos = []
    for linha in editais:
        codigos.append(int(linha[0]))
    if total>0:
        resultado = str(tuple(codigos))
        return (resultado)
    else:
        return (0)


@app.route("/cruzarDados", methods=['GET', 'POST'])
def cruzarDados():
    if request.method == "GET":
        #Recuperando o ano dos editais
        if 'ano' in request.args:
            ano = str(request.args.get('ano'))
            if ((autenticado()) and (session['permissao']==0)):
                editais = tuplaDeEditais(ano)
                if (editais!=0):
                    consulta = """SELECT siape,editalProjeto.nome,sum(bolsas_concedidas),GROUP_CONCAT(editais.nome ORDER BY tipo SEPARATOR '<BR>') as editais, GROUP_CONCAT(modalidades.descricao ORDER BY tipo SEPARATOR '<BR>') as tipos FROM editalProjeto,modalidades,editais WHERE modalidades.id=editalProjeto.modalidade AND editalProjeto.tipo=editais.id AND valendo=1 and tipo in """ + editais + """ AND modalidade in (1,2,3) GROUP BY siape ORDER BY nome"""
                    linhas,total = executarSelect(consulta)
                    return(render_template('bolsasPorAno.html',linhas=linhas,ano=ano,total=total))
                else:
                    return("Sem dados disponíveis!")
            else:
                return("Acesso negado!")
        else:
            return("OK")
    else:
        return("OK")

def idSiape(id,siape):
    siapeObtido = obterColunaUnica('editalProjeto','siape','id',id)
    if siape=="0":
        return (False)
    else:
        if (siapeObtido==siape):
            return(True)
        else:
            return(False)

@app.route("/verArquivo", methods=['GET', 'POST'])
def verArquivo():
    if request.method == "GET":
        #Recuperando arquivo
        if 'file' in request.args:
            arquivo = str(request.args['file'])
            if os.path.isfile(ATTACHMENTS_DIR + arquivo):
                return(send_from_directory(app.config['UPLOADED_DOCUMENTS_DEST'], arquivo))
            else:
                return("Arquivo não encontrado!")
        else:
            return("OK")
    else:
        return("OK")

@app.route("/estatisticas", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def estatisticas():

    if request.method == "GET":
        #Recuperando o ano dos editais
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            c1 = "SELECT id FROM editalProjeto where valendo=1 and tipo=" + edital
            linhas,totalSubmissoes = executarSelect(c1)

            c2 = "SELECT avaliacoes.id FROM avaliacoes,editalProjeto WHERE avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital
            linhas,totalAvaliacoes = executarSelect(c2)

            c3 = "SELECT avaliacoes.id FROM avaliacoes,editalProjeto WHERE aceitou=0 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital
            linhas,totalAvaliacoesNegadas = executarSelect(c3)

            c4 = "SELECT avaliacoes.id FROM avaliacoes,editalProjeto WHERE finalizado=1 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital
            linhas,totalAvaliacoesFinalizadas = executarSelect(c4)

            c5 = "SELECT avaliacoes.idProjeto,count(avaliacoes.id) as total FROM avaliacoes,editalProjeto WHERE finalizado=1 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital + " GROUP by idProjeto HAVING total>=2"
            linhas,totalAvaliacoesConcluidas = executarSelect(c5)

            c6 = "SELECT avaliacoes.idProjeto,(sum(if(recomendacao=1,1,0))-sum(if(recomendacao=0,1,0))) as diferenca, (sum(if(recomendacao=1,1,0))+sum(if(recomendacao=0,1,0))) as total FROM avaliacoes,editalProjeto WHERE finalizado=1 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital + " GROUP by idProjeto HAVING (total=1)"
            linhas,totalAvaliacoesPendentes = executarSelect(c6)

            c7 = "SELECT avaliacoes.idProjeto,(sum(if(recomendacao=1,1,0))-sum(if(recomendacao=0,1,0))) as diferenca, (sum(if(recomendacao=1,1,0))+sum(if(recomendacao=0,1,0))) as total FROM avaliacoes,editalProjeto WHERE finalizado=1 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital + " GROUP by idProjeto HAVING (diferenca>0 and total>1)"
            linhas,totalSubmissoesAprovadas = executarSelect(c7)

            c8 = "SELECT avaliacoes.idProjeto,(sum(if(recomendacao=1,1,0))-sum(if(recomendacao=0,1,0))) as diferenca, (sum(if(recomendacao=1,1,0))+sum(if(recomendacao=0,1,0))) as total FROM avaliacoes,editalProjeto WHERE finalizado=1 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital + " GROUP by idProjeto HAVING (diferenca<0 and total>1)"
            linhas,totalSubmissoesReprovadas = executarSelect(c8)

            c9 = "SELECT avaliacoes.idProjeto,(sum(if(recomendacao=1,1,0))-sum(if(recomendacao=0,1,0))) as diferenca, (sum(if(recomendacao=1,1,0))+sum(if(recomendacao=0,1,0))) as total FROM avaliacoes,editalProjeto WHERE finalizado=1 AND avaliacoes.idProjeto=editalProjeto.id AND editalProjeto.tipo=" + edital + " GROUP by idProjeto HAVING (diferenca=0 and total>1)"
            linhas,totalSubmissoesIndefinidas = executarSelect(c9)

            totalSubmissoesDefinidas = totalSubmissoesAprovadas+totalSubmissoesReprovadas

            #totalAvaliacoesZeradas = totalSubmissoes - totalAvaliacoesConcluidas - totalAvaliacoesPendentes
            try:
                totalAvaliacoesZeradas = totalSubmissoes - totalSubmissoesAprovadas - totalSubmissoesReprovadas - totalSubmissoesIndefinidas - totalAvaliacoesPendentes
                progresso = ((totalSubmissoesAprovadas + totalSubmissoesReprovadas)/float(totalSubmissoes))*100
                nomeEdital = obterColunaUnica('editais','nome','id',edital)
                return(render_template('estatisticas.html',totalSubmissoesAprovadas=totalSubmissoesAprovadas,totalSubmissoesReprovadas=totalSubmissoesReprovadas,totalSubmissoesIndefinidas=totalSubmissoesIndefinidas,totalSubmissoesDefinidas=totalSubmissoesDefinidas,nomeEdital=nomeEdital,total = totalSubmissoes,totalAvaliacoes=totalAvaliacoes,totalAvaliacoesNegadas=totalAvaliacoesNegadas,totalAvaliacoesFinalizadas=totalAvaliacoesFinalizadas,totalAvaliacoesConcluidas=totalAvaliacoesConcluidas,totalAvaliacoesPendentes=totalAvaliacoesPendentes,totalAvaliacoesZeradas=totalAvaliacoesZeradas,progresso=progresso))
            except Exception as e:
                return('Estatísticas ainda não disponíveis!')
        else:
            return("Edital?")
    else:
        return("Acesso negado.")

@app.route("/resultados", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def resultados():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND tipo=""" + edital
            principal,total = executarSelect(consulta_principal)
            for linha in principal:
                id = str(linha[0])
                consulta_interna = """SELECT sum(if(recomendacao=1,1,0))-sum(if(recomendacao=0,1,0)),sum(finalizado) FROM avaliacoes WHERE idProjeto=""" + id
                auxiliar,totalAuxiliar = executarSelect(consulta_interna,1)
                pontuacao = int(auxiliar[0])
                finalizado = int(auxiliar[1])
                if (pontuacao<0):
                    '''
                    if (finalizado>1):
                        situacao = str("0")
                    else:
                        situacao = str("1")
                    '''
                    situacao = "0"
                else:
                    situacao = str("1")
                consulta_update = "UPDATE editalProjeto SET situacao=" + situacao + " WHERE id=" + id
                atualizar(consulta_update)

            consulta_poster = """SELECT editalProjeto.id,ua,nome,titulo,situacao,IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')) as modalid,local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),local_apresentacao FROM editalProjeto WHERE valendo=1 AND categoria=1 AND tipo=""" + edital + """ ORDER BY ua,modalidade DESC,nome,titulo"""
            consulta_oral = """SELECT editalProjeto.id,ua,nome,titulo,situacao,IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')) as modalid,local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),local_apresentacao FROM editalProjeto WHERE valendo=1 AND categoria=0 AND tipo=""" + edital + """ ORDER BY ua,modalidade DESC,nome,titulo"""
            poster,total_poster = executarSelect(consulta_poster)
            oral,total_oral = executarSelect(consulta_oral)
            data = getData()
            return(render_template('resultados.html',oral=oral,poster=poster,data=data,total_poster=total_poster,total_oral=total_oral,nome_edital=nome_edital,titulo="RESULTADOS"))

        else:
            return("OK")
    else:
        return("OK")

def getSlots(dia,start_time,end_time,slot_time,salas):
    hours = []
    local = []
    time = datetime.datetime.strptime(start_time, '%H:%M')
    end = datetime.datetime.strptime(end_time, '%H:%M')
    for sala in salas:
        time = datetime.datetime.strptime(start_time, '%H:%M')
        end = datetime.datetime.strptime(end_time, '%H:%M')
        while time <= end:
            hours.append(dia + " " + time.strftime("%H:%M"))
            time += datetime.timedelta(minutes=slot_time)
            local.append(sala)
    return (hours,local)

def getSessoesSalas(edital,tipo):
    consulta = """SELECT dia,DATE_FORMAT(inicio,'%H:%i'),DATE_FORMAT(termino,'%H:%i'),slot,salas FROM salas WHERE edital=""" + str(edital) + """ AND tipo=""" + str(tipo) + """ ORDER BY dia,inicio"""
    linhas,total = executarSelect(consulta)
    turno_todos = []
    local_todos = []
    for linha in linhas:
        dia = str(linha[0])
        inicio = str(linha[1])
        termino = str(linha[2])
        slot = int(linha[3])
        salas = str(linha[4])
        salas = salas.split(",")
        turno,local = getSlots(dia,inicio,termino,slot,salas)
        turno_todos = turno_todos + turno
        local_todos = local_todos + local
    return (turno_todos,local_todos)

def getSessoesPosters(edital):
    consulta = """SELECT dia,DATE_FORMAT(inicio,'%H:%i'),salas FROM salas WHERE edital=""" + str(edital) + """ AND tipo=1 ORDER BY tipo,dia,inicio"""
    linhas,total = executarSelect(consulta)
    for linha in linhas:
        dia = str(linha[0])
        inicio = str(linha[1])
        salas = str(linha[2])
        return(dia,inicio,salas)

@app.route("/distribuirSalas", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def distribuirSalas():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            turno_todos,local_todos=getSessoesSalas(edital,"0")
            #APRESENTAÇÕES ORAIS - PREMIACAO
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND situacao=1 AND categoria=0 AND tipo=""" + edital + " and premiacao=1 ORDER BY premiacao DESC,ua DESC,modalidade DESC,media1 DESC,nome,titulo"
            principal,total = executarSelect(consulta_principal)
            
            i = 0
            for linha in principal:
                id = str(linha[0])
                try:
                    update = """UPDATE editalProjeto SET local_apresentacao='""" + local_todos[i] + """' WHERE id=""" + id
                    atualizar(update)
                    update = update = """UPDATE editalProjeto SET data_apresentacao='""" + turno_todos[i] + """' WHERE id=""" + id
                    atualizar(update)
                except IndexError:
                    logging.error('Erro no indice: ' + str(i))
                    break
                i = i + 1
            
            #APRESENTAÇÕES ORAIS - DEMAIS
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND situacao=1 AND categoria=0 AND tipo=""" + edital + " and premiacao=0 ORDER BY ua DESC,modalidade DESC,media1 DESC,nome,titulo"
            principal,total = executarSelect(consulta_principal)
            
            for linha in principal:
                id = str(linha[0])
                try:
                    update = """UPDATE editalProjeto SET local_apresentacao='""" + local_todos[i] + """' WHERE id=""" + id
                    atualizar(update)
                    update = update = """UPDATE editalProjeto SET data_apresentacao='""" + turno_todos[i] + """' WHERE id=""" + id
                    atualizar(update)
                    
                except IndexError:
                    logging.error('Erro no indice: ' + str(i))
                    break
                i = i + 1

            #POSTERS
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND situacao=1 AND categoria=1 AND tipo=""" + edital + " ORDER BY ua,nome,titulo"
            principal,total = executarSelect(consulta_principal)
            i = 1
            data_apresentacao,inicio,local_apresentacao = getSessoesPosters(edital)
            data_apresentacao = data_apresentacao + " " + inicio
            
            for linha in principal:
                id = str(linha[0])
                
                update = """UPDATE editalProjeto SET local_apresentacao='""" + local_apresentacao + """' WHERE id=""" + id
                atualizar(update)
                update = update = """UPDATE editalProjeto SET data_apresentacao='""" + data_apresentacao + """' WHERE id=""" + id
                atualizar(update)
                i = i + 1
            
            return(redirect(url_for('programacao',edital=edital)))
        else:
            return("OK")
    else:
        return("OK")

@app.route("/programacao", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def programacao():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            
            final_oral = """select local_apresentacao, GROUP_CONCAT(id,concat_ws(' - ',IF(premiacao=1,'(*)',''),ua,IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')),'<b>',DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),'</b>','<i>',titulo,'</i>',nome) ORDER BY local_apresentacao,ua,data_apresentacao SEPARATOR '<BR><BR><hr>')

                        FROM editalProjeto

                        WHERE valendo=1 and situacao=1 AND categoria=0 AND tipo=""" + edital + """ GROUP BY local_apresentacao

                        ORDER BY ua,local_apresentacao,data_apresentacao """

            final_poster = """select local_apresentacao, GROUP_CONCAT(id,' ',concat_ws(' - ',ua,IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')),'<b>',DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),'</b>','<i>',titulo,'</i>',nome) ORDER BY local_apresentacao,ua,data_apresentacao SEPARATOR '<BR><BR>')

                        FROM editalProjeto

                        WHERE valendo=1 and situacao=1 AND categoria=1 AND tipo=""" + edital + """ GROUP BY local_apresentacao

                        ORDER BY ua,local_apresentacao,data_apresentacao """

            linhas,total = executarSelect(final_oral)
            poster,total_poster = executarSelect(final_poster)
            return(render_template('programacao.html',nome_edital=nome_edital,titulo=u'Programação',oral=linhas,total=total,poster=poster,total_poster=total_poster))
        else:
            return("OK")
    else:
        return("OK")

@app.route("/mapa", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def mapa():
    if 'edital' in request.args:
        edital = str(request.args.get('edital'))
        nome_edital = obterColunaUnica('editais','nome','id',edital)
        '''
        consulta = """SELECT local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y'),count(id),
        GROUP_CONCAT('<p style=\"background-color: #FCFF33;\">',DATE_FORMAT(data_apresentacao,'%H:%i'),'</p><BR> (',id,') ',ua,' <BR> <i>', nome,'</i> <BR><b>',titulo,'</b>','<BR><a href=\"',link_apresentacao,'\" target=\"_blank\">APRESENTAÇÃO</a>' ORDER BY ua,data_apresentacao,id SEPARATOR '<br><br>') FROM editalProjeto 
        WHERE situacao=1 and valendo=1 and 
        tipo=""" + edital + """ GROUP BY local_apresentacao,
        date(data_apresentacao) 
        ORDER BY local_apresentacao,date(data_apresentacao) """
        '''
        consulta = """SELECT local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y'),count(editalProjeto.id),
        GROUP_CONCAT('<p style=\"background-color: #FCFF33;\">',DATE_FORMAT(data_apresentacao,'%H:%i'),'</p><BR> (',editalProjeto.id,') ',ua,' <BR> <i>', nome,'</i> <BR><b>',titulo,'</b>','<BR><a href=\"',link_apresentacao,'\" target=\"_blank\">APRESENTAÇÃO</a>' ORDER BY ua,data_apresentacao,editalProjeto.id SEPARATOR '<br><br>'), sala_link.link,
        (SELECT GROUP_CONCAT(users.nome SEPARATOR ', ') FROM usuarios_salas,users WHERE users.username=usuarios_salas.username and usuarios_salas.edital=""" + edital + """ and usuarios_salas.sala=local_apresentacao and usuarios_salas.data=DATE(data_apresentacao)) as avaliadores FROM editalProjeto,sala_link
        WHERE situacao=1 and valendo=1 and sala_link.sala=local_apresentacao and sala_link.edital=tipo and
        tipo=""" + edital + """ GROUP BY local_apresentacao,
        date(data_apresentacao) 
        ORDER BY local_apresentacao,date(data_apresentacao)"""
        linhas,total = executarSelect(consulta)
        return(render_template('mapa.html',linhas=linhas,nome_edital=nome_edital))
    else:
        return("OK")

@app.route("/enviarVersaoFinal/<id_trabalho>", methods=['GET', 'POST'])
def enviarVersaoFinal(id_trabalho):
    
    idTrabalho = id_trabalho
    titulo = obterColunaUnica('editalProjeto','titulo','id',idTrabalho)
    edital = obterColunaUnica('editalProjeto','tipo','id',idTrabalho)
    deadline = obterColunaUnica('editais','DATE(deadline_versao_final)','id',edital)
    agora = datetime.datetime.now()
    agora = agora.strftime("%Y-%m-%d")
    if (agora>deadline):
        flash("Prazo expirado!")
        return(redirect(url_for('meusProjetos')))
    
    if autenticado():
        consulta = "SELECT id FROM editalProjeto WHERE id=" + idTrabalho + " AND siape='" + str(session['username']) + "'"
        linhas,total = executarSelect(consulta)
        if total>0:
            return(render_template('versaoFinal.html',idTrabalho=idTrabalho,titulo=titulo))
        else:
            flash("Acesso negado!")
            return(redirect(url_for('meusProjetos')))
    else:
        flash("Acesso negado!")
        return(redirect(url_for('meusProjetos')))
        

@app.route("/enviarApresentacao/<id_trabalho>", methods=['GET'])
def enviarApresentacao(id_trabalho):
    
    idTrabalho = id_trabalho
    titulo = obterColunaUnica('editalProjeto','titulo','id',idTrabalho)
    if autenticado():
        consulta = "SELECT id FROM editalProjeto WHERE id=" + idTrabalho + " AND siape='" + str(session['username']) + "'"
        linhas,total = executarSelect(consulta)
        if total>0:
            edital = obterColunaUnica('editalProjeto','tipo','id',idTrabalho)
            deadline = obterColunaUnica('editais','DATE(deadline_apresentacao)','id',edital)
            agora = datetime.datetime.now()
            agora = agora.strftime("%Y-%m-%d")
            if (agora>deadline):
                flash("Prazo para envio expirado!")
                return(redirect(url_for('meusProjetos')))
            return(render_template('enviarApresentacao.html',idTrabalho=idTrabalho,titulo=titulo))
        else:
            flash("Acesso negado. Voce nao tem permissao.")
            return(redirect(url_for('meusProjetos')))
    else:
        flash("Acesso negado")
        return(redirect(url_for('meusProjetos')))
    

@app.route("/uploadCR", methods=['GET', 'POST'])
def uploadCR():
    if request.method == "POST":
        idTrabalho = str(request.form['idTrabalho'])
        nomeDoArquivoTrabalho = ""
        if 'arquivo_trabalho' in request.files:
            token = id_generator()
            nomeDoArquivoTrabalho = "FINAL" + "." + token + ".pdf"
            filename = anexos.save(request.files['arquivo_trabalho'],name=nomeDoArquivoTrabalho)
            consulta = """UPDATE editalProjeto SET arquivo_projeto_final='""" + nomeDoArquivoTrabalho + """' WHERE id=""" + idTrabalho
            atualizar(consulta)
            return(redirect(url_for('meusProjetos')))
    else:
        return("OK")

@app.route("/cadastrarLinkApresentacao", methods=['GET', 'POST'])
def cadastrarLinkApresentacao():
    if request.method == "POST":
        idTrabalho = str(request.form['idTrabalho'])
        edital = obterColunaUnica('editalProjeto','tipo','id',idTrabalho)
        deadline = obterColunaUnica('editais','DATE(deadline_apresentacao)','id',edital)
        agora = datetime.datetime.now()
        agora = agora.strftime("%Y-%m-%d")
        if (agora>deadline):
            return("Prazo expirado!")
        if 'link' in request.form:
            link = str(request.form['link'])
            consulta = """UPDATE editalProjeto SET link_apresentacao='""" + link + """' WHERE id=""" + idTrabalho
            atualizar(consulta)
            return(redirect(url_for('meusProjetos')))
    else:
        return("OK")

@app.route("/premiacao", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def premiacao():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND situacao=1 AND modalidade=2 AND tipo=""" + edital
            principal,total = executarSelect(consulta_principal)
            for linha in principal:
                id = str(linha[0])
                consulta_interna = """SELECT AVG(c1+c2+c3+c4+c5+c6+c7+c8+c9) as soma FROM (SELECT * FROM avaliacoes where idProjeto=""" + id + """  AND finalizado=1 ORDER BY data_avaliacao LIMIT 3) av"""
                auxiliar,totalAuxiliar = executarSelect(consulta_interna,1)
                media = str(auxiliar[0])
                consulta_update = "UPDATE editalProjeto SET media1=" + media + " WHERE id=" + id
                atualizar(consulta_update)

            #VERIFICANDO QUEM CONCORRE A PREMIAÇÃO - todos trabalhos completos
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND ua='Ciências da Vida' AND situacao=1 AND modalidade=2 and categoria=0 AND tipo=""" + edital + """ ORDER BY media1 DESC"""
            principal,total = executarSelect(consulta_principal)
            for linha in principal:
                id = str(linha[0])
                consulta_update = "UPDATE editalProjeto SET premiacao=1 WHERE id=" + id
                atualizar(consulta_update)

            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND ua='Humanidades' AND situacao=1 AND modalidade=2 and categoria=0 AND tipo=""" + edital + """ ORDER BY media1 DESC"""
            principal,total = executarSelect(consulta_principal)
            for linha in principal:
                id = str(linha[0])
                consulta_update = "UPDATE editalProjeto SET premiacao=1 WHERE id=" + id
                atualizar(consulta_update)

            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND ua='Ciências Exatas, Tecnológicas e Multidisciplinar' AND situacao=1 AND modalidade=2 and categoria=0 AND tipo=""" + edital + """ ORDER BY media1 DESC"""
            principal,total = executarSelect(consulta_principal)
            for linha in principal:
                id = str(linha[0])
                consulta_update = "UPDATE editalProjeto SET premiacao=1 WHERE id=" + id
                atualizar(consulta_update)
            flash(u"Médias calculadas com sucesso!")
            return(redirect(url_for('admin',edital=edital)))
        else:
            return("OK")
    else:
        return("OK")

def getLinkSala(edital,sala):
    consulta = """SELECT link FROM sala_link WHERE edital=""" + edital + """ AND sala='""" + sala + """'"""
    linhas,total = executarSelect(consulta)
    for linha in linhas:
        return(str(linha[0]))
    
@app.route("/apresentacoes", methods=['GET', 'POST'])
@auth.login_required(role=['admin','avaliador','monitor'])
def apresentacoes():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args and 'sala' in request.args and 'data' in request.args:
            
            edital = str(request.args.get('edital'))
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            sala = str(request.args.get('sala'))
            data = str(request.args.get('data'))
            session['sala'] = sala
            session['data'] = data
            session['edital'] = edital
            data_formatada = data
            if (not avaliadorTemPermissao(edital,data,sala))and('admin' not in session['roles'])and('monitor' not in session['roles']):
                return("Acesso negado.")
            try:
                data_formatada = datetime.datetime.strptime(data,'%Y-%m-%d').strftime('%d/%m/%Y')
            except:
                data_formatada = data
            
            if (sala!='POSTER'): #APRESENTAÇÃO ORAL
                consulta = """SELECT id,nome,titulo,DATE_FORMAT(editalProjeto.data_apresentacao,'%d/%m/%Y - %T') as data,apresentou,arquivo_projeto_final,ua,link_apresentacao FROM editalProjeto WHERE local_apresentacao='""" + sala + """' AND tipo=""" + edital + """ and valendo=1 and situacao=1 and DATE(data_apresentacao)='""" + data + """' ORDER BY ua,data_apresentacao"""                
                linhas,total = executarSelect(consulta)
                link = getLinkSala(edital,sala)
                return(render_template('apresentacoes.html',linhas=linhas,total=total,nome_edital=nome_edital,sala=sala,data=data_formatada,link=link,roles=session['roles']))
            else: #POSTER
                if 'ua' in request.args:
                    ua = int(request.args.get('ua'))
                    if ua==1:
                        consulta = """SELECT id,nome,titulo,DATE_FORMAT(data_apresentacao,'%d/%m/%Y - %T') as data,apresentou,arquivo_projeto_final,ua,link_apresentacao FROM editalProjeto WHERE ua='Ciências da Vida' AND situacao=1 AND categoria=1 AND tipo=""" + edital + """ and valendo=1 ORDER BY ua,local_apresentacao,data_apresentacao"""
                    elif ua==2:
                        consulta = """SELECT id,nome,titulo,DATE_FORMAT(data_apresentacao,'%d/%m/%Y - %T') as data,apresentou,arquivo_projeto_final,ua,link_apresentacao FROM editalProjeto WHERE ua='Humanidades' AND situacao=1 AND categoria=1 AND tipo=""" + edital + """ and valendo=1 ORDER BY ua,local_apresentacao,data_apresentacao"""
                    else:
                        consulta = """SELECT id,nome,titulo,DATE_FORMAT(data_apresentacao,'%d/%m/%Y - %T') as data,apresentou,arquivo_projeto_final,ua,link_apresentacao FROM editalProjeto WHERE ua='Ciências Exatas, Tecnológicas e Multidisciplinar' AND situacao=1 AND categoria=1 AND tipo=""" + edital + """ and valendo=1 ORDER BY ua,local_apresentacao,data_apresentacao"""
                else:
                    consulta = """SELECT id,nome,titulo,DATE_FORMAT(data_apresentacao,'%d/%m/%Y - %T') as data,apresentou,arquivo_projeto_final,ua,link_apresentacao FROM editalProjeto WHERE situacao=1 AND categoria=1 AND tipo=""" + edital + """ and valendo=1 ORDER BY ua,local_apresentacao,data_apresentacao"""
                linhas,total = executarSelect(consulta)
                
                return(render_template('apresentacoes.html',linhas=linhas,total=total,nome_edital=nome_edital,sala=sala,data=data_formatada,roles=session['roles']))
        else:
            return("OK")
    else:
        return ("OK")

@app.route("/solicitarVersaoFinal/<edital>", methods=['GET', 'POST'])
def solicitarVersaoFinal(edital):
    """
    SOLICITA A VERSÃO FINAL PARA OS APRESENTADORES
    """
    consulta = """SELECT editalProjeto.email,titulo,editalProjeto.id,siape,editalProjeto.email,
    users.password,arquivo_projeto_final,editalProjeto.nome FROM editalProjeto,users 
    WHERE editalProjeto.siape=users.username and situacao=1 and 
    valendo=1 and arquivo_projeto_final='0' and tipo=""" + edital
    nome_edital = obterColunaUnica('editais','nome','id',edital)
    linhas,total=executarSelect(consulta)            
    cont = 0
    erros = 0
    for linha in linhas:
        titulo = str(linha[1])
        id_trabalho = str(linha[2])
        cpf = str(linha[3])
        email_autor = str(linha[4])
        senha = str(linha[5])
        arquivo = str(linha[6])
        autores = str(linha[7])
        if (arquivo=="0"):
            texto_email = render_template('email_versao_final.html',evento=nome_edital,id=id_trabalho,titulo=titulo,cpf=cpf,email=email_autor,senha=senha,autores=autores)
            msg = Message(subject = nome_edital + u"- SOLICITAÇÃO DE VERSÃO FINAL",bcc=[str(linha[0])],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
            try:
                if PRODUCAO==1:
                    t = threading.Thread(target=enviar_email,args=(msg,))
                    t.start()
                    #mail.send(msg)
                cont = cont + 1
            except:
                erros = erros + 1
    flash("Solicitações enviadas com sucesso!")
    return(redirect(url_for('admin',edital=edital)))


def getAvaliadoresSala(edital,sala,dia):
    consulta = """SELECT users.nome FROM users,usuarios_salas 
    WHERE users.username=usuarios_salas.username and 
    usuarios_salas.edital=""" + edital + """ and 
    usuarios_salas.sala='""" + sala + """' and 
    usuarios_salas.data='""" + dia + """'"""
    linhas,total = executarSelect(consulta)
    avaliadores = []
    for linha in linhas:
        avaliadores.append(str(linha[0]))
    return (avaliadores)

@app.route("/emailInformacoes", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def emailInformacoes():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            consulta = """SELECT email,titulo,id,
            nome,local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),DATE(data_apresentacao) FROM editalProjeto 
            WHERE situacao=1 and valendo=1 and tipo=""" + edital
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            linhas,total=executarSelect(consulta)            
            cont = 0
            erros = 0
            for linha in linhas:
                titulo = str(linha[1])
                id_trabalho = str(linha[2])
                email_autor = str(linha[0])
                autores = str(linha[3])
                local = str(linha[4])
                data = str(linha[5])
                link = getLinkSala(edital,local)
                avaliadores = getAvaliadoresSala(edital,local,str(linha[6]))
                jaMandouOlink = obterColunaUnica('editalProjeto','link_apresentacao','id',edital)
                jaMandouVersaoFinal = obterColunaUnica('editalProjeto','arquivo_projeto_final','id',edital)
                if (jaMandouVersaoFinal=='0') or (jaMandouOlink=='0'):    
                    texto_email = render_template('email_data_local.html',evento=nome_edital,id=id_trabalho,titulo=titulo,email=email_autor,autores=autores,local=local,data=data,avaliadores=avaliadores,link=link,jaMandouOlink=jaMandouOlink,jaMandouVersaoFinal=jaMandouVersaoFinal)
                    msg = Message(subject = nome_edital + u"- INFORMAÇÕES SOBRE A APRESENTAÇÃO",bcc=[email_autor],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
                    #msg = Message(subject = nome_edital + u"- INFORMAÇÕES SOBRE A APRESENTAÇÃO",bcc=["rafael.mota@ufca.edu.br"],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
                    try:
                        if PRODUCAO==1:
                            mail.send(msg)
                        cont = cont + 1
                    except:
                        erros = erros + 1
                    #break
            return(str(cont) + " e-mails enviados com sucesso." + str(erros) + " erro(s).")
        else:
            return("OK")
    else:
        return("OK")

@app.route("/emailInstrucoes/<edital>", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def emailInstrucoes(edital):
    """
    ENVIO DAS INSTRUÇÕES PARA ENVIO DAS APRESENTAÇÕES
    """
    consulta = """SELECT editalProjeto.email,titulo,editalProjeto.id,siape,editalProjeto.nome,
    users.password,IF(categoria=0,'APRESENTACAO ORAL','POSTER'),DATE_FORMAT(data_apresentacao,'%d/%m/%Y - %H:%i'),local_apresentacao,DATE(data_apresentacao) FROM editalProjeto,users 
    WHERE editalProjeto.siape=users.username and situacao=1 and 
    valendo=1 and tipo=""" + edital
    nome_edital = obterColunaUnica('editais','nome','id',edital)
    prazo_apresentacao = obterColunaUnica('editais','DATE(deadline_apresentacao)','id',edital)
    prazo_apresentacao = datetime.datetime.strptime(prazo_apresentacao,'%Y-%m-%d').strftime('%d/%m/%Y')
    nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
    linhas,total=executarSelect(consulta)            
    cont = 0
    erros = 0
    for linha in linhas:
        titulo = str(linha[1])
        id_trabalho = str(linha[2])
        email_autor = str(linha[0])
        autores = str(linha[4])
        cpf = str(linha[3])
        senha = str(linha[5])
        apresentacao = str(linha[6])
        dataHora_apresentacao = str(linha[7])
        local_apresentacao = str(linha[8])
        data_apresentacao = str(linha[9])
        link = getLinkSala(edital,local_apresentacao)
        texto_email = render_template('email_instrucoes.html',evento=nome_edital,id=id_trabalho,titulo=titulo,email=email_autor,autores=autores,cpf=cpf,senha=senha,nome_longo=nome_longo,apresentacao=apresentacao,prazo_apresentacao=prazo_apresentacao,data_apresentacao=dataHora_apresentacao,local_apresentacao=local_apresentacao,link=link)
        msg = Message(subject = nome_edital + u"- ORIENTAÇÕES SOBRE A APRESENTAÇÃO",bcc=[email_autor],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
        
        try:
            if PRODUCAO==1:
                t = threading.Thread(target=enviar_email,args=(msg,))
                t.start()
                #mail.send(msg)
            cont = cont + 1
        except:
            erros = erros + 1
        
    flash("Instruções enviadas com sucesso!")
    return(redirect(url_for('admin',edital=edital)))


@app.route("/emailPosEvento", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def emailPosEvento():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            consulta = """(SELECT DISTINCT users.email FROM users,editalProjeto WHERE users.username=editalProjeto.siape and 
            editalProjeto.tipo=""" + edital + """) UNION (SELECT DISTINCT users.email FROM users,usuarios_salas WHERE users.username=usuarios_salas.username and 
            usuarios_salas.edital=""" +edital + """)"""
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
            linhas,total=executarSelect(consulta)            
            for linha in linhas:
                email_autor = str(linha[0])
                texto_email = render_template('email_pos_evento.html',evento=nome_edital,nome_longo=nome_longo)
                subject = "AGRADECIMENTOS"
                msg = Message(subject = subject,bcc=[email_autor],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
                #msg = Message(subject = subject,bcc=["rafael.mota@ufca.edu.br"],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
                try:
                    if PRODUCAO==1:
                        mail.send(msg)
                except:
                    logging.error('Erro no /emailPosEvento') 
                     
            return("E-mails enviados...")
        else:
            return("OK")
    else:
        return("OK")


@app.route("/emailInstrucoesAvaliador/<edital>", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def emailInstrucoesAvaliador(edital):
    """
    Envia os e-mails (todos) com as instruções para os moderadores de sessões
    """
    consulta = """SELECT DISTINCT usuarios_salas.username,users.password,users.email FROM users,usuarios_salas 
    WHERE usuarios_salas.edital=""" + edital + """ 
    and users.username=usuarios_salas.username ORDER BY usuarios_salas.username"""
    nome_edital = obterColunaUnica('editais','nome','id',edital)
    nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
    linhas,total=executarSelect(consulta)            
    cont = 0
    erros = 0
    for linha in linhas:
        cpf = str(linha[0])
        senha = str(linha[1])
        email_avaliador = str(linha[2])
        texto_email = render_template('email_instrucoes_avaliador.html',evento=nome_edital,nome_longo=nome_longo,cpf=cpf,senha=senha,edital=edital)
        msg = Message(subject = nome_edital + u"- ORIENTAÇÕES SOBRE A APRESENTAÇÃO",bcc=[email_avaliador],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
        try:
            if PRODUCAO==1:
                t = threading.Thread(target=enviar_email,args=(msg,))
                t.start()
                #mail.send(msg)
            cont = cont + 1
        except:
            erros = erros + 1
        #break
    return(str(cont) + " e-mails enviados com sucesso." + str(erros) + " erro(s).")
        

def getDatas(edital):
    consulta = """SELECT DISTINCT (DATE(data_apresentacao)) FROM editalProjeto WHERE categoria=0 and situacao=1 and tipo=""" + edital + """ ORDER BY data_apresentacao"""
    linhas,total = executarSelect(consulta)
    datas = []
    for linha in linhas:
        datas.append(str(linha[0]))
    return (datas)

def getSalas(edital):
    consulta = """SELECT DISTINCT (local_apresentacao) FROM editalProjeto WHERE categoria=0 and situacao=1 and tipo=""" + edital + """ ORDER BY local_apresentacao"""
    linhas,total = executarSelect(consulta)
    salas = []
    for linha in linhas:
        salas.append(str(linha[0]))
    return (salas)

def getSalasPorData(edital,data):
    consulta = """SELECT DISTINCT (local_apresentacao) FROM editalProjeto WHERE tipo=""" + edital + """ 
     and categoria=0 and situacao=1 and DATE(data_apresentacao)='""" + data + """' ORDER BY local_apresentacao"""
    linhas,total = executarSelect(consulta)
    salas = []
    for linha in linhas:
        salas.append(str(linha[0]))
    return (salas)

def getMapaApresentacoes(edital):
    datas = getDatas(edital)
    mapa = []
    for data in datas:
        mapa.append([data,getSalasPorData(edital,data)])
    resultado = []
    dias = []
    salas = []
    for linha in mapa:
        for sala in linha[1]:
            dias.append(linha[0])
            salas.append(sala)
            resultado.append('&data=' + linha[0] + "&sala=" + sala)
    
    return (dias,salas)


@app.route("/organizacao", methods=['GET', 'POST'])
@auth.login_required(role=['admin','monitor'])
def organizacao():
    if request.method == "GET":
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            dias,salas = getMapaApresentacoes(edital)
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            return(render_template('organizacao.html',linhas=zip(dias,salas),nome_edital=nome_edital, root = CPPGI_SITE,edital=edital))
        else:
            return("OK")
    else:
        return ("OK")

@app.route("/admin", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def root():
    titulo = u"PÁGINA ADMINISTRATIVA"
    consulta = """
    SELECT id,nome_longo,deadline,deadline_avaliacao,nome_curto,deadline_apresentacao,deadline_versao_final,
    isbn,situacao,certificado_apresentador,certificado_moderador,certificado_participante,certificado_demais,certificado_convidado,
    declaracao_avaliador,periodo,local  
    FROM editais
    """
    linhas,total = executarSelect(consulta)
    return(render_template('index.html',titulo=titulo,root=CPPGI_SITE,linhas=linhas))

@app.route("/admin/<edital>", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def admin(edital):
    nome_edital = obterColunaUnica('editais','nome','id',edital)
    deadline_avaliacao = obterColunaUnica('editais','deadline_avaliacao','id',edital)
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if agora>deadline_avaliacao:
        mostrar_pos_avaliacao = True
    else:
        mostrar_pos_avaliacao = False
    
    titulo = u"PÁGINA ADMINISTRATIVA"
    return(render_template('admin.html',edital=edital,titulo=titulo,nome_edital=nome_edital,root=CPPGI_SITE,mostrar_pos_avaliacao=mostrar_pos_avaliacao))

@app.route("/mapaavaliadores", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def mapaavaliadores():
    if request.method == "GET":
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            nome_edital = obterColunaUnica('editais','nome','id',edital)
            titulo = u"AVALIADORES"
            consulta = """SELECT users.nome,DATE_FORMAT(usuarios_salas.data,'%d/%m/%Y'),usuarios_salas.sala,usuarios_salas.area,sala_link.link FROM users,usuarios_salas,sala_link 
            WHERE usuarios_salas.edital=""" + edital + """ and users.username=usuarios_salas.username and sala_link.sala=usuarios_salas.sala and sala_link.edital=usuarios_salas.edital ORDER by usuarios_salas.data,usuarios_salas.sala"""
            linhas,total = executarSelect(consulta)
            return(render_template('mapa_avaliadores.html',edital=edital,titulo=titulo,nome_edital=nome_edital,root=CPPGI_SITE,linhas=linhas))
        else:
            return ("OK")
    else:
        return("OK")

@app.route("/gerarCertificadoAvaliador", methods=['GET'])
@auth.login_required(role=['avaliador'])
def gerarCertificadoAvaliador():
    """
    Emite o certificado do moderador de sessões
    """
    template = obterColunaUnica('editais','certificado_moderador','id',session['edital'])
    nome = session['nome']
    token = "hskaOPia"
    periodo = obterColunaUnica('editais','periodo','id',session['edital'])
    evento = obterColunaUnica('editais','nome_longo','id',session['edital'])
    local = obterColunaUnica('editais','local','id',session['edital'])
    arquivoCertificado = app.config['CERTIFICADOS_FOLDER'] + 'certificado.pdf'
    options = {
        'page-size': 'A4',
        'orientation': 'landscape',
        'margin-top': '0cm',
        'margin-right': '0cm',
        'margin-bottom': '0cm',
        'margin-left': '0cm',
    }
    #Gerando QrCode
    qrcode_url = url_for('autenticar_certificado',tipo=1,codigo=token,id_projeto=0,_external=True)
    qrcode = pyqrcode.create(qrcode_url)
    qrcode.png(CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png',scale=3)
    qr_code = get_image_file_as_base64_data(CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png')

    #Recuperando template
    background = get_image_file_as_base64_data(CERTIFICADOS_TEMPLATE_DIR + template)
    
    #Gerando certificado em PDF
    try:
        pdfkit.from_string(render_template('certificado_moderador.html',nome=nome,periodo=periodo,evento=evento,identificador=0,local=local,arquivo=template,background=background,qrcode=qr_code,token=token,tipo=1,data="Juazeiro do Norte, " + getData()),arquivoCertificado,options=options)
    except Exception as e:
        app.logger.error('Erro gerando certificado apresentador')
    finally:
        consulta = """
        SELECT id,username FROM usuarios_salas WHERE username='%s' AND edital=%s AND compareceu=1
        """ %(session['username'],session['edital'])
        linhas,total = executarSelect(consulta)
        if total>0:
            return send_from_directory(app.config['CERTIFICADOS_FOLDER'], 'certificado.pdf')
        else:
            flash("Nenhuma avaliação foi realizada até o momento!")
            return(redirect(url_for('avaliador',edital=session['edital'])))

def gerarCertificadoComplexo(name, template, font_path,posicao, output_png, output_pdf,tamanho,titulo="TITULO",tamanho2=30):
   
    text_y_position = posicao

    # opens the image
    img = Image.open(template, mode ='r')
        
    # gets the image width
    image_width = img.width
        
    # gets the image height
    image_height = img.height 

    # creates a drawing canvas overlay 
    # on top of the image
    draw = ImageDraw.Draw(img)

    # gets the font object from the 
    # font file (TTF)
    font = ImageFont.truetype(
        font_path,
        tamanho # change this according to your needs
    )

    # fetches the text width for 
    # calculations later on
    text_width, _ = draw.textsize(name, font = font)

    draw.multiline_text(
        (
            # this calculation is done 
            # to centre the image
            (image_width - text_width) / 2,
            text_y_position
        ),
        name,
        font = font,fill=(0,0,0)        )
    
    font = ImageFont.truetype(
        font_path,
        tamanho2 # change this according to your needs
    )
    draw.multiline_text(
        (
            # this calculation is done 
            # to centre the image
            (image_width - text_width) / 2,
            text_y_position+300
        ),
        titulo,
        font = font,fill=(0,0,0)        )

    # saves the image in png format
    img.save(output_png)
    image1 = Image.open(output_png)
    im1 = image1.convert('RGB')
    im1.save(output_pdf)


@app.route("/baixarCertificado/<id_projeto>", methods=['GET'])
@auth.login_required(role=['user','admin'])
def baixarCertificado(id_projeto):
    """
    Emite o CERTIFICADO DE APRESENTADOR
    """
    id = id_projeto
    apresentou = obterColunaUnica('editalProjeto','apresentou','id',id)
    consulta = """SELECT id FROM editalProjeto WHERE siape='""" + session['username'] +"""'"""
    linhas,total = executarSelect(consulta)
    if (total==0)and('admin' not in session['roles']):
        return ("Acesso não permitido.")
    if (apresentou=='0')and('admin' not in session['roles']):
        return("Trabalho não apresentado.")
    consulta = """SELECT nome,titulo,tipo FROM editalProjeto where id=""" + id
    linhas,total = executarSelect(consulta)
    nome = "INDEFINIDO"
    titulo = "INDEFINIDO"
    for linha in linhas:
        edital = str(linha[2])
        template = obterColunaUnica('editais','certificado_apresentador','id',edital)
        nome = str(linha[0])
        titulo = str(linha[1])
        evento = obterColunaUnica('editais','nome_longo','id',edital)
        periodo = obterColunaUnica('editais','periodo','id',edital)
        local = obterColunaUnica('editais','local','id',edital)
        verbo = "apresentou"
        if ',' in nome:
            verbo = "apresentaram"
        arquivoCertificado = app.config['CERTIFICADOS_FOLDER'] + 'certificado.pdf'
        options = {
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0cm',
            'margin-right': '0cm',
            'margin-bottom': '0cm',
            'margin-left': '0cm',
        }
        
        token = obterColunaUnica('editalProjeto','token','id',id_projeto)
        if token=='0':
            token = id_generator()
            consulta = """
            UPDATE editalProjeto SET token='%s' 
            WHERE id=%s
            """ %(token,id_projeto)
            atualizar(consulta)

        #Gerando QrCode
        qrcode_url = url_for('autenticar_certificado',tipo=0,codigo=token,id_projeto=id_projeto,_external=True)
        qrcode = pyqrcode.create(qrcode_url)
        qrcode.png(CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png',scale=3)
        qr_code = get_image_file_as_base64_data(CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png')

        #Recuperando template
        background = get_image_file_as_base64_data(CERTIFICADOS_TEMPLATE_DIR + template)
        
        #Gerando certificado em PDF
        try:
            app.logger.error(CERTIFICADOS_TEMPLATE_DIR + template)
            pdfkit.from_string(render_template('certificado_apresentador.html',nome=nome,titulo=titulo,periodo=periodo,evento=evento,identificador=id,local=local,arquivo=template,verbo=verbo,background=background,qrcode=qr_code,token=token,tipo=0,data="Juazeiro do Norte, " + getData()),arquivoCertificado,options=options)
        except Exception as e:
            app.logger.error('Erro gerando certificado apresentador')
        finally:
            return send_from_directory(app.config['CERTIFICADOS_FOLDER'], 'certificado.pdf')

@app.route("/demaisCertificados", methods=['GET', 'POST'])
def demaisCertificados():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            consulta = """SELECT nome,tipo,id FROM certificados_moderador WHERE edital=""" + edital + """ ORDER BY nome"""
            linhas,total = executarSelect(consulta)
            return(render_template('certificados_moderador.html',linhas=linhas))
        else:
            return("OK")
    else:
        return("OK")

@app.route("/baixarCertificadoIndividual", methods=['GET', 'POST'])
def certificadoIndividual():
    if request.method == "GET":
        #Recuperando o id do certificado
        if 'id' in request.args:
            id = str(request.args.get('id'))
            consulta = """SELECT nome,tipo,edital FROM certificados_moderador WHERE id=""" + id
            linhas,total = executarSelect(consulta)
            for linha in linhas:
                nome = linha[0]
                tipo_participacao = str(linha[1])
                template = obterColunaUnica('editais','certificado_demais','id',str(linha[2]))
                output_png = CERTIFICADOS_TEMP_DIR + 'certificado.png'
                output_pdf = CERTIFICADOS_TEMP_DIR + 'certificado.pdf'
                template = CERTIFICADOS_TEMPLATE_DIR + template
                font = ImageFont.truetype(FONT_PATH,40)
                wrapper = TextWrapper(tipo_participacao, font, 1250)
                tipo_participacao = wrapper.wrapped_text()
                gerarCertificadoComplexo(nome,template,FONT_PATH,550,output_png,output_pdf,40,tipo_participacao,30)
                return (send_from_directory(CERTIFICADOS_TEMP_DIR, 'certificado.pdf'))
        else:
            return("OK")
    else:
        return("OK")

@app.route("/confirmar", methods=['GET', 'POST'])
@auth.login_required(role=['avaliador','admin'])
def confirmar():

    if request.method == "GET":
        if 'id' in request.args:
            id = str(request.args.get('id'))
            titulo = obterColunaUnica('editalProjeto','titulo','id',id)
            arquivo = obterColunaUnica('editalProjeto','arquivo_projeto','id',id)
            final = obterColunaUnica('editalProjeto','arquivo_projeto_final','id',id)
            return(render_template('avaliacao_orais.html',titulo=titulo,arquivo=arquivo,final=final,id=id))
        else:
            return("ERRO")
    elif request.method == "POST":
        c1 = int(request.form['c1'])
        c2 = int(request.form['c2'])
        c3 = int(request.form['c3'])
        c4 = int(request.form['c4'])
        c = """SELECT nome FROM users WHERE username='""" + session['username'] + """'"""
        linhas,total = executarSelect(c)
        avaliador = "INDEFINIDO"
        for linha in linhas:
            avaliador = str(linha[0])
        
        comentarios = str(request.form['txtComentarios'])
        id = str(request.form['idProjeto'])
        local = obterColunaUnica('editalProjeto','local_apresentacao','id',id)
        edital = obterColunaUnica('editalProjeto','tipo','id',id)
        consulta = "UPDATE editalProjeto SET apresentou=1 WHERE id=" + id
        atualizar(consulta)
        consulta = """INSERT INTO avaliacoes_orais (idProjeto,c1,c2,c3,c4,comentarios,avaliador) VALUES (%s,%s,%s,%s,%s,%s,%s) """
        valores = (int(id),c1,c2,c3,c4,comentarios,avaliador)
        inserir(consulta,valores)
        consulta = """
        UPDATE usuarios_salas SET compareceu=1 
        WHERE username='%s' AND edital=%s AND sala='%s' AND data='%s'
        """ %(session['username'],edital,session['sala'],session['data'])
        atualizar(consulta)
        return(redirect('/cppgi/apresentacoes?edital=' + session['edital'] + '&sala=' + session['sala'] + '&data='+session['data']))
    else:
        return("ERRO")

@app.route("/notasApresentacoes", methods=['BGET', 'POST'])
def notasApresentacoes():
    if request.method == "GET":
        #Recuperando o edital
        if 'edital' in request.args:
            edital = str(request.args.get('edital'))
            consulta_principal = """SELECT id FROM editalProjeto WHERE valendo=1 AND situacao=1 AND premiacao=1 AND tipo=""" + edital
            principal,total = executarSelect(consulta_principal)
            for linha in principal:
                id = str(linha[0])
                consulta_interna = """SELECT AVG(c1+c2+c3+c4) as soma FROM (SELECT * FROM avaliacoes_orais where idProjeto=""" + id + """  ORDER BY data LIMIT 2) av"""
                auxiliar,totalAuxiliar = executarSelect(consulta_interna,1)
                media = str(auxiliar[0])
                consulta_update = "UPDATE editalProjeto SET media2=" + media + " WHERE id=" + id
                atualizar(consulta_update)

            return("Medias calculadas com sucesso!")
        else:
            return("OK")
    else:
        return("OK")


def updateZip(zipname, filename, data):
    # generate a temp file
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
    os.close(tmpfd)

    # create a temp copy of the archive without filename
    with zipfile.ZipFile(zipname, 'r') as zin:
        with zipfile.ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    # replace with the temp archive
    os.remove(zipname)
    os.rename(tmpname, zipname)

    # now add filename with its new data
    with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        dados = data.encode('utf8')
        zf.writestr(filename, dados)

def gerarCertificadoApresentacao(autores,titulo,id,token=0):
    namef = app.config['CERTIFICADOS_FOLDER'] + 'certificado-' + id + '.odt'
    odt = newdoc(doctype='odt', filename=namef, template='/home/perazzo/cppgi/documentos/07-certificado.apresentacao.odt')
    odt.save()
    a = zipfile.ZipFile('/home/perazzo/cppgi/documentos/07-certificado.apresentacao.odt')
    content = a.read('content.xml')
    content = str(content.decode(encoding='utf8'))
    content = unicode.replace(content,"[AUTORES]", autores)
    content = unicode.replace(content, '[TITULO]', titulo)
    content = unicode.replace(content, '[CODIGO]', token)
    updateZip(namef, app.config['DOCUMENTS_FOLDER'] + 'content.xml', content)
    #odt2Pdf()

@app.route("/certificadoApresentacao", methods=['GET', 'POST'])
def certificadoApresentacoes():
    if request.method == "GET":
        #Recuperando o edital
        if 'id' in request.args:
            id = str(request.args.get('id'))
            consulta = """SELECT nome,titulo,id,token FROM editalProjeto WHERE valendo=1 AND situacao=1 AND apresentou=1 AND tipo=""" + id
            linhas,total = executarSelect(consulta)
            for linha in linhas:
                nome = str(linha[0])
                titulo = str(linha[1])
                idTrabalho = str(linha[2])
                token = str(linha[3])
                gerarCertificadoApresentacao(nome,titulo,idTrabalho,token)
            return("Certificados gerados com sucesso!")
        else:
            return("OK")
    else:
        return("OK")

@app.route("/enviarCertificados/<edital>", methods=['GET', 'POST'])
def enviarCertificados(edital):
    id = edital
    consulta = """SELECT nome,titulo,email,id FROM editalProjeto WHERE valendo=1 AND situacao=1 AND apresentou=1 AND tipo=""" + id
    linhas,total = executarSelect(consulta)
    for linha in linhas:
        email = str(linha[2])
        idTrabalho = str(linha[3])
        nome = str(linha[0])
        titulo = str(linha[1])
        nome_curto = obterColunaUnica('editais','nome_curto','id',str(id))
        nome_longo = obterColunaUnica('editais','nome_longo','id',str(id))
        link = url_for('baixarCertificado',id_projeto=idTrabalho)
        texto_email = render_template('certificado_submissao.html',id_projeto=idTrabalho,proponente=nome,titulo_projeto=titulo,link=link,evento=nome_longo)
        msg = Message(reply_to="NAO-RESPONDA@ufca.edu.br",subject = u"Plataforma Yoko - [" + nome_curto + u"] CERTIFICADO DE APRESENTAÇÃO DE TRABALHO",recipients=[email],html=texto_email)
        t = threading.Thread(target=enviar_email,args=(msg,))
        t.start()
        #mail.send(msg)
    flash("Certificados ENVIADOS com sucesso!")
    return(redirect(url_for('admin',edital=edital)))
        


def gerarCertificadoModerador(nome,tipo,id,token=0):
    namef = app.config['CERTIFICADOS_FOLDER'] + 'MODERADOR-certificado-' + id + '.odt'
    odt = newdoc(doctype='odt', filename=namef, template='/home/perazzo/cppgi/documentos/07-certificado.moderador.odt')
    odt.save()
    a = zipfile.ZipFile('/home/perazzo/cppgi/documentos/07-certificado.moderador.odt')
    content = a.read('content.xml')
    content = str(content.decode(encoding='utf8'))
    content = unicode.replace(content,"[MODERADOR]", nome)
    content = unicode.replace(content, '[TIPO]', tipo)
    content = unicode.replace(content, '[CODIGO]', token)
    updateZip(namef, app.config['DOCUMENTS_FOLDER'] + 'content.xml', content)
    #odt2Pdf()

@app.route("/certificadoModerador", methods=['GET', 'POST'])
def certificadoModerador():
    if request.method == "GET":
        #Recuperando o edital
        if 'id' in request.args:
            id = str(request.args.get('id'))
            consulta = """SELECT nome,tipo,id,token FROM certificados_moderador ORDER BY nome"""
            linhas,total = executarSelect(consulta)
            for linha in linhas:
                nome = str(linha[0])
                tipo = str(linha[1])
                id = str(linha[2])
                token = str(linha[3])
                gerarCertificadoModerador(nome,tipo,id,token)
            return("Certificados gerados com sucesso!")
        else:
            return("OK")
    else:
        return("OK")

@app.route("/listarCertificados", methods=['GET', 'POST'])
def listarCertificados():
    consulta = """SELECT nome,id,tipo FROM certificados_moderador ORDER BY tipo,nome"""
    linhas,total = executarSelect(consulta)
    return(render_template('certificados_moderador.html',linhas=linhas))

@app.route("/baixarCertificadoModerador", methods=['GET', 'POST'])
def baixarCertificadoModerador():
    if request.method == "GET":
        if 'id' in request.args:
            id = str(request.args.get('id'))
            return (send_from_directory(app.config['CERTIFICADOS_FOLDER'], 'MODERADOR-certificado-' + id + '.pdf'))
        else:
            return("OK")
    else:
        return("OK")

'''
SELECT id,IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')),ua,nome,ua,arquivo_projeto_final FROM `editalProjeto`
WHERE valendo=1 AND situacao=1 and arquivo_projeto_final!='0' and tipo=7 ORDER BY ua,modalidade,id
'''
@app.route("/anais", methods=['GET', 'POST'])
def anais():
    if request.method == "GET":
        #Recuperando o edital
        if 'id' in request.args:
            id = str(request.args.get('id'))
            consulta = """SELECT id,IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')),ua,nome,arquivo_projeto_final FROM `editalProjeto`
            WHERE valendo=1 AND situacao=1 and arquivo_projeto_final!='0' and tipo=""" + id + """ ORDER BY ua,modalidade,id """
            linhas,total = executarSelect(consulta)
            conferencia = obterColunaUnica('editais','nome_longo','id',id)
            logo = obterColunaUnica('editais','logo','id',id)
            ficha = obterColunaUnica('editais','ficha','id',id)
            isbn = obterColunaUnica('editais','isbn','id',id)
            return(render_template('anais.html',linhas=linhas,total=total,conferencia=conferencia,logo=logo,ficha=ficha,isbn=isbn))
        else:
            return("OK")
    else:
        return("OK")

def gerarLinkAvaliacao():
    consulta = """SELECT id,idProjeto,token FROM avaliacoes 
    WHERE idProjeto in (SELECT id FROM editalProjeto WHERE valendo=1) ORDER BY id """
    linhas,total = executarSelect(consulta)
    for linha in linhas:
        id = str(linha[0])
        idProjeto = str(linha[1])
        token = str(linha[2])
        link = LINK_AVALIACAO + "?id=" + idProjeto + "&token=" + token
        consulta = "UPDATE avaliacoes SET link=\"" + link + "\"" + " WHERE id=" + id
        atualizar(consulta)

def enviar_email_avaliadores():
    gerarLinkAvaliacao()
    consulta = """
    SELECT e.id,e.titulo,e.resumo,a.avaliador,a.link,a.id,a.enviado,a.token,e.categoria,
    e.tipo, DATEDIFF(NOW(),a.data_envio) as enviados,DATE_FORMAT(ed.deadline_avaliacao,'%d/%m/%Y') as deadline_avaliacao,ed.nome 
    FROM editalProjeto as e, avaliacoes as a,editais as ed WHERE e.id=a.idProjeto AND e.tipo=ed.id AND e.valendo=1
    AND a.finalizado=0 AND a.aceitou!=0 AND DATEDIFF(NOW(),a.data_envio)>1 
    AND tipo in (SELECT id from editais WHERE deadline_avaliacao>now() AND ADDDATE(deadline,5)<now())
    """
    consulta = """
    SELECT e.id,e.titulo,e.resumo,a.avaliador,a.link,a.id,a.enviado,a.token,e.categoria,
    e.tipo, DATEDIFF(NOW(),a.data_envio) as enviados,DATE_FORMAT(ed.deadline_avaliacao,'%d/%m/%Y') as deadline_avaliacao,ed.nome 
    FROM editalProjeto as e, avaliacoes as a,editais as ed WHERE e.id=a.idProjeto AND e.tipo=ed.id AND e.valendo=1
    AND a.finalizado=0 AND a.aceitou!=0 AND DATEDIFF(NOW(),a.data_envio)>=1 
    AND tipo in (SELECT id from editais WHERE deadline_avaliacao>now())
    """
    linhas,total = executarSelect(consulta)
    for linha in linhas:
        titulo = str(linha[1])
        resumo = str(linha[2])
        link = str(linha[4])
        token = str(linha[7])
        email_avaliador = str(linha[3])
        link_recusa = ROOT_SITE + "/cppgi/recusarConvite?token=" + token
        deadline = str(linha[11])
        nome_longo = str(linha[12])
        with app.app_context():
            texto_email = render_template('email_avaliador.html',nome_longo=nome_longo,titulo=titulo,resumo=resumo,link=link,link_recusa=link_recusa,deadline=deadline)
            msg = Message(subject = u"CONVITE: AVALIAÇÃO DE TRABALHO CIENTÍFICO",bcc=[email_avaliador],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
            try:
                if PRODUCAO==1:
                    mail.send(msg)
                consulta = "UPDATE avaliacoes SET enviado=enviado+1,data_envio=NOW() WHERE id=" + str(linha[5])
                atualizar(consulta)    
            except:
                logging.error("EMAIL SOLICITANDO AVALIACAO FALHOU: " + email_avaliador)
                return("Erro! Verifique o log!")

"""
Envia solicitação para os avaliadores dos trabalhos escritos
"""
@app.route("/emailSolicitarAvaliacao", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def email_solicitar_avaliacao():
    t = threading.Thread(target=enviar_email_avaliadores)
    t.start()
    flash("Envio de e-mails iniciado!")
    return(redirect(url_for('root')))
    
def enviarPedidoAvaliacao(id):
    gerarLinkAvaliacao()
    consulta = """
    SELECT e.id,e.titulo,e.resumo,a.avaliador,a.link,a.id,a.enviado,a.token,e.categoria,e.tipo 
    FROM editalProjeto as e, avaliacoes as a WHERE e.id=a.idProjeto AND e.valendo=1 
    AND a.finalizado=0 AND e.id=""" + str(id) + """ 
    ORDER BY a.id DESC
    """
    linhas,total = executarSelect(consulta)
    logging.debug("Enviado pedido de avaliacao para: " + str(total))
    
    for linha in linhas:
        titulo = str(linha[1])
        resumo = str(linha[2])
        link = str(linha[4])
        token = str(linha[7])
        email_avaliador = str(linha[3])
        app.logger.debug(email_avaliador)
        link_recusa = ROOT_SITE + "/cppgi/recusarConvite?token=" + token
        deadline = obterColunaUnica('editais',"DATE_FORMAT(deadline_avaliacao,'%d/%m/%Y')",'id',str(linha[9]))
        nome_longo = obterColunaUnica('editais','nome','id',str(linha[9]))
        with app.app_context():
            texto_email = render_template('email_avaliador.html',nome_longo=nome_longo,titulo=titulo,resumo=resumo,link=link,link_recusa=link_recusa,deadline=deadline)
            msg = Message(subject = u"CONVITE: AVALIAÇÃO DE TRABALHO CIENTÍFICO",bcc=[email_avaliador],reply_to="NAO-RESPONDA@ufca.edu.br",html=texto_email)
            try:
                if PRODUCAO==1:
                    mail.send(msg)
                logging.debug("E-MAIL ENVIADO COM SUCESSO.")    
            except:
                logging.error("EMAIL SOLICITANDO AVALIACAO FALHOU: " + email_avaliador)

def remover_arquivo(arquivo):
    if os.path.exists(arquivo):
        try:
            os.remove(arquivo)
        except Exception as e:
            app.logger.debug(str(e))

def redimensionar_imagem(certificado,novotamanho):
    imagem = Image.open(CERTIFICADOS_TEMPLATE_DIR + certificado)
    novaimagem = imagem.resize(novotamanho)
    imagem.close()
    novaimagem.save(CERTIFICADOS_TEMPLATE_DIR + certificado)

@app.route("/salvarEdital/<operacao>", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def salvar_edital(operacao):
    edital = int(request.form['codigo_edital'])
    if int(operacao)==0:
        consulta = """
        UPDATE editais set deadline='%s',deadline_avaliacao='%s',nome_longo='%s',nome_curto='%s',
        deadline_apresentacao='%s',deadline_versao_final='%s',situacao='%s',isbn='%s',
        periodo='%s', local='%s'  
        WHERE id=%s 
        """ % (str(request.form['deadline']),str(request.form['deadline_avaliacao']),str(request.form['nome']),str(request.form['nome_curto']),str(request.form['deadline_apresentacao']),str(request.form['deadline_final']),str(request.form['situacao']),str(request.form['isbn']),str(request.form['periodo']),str(request.form['local']),str(edital),)
        atualizar(consulta)
        return("Alterações gravadas com sucesso!")
    else:
        if 'avaliador' in request.files:
            certificado = "avaliador_" + str(edital) + ".png"
            remover_arquivo(CERTIFICADOS_TEMPLATE_DIR + certificado)
            certificados.save(request.files['avaliador'],name=certificado)
            if os.path.getsize(CERTIFICADOS_TEMPLATE_DIR + certificado)!=0:
                consulta = """
                UPDATE editais set declaracao_avaliador='%s' WHERE id=%s
                """ % (certificado,str(edital))
                atualizar(consulta)
                novotamanho = (1754,1238)
                redimensionar_imagem(certificado,novotamanho)
            
        if 'apresentador' in request.files:
            certificado = "apresentador_" + str(edital) + ".png"
            remover_arquivo(CERTIFICADOS_TEMPLATE_DIR + certificado)
            certificados.save(request.files['apresentador'],name=certificado)
            if os.path.getsize(CERTIFICADOS_TEMPLATE_DIR + certificado)!=0:
                consulta = """
                UPDATE editais set certificado_apresentador='%s' WHERE id=%s
                """ % (certificado,str(edital))
                atualizar(consulta)
                novotamanho = (1754,1238)
                redimensionar_imagem(certificado,novotamanho)
            
        if 'convidado' in request.files:
            certificado = "convidado_" + str(edital) + ".png"
            remover_arquivo(CERTIFICADOS_TEMPLATE_DIR + certificado)
            certificados.save(request.files['convidado'],name=certificado)
            if os.path.getsize(CERTIFICADOS_TEMPLATE_DIR + certificado)!=0:
                consulta = """
                UPDATE editais set certificado_convidado='%s' WHERE id=%s
                """ % (certificado,str(edital))
                atualizar(consulta)
                novotamanho = (1754,1238)
                redimensionar_imagem(certificado,novotamanho)
            

        if 'moderador' in request.files:
            certificado = "moderador_" + str(edital) + ".png"
            remover_arquivo(CERTIFICADOS_TEMPLATE_DIR + certificado)
            certificados.save(request.files['moderador'],name=certificado)
            if os.path.getsize(CERTIFICADOS_TEMPLATE_DIR + certificado)!=0:
                consulta = """
                UPDATE editais set certificado_moderador='%s' WHERE id=%s
                """ % (certificado,str(edital))
                atualizar(consulta)
                novotamanho = (1754,1238)
                redimensionar_imagem(certificado,novotamanho)
            

        if 'participante' in request.files:
            certificado = "participante_" + str(edital) + ".png"
            remover_arquivo(CERTIFICADOS_TEMPLATE_DIR + certificado)
            certificados.save(request.files['participante'],name=certificado)
            if os.path.getsize(CERTIFICADOS_TEMPLATE_DIR + certificado)!=0:
                consulta = """
                UPDATE editais set certificado_participante='%s' WHERE id=%s
                """ % (certificado,str(edital))
                atualizar(consulta)
                novotamanho = (1754,1238)
                redimensionar_imagem(certificado,novotamanho)
            

        if 'demais' in request.files:
            certificado = "demais_" + str(edital) + ".png"
            remover_arquivo(CERTIFICADOS_TEMPLATE_DIR + certificado)
            certificados.save(request.files['demais'],name=certificado)
            if os.path.getsize(CERTIFICADOS_TEMPLATE_DIR + certificado)!=0:
                consulta = """
                UPDATE editais set certificado_demais='%s' WHERE id=%s
                """ % (certificado,str(edital))
                atualizar(consulta)
                novotamanho = (1754,1238)
                redimensionar_imagem(certificado,novotamanho)

        return(redirect(url_for('root')))

@app.route("/cadastrar_edital", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def cadastrar_edital():
    if request.method == "GET":
        return(render_template('cadastrar_edital.html'))
    else:
        try:
            consulta = """INSERT INTO editais 
            (nome,nome_curto,nome_longo,deadline,deadline_avaliacao,deadline_versao_final,
            deadline_apresentacao,situacao,isbn,setor) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,1)"""
            valores = (str(request.form['nome']),str(request.form['nome_curto']),str(request.form['nome']),str(request.form['deadline']),str(request.form['deadline_avaliacao']),str(request.form['deadline_final']),str(request.form['deadline_apresentacao']),str(request.form['situacao']),str(request.form['isbn']))
        except Exception as e:
            return(str(e))
    inserir(consulta,valores)
    flash('Edital adicionado com sucesso')
    return(redirect(url_for('root')))

@app.route("/ver_imagem/<qual>", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def ver_imagem(qual):
    return (send_from_directory(CERTIFICADOS_TEMPLATE_DIR, qual))

@app.route("/salvar_projeto", methods=['GET', 'POST'])
@auth.login_required(role=['admin'])
def salvar_projeto():
    nome = str(request.form['nome'])
    ga = str(request.form['grande_area'])
    titulo = str(request.form['titulo'])
    palavras = str(request.form['palavras'])
    situacao = str(request.form['situacao'])
    id_projeto = str(request.form['id_projeto'])
    consulta = """
    UPDATE editalProjeto SET nome='%s',ua='%s',titulo='%s',palavras='%s',situacao=%s WHERE id=%s
    """ % (nome,ga,titulo,palavras,situacao,id_projeto)
    atualizar(consulta)
    return("OK")

@app.route("/listar_consultores/<id_projeto>", methods=['GET'])
@auth.login_required(role=['admin'])
def listar_consultores(id_projeto):
    
    consulta = """
    SELECT id,idProjeto,token,avaliador,nome_avaliador,recomendacao,link,finalizado,data_avaliacao 
    FROM avaliacoes 
    WHERE idProjeto=%s ORDER BY finalizado DESC, id ASC
    """ % (id_projeto)
    avaliacoes,total = executarSelect(consulta)
    titulo = obterColunaUnica('editalProjeto','titulo','id',id_projeto)
    autores = obterColunaUnica('editalProjeto','nome','id',id_projeto)
    edital = obterColunaUnica('editalProjeto','tipo','id',id_projeto)
    area = obterColunaUnica('editalProjeto','ua','id',id_projeto)
    return(render_template('listar_avaliadores.html',avaliacoes=avaliacoes,id_projeto=id_projeto,titulo=titulo,autores=autores,edital=edital,area=area))

@app.route("/listar_consultores_edital/<edital>", methods=['GET'])
@auth.login_required(role=['admin'])
def listar_consultores_edital(edital):
    consulta = """
    SELECT avaliacoes.id,idProjeto,avaliacoes.token,avaliador,nome_avaliador,
    recomendacao,avaliacoes.link,finalizado,data_avaliacao 
    FROM avaliacoes 
    INNER JOIN editalProjeto on editalProjeto.id=avaliacoes.idProjeto 
    INNER JOIN editais ON editais.id=editalProjeto.tipo 
    WHERE editais.id=%s
    ORDER BY avaliacoes.idProjeto,avaliacoes.finalizado DESC
    """ %(edital)
    nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
    avaliacoes,total = executarSelect(consulta)
    return(render_template('listar_avaliadores_edital.html',avaliacoes=avaliacoes,edital=edital,nome_longo=nome_longo))

@app.route("/salvar_consultores", methods=['POST'])
@auth.login_required(role=['admin'])
def salvar_consultores():
    id_avaliacao = request.form['id_avaliacao']
    avaliador = request.form['avaliador']
    nome = str(request.form['nome_avaliador'])
    recomendacao = request.form['recomendacao']
    finalizado = request.form['finalizado']
    consulta = """
    UPDATE avaliacoes SET avaliador='%s',nome_avaliador='%s',recomendacao=%s,finalizado=%s 
    WHERE id=%s
    """ % (avaliador,nome,recomendacao,finalizado,id_avaliacao)
    atualizar(consulta)
    return(str(id_avaliacao))

@app.route("/remover_avaliacao/<id_avaliacao>/<id_projeto>", methods=['GET'])
@auth.login_required(role=['admin'])
def remover_avaliacao(id_avaliacao,id_projeto):
    consulta = """
    DELETE FROM avaliacoes WHERE id=%s
    """ % (id_avaliacao)
    atualizar(consulta)
    flash(u"Avaliação removida com sucesso!")
    return(redirect(url_for('listar_consultores',id_projeto=id_projeto)))

@app.route("/cadastrar_salas/<edital>", methods=['GET','POST'])
@auth.login_required(role=['admin'])
def cadastrar_salas(edital):
    if request.method=='GET':
        return(render_template('cadastrar_salas.html',edital=edital))
    else:
        tipo = request.form['tipo']
        dia = request.form['dia']
        inicio = request.form['inicio']
        fim = request.form['fim']
        slot = request.form['slots']
        salas = request.form['salas']
        consulta = """
        INSERT INTO salas (edital,tipo,dia,inicio,termino,slot,salas) VALUES (%s,%s,'%s','%s','%s',%s,'%s')
        """ % (edital,tipo,dia,inicio,fim,slot,salas)
        atualizar(consulta)
        flash(u"Sessão incluída com sucesso")
        return(redirect(url_for('listar_salas',edital=edital)))

@app.route("/listar_salas/<edital>", methods=['GET'])
@auth.login_required(role=['admin'])
def listar_salas(edital):
    consulta = """
    SELECT id,edital,tipo,dia,time_format(inicio,'%H:%i') as inicio,time_format(termino,'%H:%i') as termino,slot,salas FROM salas WHERE edital=""" + str(edital)
    linhas,total = executarSelect(consulta)
    nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
    return(render_template('listar_salas.html',sessoes=linhas,nome_longo=nome_longo,edital=edital))

@app.route("/salvar_salas", methods=['POST'])
@auth.login_required(role=['admin'])
def salvar_salas():
    tipo = request.form['tipo']
    dia = request.form['dia']
    inicio = request.form['inicio']
    fim = request.form['fim']
    slot = request.form['slot']
    salas = request.form['salas']
    id_salas = request.form['id_salas']
    consulta = """
    UPDATE salas SET tipo=%s,dia='%s',inicio='%s',termino='%s',slot=%s,salas='%s'
    WHERE id=%s
    """ % (tipo,dia,inicio,fim,slot,salas,id_salas)
    atualizar(consulta)
    return("OK")

@app.route("/remover_salas/<id_salas>", methods=['GET'])
@auth.login_required(role=['admin'])
def remover_salas(id_salas):
    consulta = """DELETE FROM salas WHERE id=%s""" % (id_salas)
    atualizar(consulta)
    edital = obterColunaUnica('salas','edital','id',id_salas)
    return(redirect(url_for('listar_salas',edital=edital)))

@app.route("/local_apresentacao/<edital>", methods=['GET'])
@auth.login_required(role=['admin'])
def local_apresentacao(edital):
    consulta = u"""
    SELECT id,UPPER(nome),ua,UPPER(titulo),data_apresentacao,local_apresentacao,
    categoria,modalidade,media1,media2,obs,arquivo_projeto
    FROM editalProjeto 
    WHERE valendo=1 and situacao=1 and tipo=%s 
    ORDER BY data_apresentacao,local_apresentacao,categoria,ua
    """ %(edital)
    linhas,total = executarSelect(consulta)
    consulta_salas = """
    SELECT 
    """
    descricao = obterColunaUnica('editais','nome_longo','id',edital)
    return(render_template('local_apresentacao.html',novos=linhas,total_novos=total,descricao=descricao,edital=edital))

@app.route("/salvar_local_data", methods=['POST'])
@auth.login_required(role=['admin'])
def salvar_local_data():
    id_projeto = request.form['id_projeto']
    local = request.form['local_apresentacao']
    data = request.form['data_apresentacao']
    categoria = request.form['categoria']
    modalidade = request.form['modalidade']
    obs = request.form['obs']
    consulta = """
    UPDATE editalProjeto SET local_apresentacao='%s',data_apresentacao='%s',categoria=%s,modalidade=%s,obs='%s' 
    WHERE id=%s
    """ %(local,data,categoria,modalidade,obs,id_projeto)
    atualizar(consulta)
    return("OK")
    #TODO: Sala_link
    #TODO: implementar o autenticar_certificado
    #TODO: Demais certificados

@app.route("/cadastrar_usuario/<operacao>", methods=['GET','POST'])
@auth.login_required(role=['admin'])
def cadastrar_usuario(operacao):
    if request.method=='GET':
        if int(operacao)==0: #Cadastrar novo usuário
            return(render_template('cadastrar_usuario.html'))
        else: #Listar usuários
            consulta = """
            SELECT id,username,password,permission,roles,
            nome,email FROM users
            ORDER BY nome
            """
            usuarios,total = executarSelect(consulta)
            return(render_template('listar_usuarios.html',usuarios=usuarios))
    else: #POST  
        #Operação 0: Cadastrar; 1: Atualizar
        username = request.form['username']
        password = request.form['password']
        permission = request.form['permission']
        roles = request.form['roles']
        nome = request.form['nome']
        email = request.form['email']
        id_usuario = request.form['id_usuario']
        if operacao==0: #Cadastrar
            consulta = """
            INSERT INTO users (username,password,permission,roles,nome,email) 
            VALUES ('%s','%s',%s,'%s','%s','%s)
            """ %(username,password,permission,roles,nome,email)
            atualizar(consulta)
            flash(u"Usuário cadastrado com sucesso!")
            return(redirect(url_for(cadastrar_usuario,operacao=1)))
        else: #Atualizar
            consulta = """
            UPDATE users SET username='%s',password='%s',permission=%s,roles='%s',nome='%s',
            email='%s'
            WHERE id=%s
            """ %(username,password,permission,roles,nome,email,id_usuario)
            atualizar(consulta)
            return("OK")

@app.route("/remover_usuario/<id_usuario>", methods=['GET','POST'])
@auth.login_required(role=['admin'])
def remover_usuario(id_usuario):
    consulta = """
    DELETE FROM users WHERE id=%s
    """ %(id_usuario)
    atualizar(consulta)
    flash(u"Usuário removido com sucesso!")
    return(redirect(url_for(cadastrar_usuario,operacao=1)))

@app.route("/avaliador_sala/<edital>", methods=['GET','POST'])
@auth.login_required(role=['admin'])
def avaliador_sala(edital):
    if request.method=='GET':
        consulta = """
        SELECT tipo,dia,inicio,termino,salas FROM salas
        WHERE edital=%s
        """ %(edital)
        datas,total = executarSelect(consulta)
        
        consulta_usuarios = """
        SELECT username,nome FROM users 
        WHERE roles like '%avaliador%'
        ORDER BY nome
        """
        usuarios,total = executarSelect(consulta_usuarios)
        nome_longo = obterColunaUnica('editais','nome_longo','id',edital)

        return(render_template('avaliador_sala.html',edital=edital,usuarios=usuarios,datas=datas,nome_longo=nome_longo))

    else:
        username = request.form['username']
        sala_data = request.form['sala_data']
        area = request.form['area']
        data,sala=str(sala_data).split(';')
        consulta = """
        INSERT INTO usuarios_salas(username,edital,sala,data,area) 
        VALUES('%s',%s,'%s','%s','%s')
        """ %(username,edital,sala,data,area)
        atualizar(consulta)
        return("SUCESSO")

@app.route("/avaliador_sala_listar/<edital>", methods=['GET','POST'])
@auth.login_required(role=['admin'])
def avaliador_sala_listar(edital):
    consulta = """
    SELECT usuarios_salas.id,usuarios_salas.username,usuarios_salas.edital,
    usuarios_salas.sala,usuarios_salas.data,usuarios_salas.area,users.nome
    FROM usuarios_salas
    INNER JOIN users ON users.username=usuarios_salas.username 
    WHERE edital=%s 
    ORDER BY area,data,sala
    """ %(edital)
    linhas,total = executarSelect(consulta)
    nome_longo = obterColunaUnica('editais','nome_longo','id',edital)
    
    consulta_usuarios = """
    SELECT username,nome FROM users 
    WHERE roles like '%avaliador%'
    ORDER BY nome
    """
    usuarios,total = executarSelect(consulta_usuarios)
    
    consulta_salas = """
    SELECT dia,salas FROM salas 
    WHERE edital=%s 
    ORDER BY dia,salas
    """ %(edital)

    datas,total = executarSelect(consulta_salas)

    return(render_template('avaliador_sala_listar.html',linhas=linhas,edital=edital,nome_longo=nome_longo,usuarios=usuarios,datas=datas))

@app.route("/avaliador_sala_remover/<id_avaliador_sala>/<edital>", methods=['GET','POST'])
@auth.login_required(role=['admin'])
def avaliador_sala_remover(id_avaliador_sala,edital):
    consulta = """
    DELETE FROM usuarios_salas WHERE id=%s
    """ %(id_avaliador_sala)
    atualizar(consulta)
    flash(u"Atribuição removida com sucesso!")
    return(redirect(url_for('avaliador_sala_listar',edital=edital)))

@app.route("/salvar_avaliador_sala", methods=['POST'])
@auth.login_required(role=['admin'])
def salvar_avaliador_sala():
    username = request.form['username']
    sala_data = request.form['sala_data']
    area = request.form['area']
    data,sala=str(sala_data).split(';')
    id_avaliador_sala = request.form['id_avaliador_sala']
    consulta = """
    UPDATE usuarios_salas SET username='%s',sala='%s',data='%s',area='%s' 
    WHERE id=%s
    """ %(username,sala,data,area,id_avaliador_sala)
    atualizar(consulta)
    return("OK")

@app.route("/autenticar_certificado/<tipo>/<codigo>/<id_projeto>", methods=['GET'])
def autenticar_certificado(tipo,codigo,id_projeto):
    if tipo==0: #CERTIFICADO DE APRESENTADOR
        token = obterColunaUnica('editalProjeto','token','id',id_projeto)
        if token==codigo:
            return(redirect(url_for('baixarCertificado',id_projeto=id_projeto)))
        else:
            return("Certificado inexistente!")
    elif tipo==1: #Moderador
        return("Não implementado!")
    elif tipo==2: #Participantes
        return("Não implementado!")
    elif tipo==3: #Convidados
        return("Não implementado!")
    else: #Avaliadores
        return("Não implementado!")

@app.route('/img_file/<path:filename>')
def img_file(filename):
    #https://stackoverflow.com/questions/26971491/how-do-i-link-to-images-not-in-static-folder-in-flask
    return send_from_directory(CERTIFICADOS_TEMPLATE_DIR, filename, as_attachment=True)

def get_image_file_as_base64_data(image):
    #https://stackoverflow.com/questions/38329909/pdfkit-not-converting-image-to-pdf
    with open(image, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode()

@app.route("/salvar/<tabela>/<valor_id>/<coluna>/<novo_valor>", methods=['GET'])
@auth.login_required(role=['admin'])
def salvar(tabela,valor_id,coluna,novo_valor):
    consulta = """
    UPDATE %s SET %s='%s' 
    WHERE id=%s
    """ %(tabela,coluna,novo_valor,valor_id)
    atualizar(consulta)
    return("OK")

@app.route("/detalhes/<tabela>/<valor_id>/<coluna>", methods=['GET'])
@auth.login_required(role=['admin'])
def detalhes(tabela,valor_id,coluna):
    valor = obterColunaUnica(tabela,coluna,'id',valor_id)
    return(valor)

@app.route('/enviar_arquivo/<filename>')
def enviar_arquivo(filename):
    return(send_from_directory(ATTACHMENTS_DIR,filename))


if __name__ == "__main__":
    from app_api import Submissoes,Editais,Avaliacoes
    api.add_resource(Submissoes,'/api/submissoes/<tipo>/<id_edital>/<modalidade>/<area>')
    api.add_resource(Editais,'/api/editais')
    api.add_resource(Avaliacoes,'/api/avaliacoes/<id_edital>/<modalidade>/<area>')
    serve(app, host='0.0.0.0', port=80, url_prefix='/cppgi')

