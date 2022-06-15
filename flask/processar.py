# -*- coding: utf-8 -*-
#https://stackoverflow.com/questions/8329741/issue-with-smtplib-sending-mail-with-unicode-characters-in-python-3-1
#https://mariadb.com/kb/en/library/timestampdiff/
import logging
import os
import sys
import MySQLdb
import xml.etree.ElementTree as ET
from modules import scoreLattes as SL
import smtplib
from email.mime.multipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication

SITE = "https://sci02-ter-jne.ufca.edu.br/cppgi/avaliacao"
LINK_RECUSA = "https://sci02-ter-jne.ufca.edu.br/cppgi/"
LINK_HOME = "https://sci02-ter-jne.ufca.edu.br/cppgi/"
UPLOAD_FOLDER = '/home/perazzo/cppgi/static/files/'
ALLOWED_EXTENSIONS = set(['pdf','xml'])
WORKING_DIR='/home/perazzo/cppgi/'
CURRICULOS_DIR='/home/perazzo/cppgi/static/files/'
DOCUMENTOS_DIR='/home/perazzo/cppgi/documentos/'
#Obtendo senhas
lines = [line.rstrip('\n') for line in open(WORKING_DIR + 'senhas.pass')]
PASSWORD = lines[0]
GMAIL_PASSWORD = lines[1]


def atualizar(consulta):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.autocommit(False)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    try:
        cursor.execute(consulta)
        conn.commit()
    except MySQLdb.Error, e:
        e = sys.exc_info()[0]
        logging.debug(e)
	logging.debug(consulta)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def gerarLinkAvaliacao():
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT id,idProjeto,token FROM avaliacoes ORDER by id"
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    for linha in linhas:
        id = str(linha[0])
        idProjeto = str(linha[1])
        token = str(linha[2])
        link = SITE + "?id=" + idProjeto + "&token=" + token
        consulta = "UPDATE avaliacoes SET link=\"" + link + "\"" + " WHERE id=" + id
        atualizar(consulta)
    cursor.close()
    conn.close()

def getArquivo(edital,tipo):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    if tipo==1:
        consulta = "SELECT carta_convite FROM editais WHERE id=" + str(edital)
    else:
        consulta = "SELECT carta_agradecimento FROM editais WHERE id=" + str(edital)
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    arquivo = ""
    for linha in linhas:
        arquivo = linha[0]
    arquivo = DOCUMENTOS_DIR + arquivo
    cursor.close()
    conn.close()
    return (arquivo)

'''
tipo 0: E-mail ordinário
tipo 1: E-mail convite
tipo 2: E-mail agradecimento
'''
def enviarEmail(to,subject,body,html,tipo=1,edital=7):
    gmail_user = 'pesquisa.prpi@ufca.edu.br'
    gmail_password = GMAIL_PASSWORD
    sent_from = gmail_user
    para = [to]
    msg = MIMEMultipart('alternative')
    part1 = MIMEText(body,'plain','utf-8')
    part2 = MIMEText(html, 'html','utf-8')
    msg.attach(part1)
    msg.attach(part2)
    if tipo==1:
        #pdf = open(WORKING_DIR + "convite-consultor-ad-hoc.pdf", "rb")
        anexo = getArquivo(edital,tipo)
        pdf = open(anexo, "rb")
    else:
        #pdf = open(WORKING_DIR + "carta-agradecimento-adhoc.pdf", "rb")
        anexo = getArquivo(edital,tipo)
        pdf = open(anexo, "rb")
    pdfAttachment = MIMEApplication(pdf.read(), _subtype = "pdf")
    if tipo==1:
        pdfAttachment.add_header('content-disposition', 'attachment', filename = 'convite.pdf')
    else:
        pdfAttachment.add_header('content-disposition', 'attachment', filename = 'agradecimento.pdf')
    message = MIMEMultipart('mixed')
    message.attach(msg)
    if tipo in (1,2):
        message.attach(pdfAttachment)
    message['From'] = gmail_user
    message['To'] = to
    message['Subject'] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, message.as_string())
        server.close()
        logging.debug("E-Mail enviado com sucesso para " + to)
        return (True)
    except:
        e = sys.exc_info()[0]
        logging.debug("Erro ao enviar e-mail: " + str(e))
        return (False)

