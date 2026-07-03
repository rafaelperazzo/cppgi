from pesquisa import app,executarSelect,config,WORKING_DIR,id_generator,atualizar,inserir,ATTACHMENTS_DIR,obterColunaUnica
import pytest
import base64
import os
import re
import datetime

import random
import string

aplicacao = app.test_client()
client = aplicacao
usuario = config['DEFAULT']['usuario']
senha = config['DEFAULT']['senha']
usuario_senha = str.encode("%s:%s" %(usuario,senha))

def random_char(char_num):
       prefixo =  ''.join(random.choice(string.ascii_letters) for _ in range(char_num))
       prefixo = prefixo + "@gmail.com"
       return(prefixo)

def get_csrf_token(res, auth_required=False):
    headers = {}
    if auth_required:
        valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
        headers = {"Authorization": "Basic " + valid_credentials}
    rv = client.get(res, headers=headers)
    match = re.search(r'name="csrf_token" value="([^"]+)"', rv.data.decode())
    return match.group(1)

def get_last_id(tabela):
    consulta = """
    SELECT max(id) FROM %s
    """ %(tabela)
    linhas,total=executarSelect(consulta)
    last_id = linhas[0][0]
    return(last_id)

def post_res(res,data):
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    response = client.post(res, data=data,follow_redirects=True,headers={"Authorization": "Basic " + valid_credentials})
    assert response.status_code == 200
    return (response)

def get_res(res):
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    rv = aplicacao.get(res,follow_redirects=True,headers={"Authorization": "Basic " + valid_credentials})
    assert rv.status_code==200

def test_main():
    rv = aplicacao.get('/',follow_redirects=True)
    assert rv.status_code==200

def test_home():
    get_res('/')

def test_admin():
    get_res('/admin')

def test_admin_edital():
    get_res('/admin/9')

def test_edital_projeto():
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    consulta = """
    SELECT id FROM editais
    """
    editais,total = executarSelect(consulta)
    for edital in editais:
        get_res('/editalProjeto/' + str(edital[0]))