def prazoAvaliacao(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = """SELECT DATE_FORMAT(deadline_avaliacao,'%d/%m/%Y') FROM editais WHERE id=""" + codigoEdital
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    resultado = ""
    for linha in linhas:
        resultado = linha[0]
    cursor.close()
    conn.close()
    return (str(resultado))

def podeAvaliar(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT id,deadline_avaliacao FROM editais WHERE deadline_avaliacao>CURRENT_TIMESTAMP() AND id=" + codigoEdital
    cursor.execute(consulta)
    total = cursor.rowcount
    cursor.close()
    conn.close()
    if (total==0): #Edital com avaliacoes encerradas
        return(False)
    else: #Edital com avaliacoes em andamento
        return(True)

def jaAgradeceu(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT id,agradecimento FROM editais WHERE agradecimento=0 AND id=" + codigoEdital
    cursor.execute(consulta)
    total = cursor.rowcount
    cursor.close()
    conn.close()
    if (total==1): #Agradecimento ainda não enviado
        return(False)
    else: #Agradecimento enviado...
        return(True)

def descricaoEdital(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT id,nome FROM editais WHERE id=" + codigoEdital
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    nomeEdital = "EDITAL NAO DEFINIDO"
    for linha in linhas:
        nomeEdital = unicode(linha[1])
    cursor.close()
    conn.close()
    return (nomeEdital)

def enviarLinksParaAvaliadores(codigoEdital,novos=0):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()

    if novos==0:
        consulta = """SELECT e.id,e.titulo,e.resumo,a.avaliador,a.link,a.id,a.enviado,a.token,e.categoria,e.tipo,IF(modalidade=2,'TRABALHO COMPLETO',IF(modalidade=1,'RESUMO EXPANDIDO','RESUMO SIMPLES')) FROM editalProjeto as e, avaliacoes as a WHERE e.id=a.idProjeto AND e.valendo=1 AND a.finalizado=0 AND a.aceitou!=0 AND tipo=""" + codigoEdital
    else:
        consulta = """SELECT e.id,e.titulo,e.resumo,a.avaliador,a.link,a.id,a.enviado,a.token,e.categoria,e.tipo,IF(modalidade=2,'TRABALHO COMPLETO',IF(modalidade=1,'RESUMO EXPANDIDO','RESUMO SIMPLES')) FROM editalProjeto as e, avaliacoes as a WHERE e.id=a.idProjeto AND e.valendo=1 AND a.finalizado=0 AND a.aceitou!=0 AND enviado=0 AND tipo=""" + codigoEdital

    cursor.execute(consulta)
    linhas = cursor.fetchall()

    if podeAvaliar(codigoEdital):
        print("Enviando " + str(len(linhas)) + " e-mails...")
        deadline = prazoAvaliacao(codigoEdital)
        for linha in linhas:
            titulo = unicode(linha[1])
            resumo = unicode(linha[2])
            email = unicode(linha[3])
            envios = int(linha[6])
            #email = "rafael.mota@ufca.edu.br"
            link = str(linha[4])
            id_avaliacao = str(linha[5])
            enviado = int(linha[6])
            token_avaliacao = unicode(linha[7])
            categoria_projeto = int(linha[8])
            link_recusa = LINK_RECUSA + "recusarConvite?token=" + token_avaliacao
            mensagem = unicode("Título do Projeto: " + titulo + "\n")
            mensagem = mensagem + "Link para avaliação: " + link + " \n"
            mensagem = mensagem + "Resumo do projeto\n" + resumo

            html = "<html><body>\n"
            html = html + "<h3><center>Universidade Federal do Cariri (UFCA) - II CONGRESSO DE PESQUISA (CONPESQ)</center></h3><BR>"
            html = html + "<h1><center>Solicitação de Avaliação de Trabalho Científico (e-mail automático)</center></h1><BR>"

            if envios==0:
                html = html + "Prezado(a) senhor(a), <BR>Gostaríamos de convida-lo(a) para avaliação do trabalho científico descrito(s) abaixo. O arquivo relativo pode ser acessado no link informado abaixo.<BR>"
            else:
                html = html + "Prezado(a) senhor(a), <BR>Gostaríamos de lembra-lo sobre a avaliação do trabalho científico descrito(s) abaixo. O arquivo relativo pode ser acessado no link informado abaixo.<BR>"

            html = html + "O trabalho está em avaliação para apresentação no II CONGRESSO DE PESQUISA(CONPESQ).<BR>"
            html = html + "Quaisquer dúvidas estamos a disposição. A avaliação é totalmente anonima para os autores da submissão. A declaração de avaliação é gerada imediatamente após a conclusão da avaliação.<BR>"
            html = html + "<h4>Em caso de indisponibilidade de avaliação, favor <a href=\"" + link_recusa + "\">Clique aqui para recusar o convite</a>" + "</h4><BR>\n"
            html = html + "<h2>Link para acessar os arquivos e envio da avaliação: <a href=\"" + link + "\">Clique Aqui</a></h2><BR>\n"
            html = html + "<h2>Título do trabalho: " + titulo + "</h2><BR>\n"
            html = html + "<h3>Resumo do trabalho <BR> " + resumo + "</h3><BR>\n"
            html = html + "<h3>Data limite para envio da avaliação:" + deadline + "  <BR> </h3><BR>\n"
            html = html + "<h3>Site oficial do evento: http://conpesq.ufca.edu.br/ </h3><BR>\n"
            html = html + "<h3>Telefone institucional para contato direto com o administrador do sistema do evento: (88)3221-9566 - http://telefonia.ufca.edu.br </h3><BR>\n"
            html = html + "</body></html>"

            if envios==0:
                enviarEmail(email,"[CONPESQ/UFCA - Solicitação de Avaliação de Trabalho Científico]",mensagem,html,1)
                consulta_enviado = "UPDATE avaliacoes SET data_envio=CURRENT_TIMESTAMP() WHERE id=" + id_avaliacao
                atualizar(consulta_enviado)
            else:
                enviarEmail(email,"[CONPESQ/UFCA - LEMBRETE de Solicitação de Avaliação de Trabalho Científico]",mensagem,html,1)
                consulta_enviado = "UPDATE avaliacoes SET data_envio2=CURRENT_TIMESTAMP() WHERE id=" + id_avaliacao
                atualizar(consulta_enviado)
            print("E-mail enviado para: " + email)
            enviado = enviado + 1
            consulta_enviado = "UPDATE avaliacoes SET enviado=" + str(enviado) + " WHERE id=" + id_avaliacao
            atualizar(consulta_enviado)

    else:
        print("Prazo de avaliação expirado para o edital selecionado.")
    cursor.close()
    conn.close()

def enviarAgradecimentosParaAvaliadores(codigoEdital):
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = """SELECT a.avaliador,a.token FROM avaliacoes a, editalProjeto e WHERE a.avaliador not like '%ufca%' AND a.finalizado=1 AND a.idProjeto=e.id AND e.tipo=""" + codigoEdital
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    if (not podeAvaliar(codigoEdital)) and (not jaAgradeceu(codigoEdital)): #Se não foi enviado agradecimento e as avaliações já encerraram-se
        print("Enviando " + str(len(linhas)) + " e-mails...")
        for linha in linhas:
            email = unicode(linha[0])
            token = str(linha[1])
            #email = "rafael.mota@ufca.edu.br"
            link = LINK_HOME + "declaracaoAvaliador?token=" + token
            mensagem = unicode("CARTA AGRADECIMENTO.")
            html = "<html><body>\n"
            html = html + "<h3><center>Universidade Federal do Cariri (UFCA) - Coordenadoria de Pesquisa</center></h3><BR>"
            html = html + "<h1><center>AGRADECIMENTO</center></h1><BR>"
            html = html + "Prezado(a) senhor(a), <BR>Gostaríamos de agradece-lo(a) pela participação como consultor ad-hoc no processo seletivo (" + descricaoEdital(codigoEdital) +  ") da Coordenadoria de Pesquisa da UFCA.<BR>"
            html = html + "A carta agradecimento oficial segue em anexo a este e-mail.<BR>"
            html = html + "<h2>Link permanente para acessar a declaração de participação: <a href=\"" + link + "\">Clique Aqui</a>. Em caso de erros no nome, favor responder este e-mail solicitando a correção.</h2><BR>\n"
            html = html + "<h3>Site oficial do processo seletivo PRPI/UFCA: http://prpi.ufca.edu.br/ </h3><BR>\n"
            html = html + "<h3>Telefone institucional para contato direto com o coordenador: (88)3221-9566 - http://telefonia.ufca.edu.br </h3><BR>\n"
            html = html + "</body></html>"
            enviarEmail(email,"[UFCA - AGRADECIMENTO]",mensagem,html,2)
            print("E-mail enviado para: " + email)

    else:
        print("Agradecimento já enviado para o edital selecionado ou prazo de avaliação em andamento.")
    consulta_agradecimento = "UPDATE editais SET agradecimento=1 WHERE id=" + codigoEdital
    atualizar(consulta_agradecimento)
    cursor.close()
    conn.close()


def tipo_de_trabalho(codigoEdital):
    from PyPDF2 import PdfFileReader
    conn = MySQLdb.connect(host="db_cppgi", user="cppgi", passwd=PASSWORD, db="cppgi", charset="utf8", use_unicode=True)
    conn.select_db('cppgi')
    cursor  = conn.cursor()
    consulta = "SELECT id,nome,ua,arquivo_projeto,modalidade FROM editalProjeto WHERE valendo=1 ORDER BY modalidade,ua,id"
    cursor.execute(consulta)
    linhas = cursor.fetchall()
    cont = 0
    for linha in linhas:
        id = str(linha[0])
        nome = unicode(linha[1])
        ua = unicode(linha[2])
        arquivo = UPLOAD_FOLDER + str(linha[3])
        modalidade = int(linha[4])
        try:
            pdf = PdfFileReader(open(arquivo,'rb'))
            paginas = int(pdf.getNumPages())
            if ((modalidade==0) and (paginas!=1)): #Resumo simples
                #print("RESUMO SIMPLES",id,nome,paginas)
                print("RESUMO SIMPLES")
                print(id)
                print(nome)
                print(str(paginas) + " páginas")
                print("*********************")
                cont = cont + 1
            if ((modalidade==1) and (not (3<=paginas<=5))): #Resumo expandido
                #print("RESUMO EXPANDIDO",id,nome,paginas)
                print("RESUMO EXPANDIDO")
                print(id)
                print(nome)
                print(str(paginas) + " páginas")
                print("*********************")
                cont = cont + 1
            if ((modalidade==2) and (not (8<=paginas<=12))): #Trabalho completo
                #print("TRABALHO COMPLETO",id,nome,paginas)
                print("TRABALHO COMPLETO")
                print(id)
                print(nome)
                print(str(paginas) + " páginas")
                print("*********************")
                cont = cont + 1
        except:
            print("Erro id: " + id + " - " + nome)
            cont = cont + 1
    cursor.close()
    conn.close()
    print ("Total de ocorrências: " + str(cont))
#INICIO DO PROGRAMA PRINCIPAL
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# create a file handler
handler = logging.FileHandler('processar.log')
handler.setLevel(logging.DEBUG)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)
reload(sys)
sys.setdefaultencoding('utf-8')
#GERAR LINK PARA AVALIADORES
codigoEdital = "0"
enviarApenasParaNaoEnviados = 0
#tipo_de_trabalho("7")

gerarLinkAvaliacao()
print("Aqui!")
if (len(sys.argv)==2):
    print("Enviando e-mail para todos avaliadores que não finalizaram.")
    codigoEdital = str(sys.argv[1])
    enviarLinksParaAvaliadores(codigoEdital,enviarApenasParaNaoEnviados)
elif (len(sys.argv)>2):
    print("Enviando e-mail para todos avaliadores que não receberam o convite.")
    codigoEdital = str(sys.argv[1])
    enviarApenasParaNaoEnviados = int(sys.argv[2])
    enviarLinksParaAvaliadores(codigoEdital,enviarApenasParaNaoEnviados)
else:
    enviarLinksParaAvaliadores("0",0)
enviarEmail("rafael.mota@ufca.edu.br","[Cron Executado - CONPESQ]","",u"Edital: [" + codigoEdital +u"]<BR> Solicitação de Avaliação/Agradecimento para avaliadores que não finalizaram.",0)

#enviarAgradecimentosParaAvaliadores("7")