def test_0_criar_edital_teste():
    token = id_generator(40)
    futuro = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
    consulta = """
    INSERT INTO editais (nome,deadline,deadline_avaliacao,deadline_apresentacao,deadline_versao_final,setor,mensagem,token,declaracao_avaliador)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    valores = ("EDITAL DE TESTE AUTOMATIZADO",futuro,futuro,futuro,futuro,1,"Edital criado para testes automatizados",token,"avaliador_2372.png")
    inserir(consulta,valores)
    id_edital = get_last_id('editais')
    consulta = """
    SELECT nome,token FROM editais WHERE id=%s
    """ %(id_edital)
    linhas,total = executarSelect(consulta)
    assert total==1
    assert linhas[0][0]=="EDITAL DE TESTE AUTOMATIZADO"
    assert linhas[0][1]==token

def test_0_cadastrar_projeto():
    edital_teste = get_last_id('editais')
    titulo = id_generator(40)
    nome = str(id_generator(30)).upper()
    orientador = str(id_generator(20)).upper()
    csrf_token = get_csrf_token('/submissao')
    response = client.post("/cadastrarProjeto", data={
        "csrf_token": csrf_token,
        "destino": str(edital_teste),
        "tipo_trabalho": "0",
        "categoria_trabalho": "1",
        "tipo_apresentacao": "1",
        "autores": nome,
        "identificacao": "00000000000",
        "email": "email@email.com",
        "matriculas": "111111,222222,333333",
        "orientador": orientador,
        "unidade_academica": "CCT",
        "vinculo": "1",
        "tipo_vinculo": "1",
        "fomento": "1",
        "grande_area": "Ciências da Vida",
        "ods": "01",
        "area_cnpq": "CIÊNCIAS EXATAS E DA TERRA",
        "subarea_cnpq": "---",
        "projeto": "0",
        "titulo": titulo,
        "palavras": "android",
        "resumo": "Resumo do trabalho",
        "arquivo_trabalho": open(WORKING_DIR + "teste.pdf","rb"),
        "anais": "1",
        "acessibilidade": "1",
        "descricao_acessibilidade": "Necessita de interprete de Libras",
        "lingua": "1",
    },follow_redirects=True)
    assert response.status_code == 200
    consulta = """
    SELECT max(id) FROM editalProjeto
    """
    linhas,total=executarSelect(consulta)
    last_id = linhas[0][0]
    consulta = """
    SELECT nome,arquivo_projeto,categoria_trabalho,unidade,ods,acessibilidade,descricao_acessibilidade,lingua,
    vinculo,tipo_vinculo,fomento,area_cnpq,subarea_cnpq,anais,modalidade,categoria,matriculas
    FROM editalProjeto WHERE id=%s
    """ %(last_id)
    linhas,total = executarSelect(consulta)
    arquivo_projeto = linhas[0][1]
    nome_esperado = nome + ', ' + orientador
    assert linhas[0][0]==nome_esperado
    assert linhas[0][1]!="0"
    assert os.path.exists(ATTACHMENTS_DIR + arquivo_projeto)==True
    os.remove(ATTACHMENTS_DIR + arquivo_projeto)
    assert linhas[0][2]==1
    assert linhas[0][3]=="CCT"
    assert linhas[0][4]=="01"
    assert linhas[0][5]==1
    assert linhas[0][6]=="Necessita de interprete de Libras"
    assert linhas[0][7]==1
    assert linhas[0][8]==1
    assert linhas[0][9]==1
    assert linhas[0][10]==1
    assert linhas[0][11]=="CIÊNCIAS EXATAS E DA TERRA"
    assert linhas[0][12]=="---"
    assert linhas[0][13]==1
    assert linhas[0][14]==0
    assert linhas[0][15]==1
    assert linhas[0][16]=="111111,222222,333333"

def test_1_submissao_lista_em_submissoes():
    id_projeto = get_last_id('editalProjeto')
    consulta = """
    SELECT tipo,titulo FROM editalProjeto WHERE id=%s
    """ %(id_projeto)
    linhas,total = executarSelect(consulta)
    edital = linhas[0][0]
    titulo = linhas[0][1]
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    response = client.get('/submissoes/' + str(edital), follow_redirects=True, headers={"Authorization": "Basic " + valid_credentials})
    assert response.status_code == 200
    assert str.encode(titulo) in response.data

def test_2_inserir_avaliador():
    id_projeto = get_last_id('editalProjeto')
    edital = obterColunaUnica('editalProjeto','tipo','id',str(id_projeto))
    csrf_token = get_csrf_token('/avaliacoesNegadas?edital=' + str(edital) + '&id=' + str(id_projeto), auth_required=True)
    email = random_char(7)
    data = {
        "csrf_token": csrf_token,
        "txtProjeto": str(id_projeto),
        "txtEmail": email,
    }
    post_res('/inserirAvaliador', data)
    consulta = """
    SELECT avaliador,idProjeto,aceitou,token FROM avaliacoes WHERE avaliador='%s' AND idProjeto=%s
    """ %(email,id_projeto)
    linhas,total = executarSelect(consulta)
    assert total==1
    assert linhas[0][0]==email
    assert linhas[0][1]==int(id_projeto)
    assert linhas[0][2]==-1
    assert linhas[0][3]!=""

def test_3_pagina_avaliacao():
    id_projeto = get_last_id('editalProjeto')
    consulta = """
    SELECT token FROM avaliacoes WHERE idProjeto=%s
    """ %(id_projeto)
    linhas,total = executarSelect(consulta)
    token = linhas[0][0]
    response = client.get('/avaliacao?id=' + str(id_projeto) + '&token=' + token, follow_redirects=True)
    assert response.status_code == 200
    assert b'action="/cppgi/avaliar"' in response.data
    consulta = """
    SELECT aceitou FROM avaliacoes WHERE token='%s'
    """ %(token)
    linhas,total = executarSelect(consulta)
    assert linhas[0][0]==1

def test_4_avaliar():
    id_projeto = get_last_id('editalProjeto')
    consulta = """
    SELECT token FROM avaliacoes WHERE idProjeto=%s
    """ %(id_projeto)
    linhas,total = executarSelect(consulta)
    token = linhas[0][0]
    csrf_token = get_csrf_token('/avaliacao?id=' + str(id_projeto) + '&token=' + token)
    nome_avaliador = str(id_generator(20)).upper()
    comentarios = "Trabalho muito bem escrito e organizado."
    data = {
        "csrf_token": csrf_token,
        "token": token,
        "txtNome": nome_avaliador,
        "identificado": "0",
        "c1": "10",
        "c2": "10",
        "c3": "10",
        "c4": "10",
        "c5": "10",
        "c6": "10",
        "c7": "10",
        "c8": "10",
        "txtComentarios": comentarios,
        "txtRecomendacao": "1",
    }
    response = client.post('/avaliar', data=data, follow_redirects=True)
    assert response.status_code == 200
    consulta = """
    SELECT finalizado,recomendacao,nome_avaliador,comentario,c1,c2,c3,c4,c5,c6,c7,c8
    FROM avaliacoes WHERE token='%s'
    """ %(token)
    linhas,total = executarSelect(consulta)
    assert linhas[0][0]==1
    assert linhas[0][1]==1
    assert linhas[0][2]==nome_avaliador
    assert linhas[0][3]==comentarios
    assert linhas[0][4]==10
    assert linhas[0][5]==10
    assert linhas[0][6]==10
    assert linhas[0][7]==10
    assert linhas[0][8]==10
    assert linhas[0][9]==10
    assert linhas[0][10]==10
    assert linhas[0][11]==10

def test_5_remover_submissao_teste():
    id_projeto = get_last_id('editalProjeto')
    consulta = """
    SELECT arquivo_projeto,tipo FROM editalProjeto WHERE id=%s
    """ %(id_projeto)
    linhas,total = executarSelect(consulta)
    arquivo_projeto = linhas[0][0]
    edital_teste = linhas[0][1]
    consulta = """
    DELETE FROM editalProjeto WHERE id=%s
    """ %(id_projeto)
    atualizar(consulta)
    if os.path.exists(ATTACHMENTS_DIR + arquivo_projeto):
        os.remove(ATTACHMENTS_DIR + arquivo_projeto)
    consulta = """
    SELECT * FROM editalProjeto WHERE id=%s
    """ %(id_projeto)
    linhas,total = executarSelect(consulta)
    assert total==0
    consulta = """
    SELECT * FROM avaliacoes WHERE idProjeto=%s
    """ %(id_projeto)
    linhas,total = executarSelect(consulta)
    assert total==0
    consulta = """
    DELETE FROM editais WHERE id=%s
    """ %(edital_teste)
    atualizar(consulta)
    consulta = """
    SELECT * FROM editais WHERE id=%s
    """ %(edital_teste)
    linhas,total = executarSelect(consulta)
    assert total==0

