from pesquisa import app,executarSelect,config,WORKING_DIR,id_generator,atualizar,inserir,ATTACHMENTS_DIR,obterColunaUnica
import pytest
import base64
import os
import re
import datetime
import logging

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

def _garantir_usuario_teste(cpf, email, senha, verificado=1):
    linhas, total = executarSelect("SELECT id FROM users WHERE username=%s", 1, valores=(cpf,))
    if total == 0:
        inserir("""INSERT INTO users (username,password,nome,email,roles,permission,email_verificado)
                   VALUES (%s,%s,%s,%s,'user',1,%s)""",
                (cpf, senha, "USUARIO DE TESTE", email, verificado))
    else:
        atualizar("UPDATE users SET password=%s, email=%s, email_verificado=%s WHERE username=%s",
                  (senha, email, verificado, cpf))

def _cpf_aleatorio():
    return ''.join(random.choice(string.digits) for _ in range(11))

def test_0_cadastrar_projeto():
    edital_teste = get_last_id('editais')
    titulo = id_generator(40)
    nome = str(id_generator(30)).upper()
    orientador = str(id_generator(20)).upper()

    #/cadastrarProjeto agora exige sessão ativa: garante a conta e popula a sessão do cliente de teste
    _garantir_usuario_teste("00000000000", "email@email.com", "SenhaDeTesteForte1!")
    with client.session_transaction() as sess:
        sess['username'] = "00000000000"
        sess['cpf'] = "00000000000"
        sess['email'] = "email@email.com"
        sess['nome'] = "USUARIO DE TESTE"
        sess['permissao'] = 1
        sess['roles'] = ['user']

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
    csrf_token = get_csrf_token('/admin/avaliacoesNegadas?edital=' + str(edital) + '&id=' + str(id_projeto), auth_required=True)
    email = random_char(7)
    data = {
        "csrf_token": csrf_token,
        "txtProjeto": str(id_projeto),
        "txtEmail": email,
    }
    post_res('/admin/inserirAvaliador', data)
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
    atualizar("DELETE FROM users WHERE username=%s", ("00000000000",))

'''
**************************************************************
TESTES: autocadastro, sessão, credencial vazada (Cloudflare) e auditoria (@log_required)
**************************************************************
'''

def test_cadastro_senha_fraca():
    casos = [
        "Curta1!",                 #menos de 12 caracteres
        "senhalongasemmaiuscula1!", #falta maiúscula
        "SENHALONGASEMMINUSCULA1!", #falta minúscula
        "SenhaLongaSemNumero!!!!",   #falta número
        "SenhaLongaSemEspecial123", #falta caractere especial
    ]
    for senha in casos:
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/cadastro', data={
            "csrf_token": csrf_token,
            "cpf": _cpf_aleatorio(),
            "nome": "Fulano de Tal",
            "email": random_char(7),
            "senha": senha,
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'mínimo 12 caracteres'.encode() in response.data

def test_cadastro_cpf_e_email_duplicado():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/cadastro', data={
            "csrf_token": csrf_token,
            "cpf": cpf,
            "nome": "Fulano de Tal",
            "email": email,
            "senha": "SenhaDeTesteForte1!",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Cadastro realizado'.encode() in response.data

        #CPF já cadastrado: não cria segunda conta, mostra e-mail mascarado
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/cadastro', data={
            "csrf_token": csrf_token,
            "cpf": cpf,
            "nome": "Outro Nome",
            "email": random_char(7),
            "senha": "OutraSenhaForte1!",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'CPF já possui cadastro'.encode() in response.data
        assert email.encode() not in response.data #e-mail completo não pode vazar
        linhas, total = executarSelect("SELECT id FROM users WHERE username=%s", 1, valores=(cpf,))
        assert total == 1

        #E-mail já em uso por outro CPF: rejeitado, sem criar nova linha
        outro_cpf = _cpf_aleatorio()
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/cadastro', data={
            "csrf_token": csrf_token,
            "cpf": outro_cpf,
            "nome": "Mais Um",
            "email": email,
            "senha": "MaisUmaSenhaForte1!",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'e-mail já está em uso'.encode() in response.data
        linhas, total = executarSelect("SELECT id FROM users WHERE username=%s", 1, valores=(outro_cpf,))
        assert total == 0
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_cadastro_token_confirmacao():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        csrf_token = get_csrf_token('/cadastro')
        client.post('/cadastro', data={
            "csrf_token": csrf_token,
            "cpf": cpf,
            "nome": "Fulano de Tal",
            "email": email,
            "senha": "SenhaDeTesteForte1!",
        }, follow_redirects=True)

        #Token inválido não confirma
        response = client.get('/confirmarEmail/token-que-nao-existe', follow_redirects=True)
        assert response.status_code == 200
        assert 'inválido ou expirado'.encode() in response.data

        #Token expirado não confirma
        linhas, total = executarSelect("SELECT token_verificacao FROM users WHERE username=%s", 1, valores=(cpf,))
        token = linhas[0]
        atualizar("UPDATE users SET token_verificacao_expira=%s WHERE username=%s",
                  (datetime.datetime.now() - datetime.timedelta(hours=1), cpf))
        response = client.get('/confirmarEmail/' + token, follow_redirects=True)
        assert response.status_code == 200
        assert 'Enviamos um novo link'.encode() in response.data
        linhas, total = executarSelect("SELECT email_verificado, token_verificacao FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 0
        assert linhas[1] != token

        #O token antigo deixa de valer após o reenvio
        response = client.get('/confirmarEmail/' + token, follow_redirects=True)
        assert 'inválido ou expirado'.encode() in response.data
        token = linhas[1]

        #Token válido confirma, e um segundo acesso (ex.: filtro de e-mail abriu o link antes) não exibe erro
        response = client.get('/confirmarEmail/' + token, follow_redirects=True)
        assert response.status_code == 200
        assert 'confirmado com sucesso'.encode() in response.data
        linhas, total = executarSelect("SELECT email_verificado FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 1

        response = client.get('/confirmarEmail/' + token, follow_redirects=True)
        assert response.status_code == 200
        assert 'já está confirmado'.encode() in response.data
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_login_bloqueado_email_nao_verificado():
    cpf = _cpf_aleatorio()
    try:
        #Requisições Basic Auth de testes anteriores (get_res/post_res) deixam sessão de admin
        #residual no cliente de teste compartilhado; limpa antes de checar o bloqueio isoladamente.
        with client.session_transaction() as sess:
            sess.clear()
        _garantir_usuario_teste(cpf, random_char(7), "SenhaDeTesteForte1!", verificado=0)
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/login', data={
            "csrf_token": csrf_token,
            "siape": cpf,
            "senha": "SenhaDeTesteForte1!",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Confirme seu e-mail'.encode() in response.data
        with client.session_transaction() as sess:
            assert 'username' not in sess
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_sessao_login_e_logout():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/login', data={
            "csrf_token": csrf_token,
            "siape": cpf,
            "senha": "SenhaDeTesteForte1!",
        }, follow_redirects=True)
        assert response.status_code == 200
        with client.session_transaction() as sess:
            assert sess['cpf'] == cpf
            assert sess['email'] == email
            assert sess['nome'] == "USUARIO DE TESTE"

        client.get('/logout', follow_redirects=True)
        with client.session_transaction() as sess:
            assert 'cpf' not in sess
            assert 'email' not in sess
            assert 'username' not in sess
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_submissao_sem_sessao():
    #Regressão: /submissao (GET, exibe o formulário de cadastrarProjeto) não tinha checagem de
    #autenticação — só o POST em /cadastrarProjeto tinha, deixando o formulário visível (com
    #campos de CPF/e-mail vazios) para quem não estava logado.
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get('/submissao', follow_redirects=True)
    assert response.status_code == 200
    assert 'necessário autenticação'.encode() in response.data
    assert b'name="identificacao"' not in response.data

def test_submissao_preenche_cpf_email_da_sessao():
    #Com sessão ativa, o formulário deve mostrar o CPF e o e-mail do usuário logado
    #(pré-preenchidos a partir da sessão), não campos vazios/manuais.
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        with client.session_transaction() as sess:
            sess['username'] = cpf
            sess['cpf'] = cpf
            sess['email'] = email
            sess['nome'] = "USUARIO DE TESTE"
        response = client.get('/submissao', follow_redirects=True)
        assert response.status_code == 200
        assert ('value="' + cpf + '"').encode() in response.data
        assert ('value="' + email + '"').encode() in response.data
        with client.session_transaction() as sess:
            sess.clear()
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_cadastrarProjeto_sem_sessao():
    with client.session_transaction() as sess:
        sess.clear()
    csrf_token = get_csrf_token('/submissao')
    response = client.post('/cadastrarProjeto', data={
        "csrf_token": csrf_token,
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'necessário autenticação'.encode() in response.data

def test_senha_fraca_forca_troca_senha():
    #Conta "legada" com senha fraca (não passaria mais na regra de senha forte hoje) — o login
    #ainda deve funcionar (a senha em si está correta), mas deve forçar a troca, no mesmo
    #mecanismo usado para credencial vazada.
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "fraca123", verificado=1)
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/login', data={
            "csrf_token": csrf_token,
            "siape": cpf,
            "senha": "fraca123",
        }, follow_redirects=True)
        assert response.status_code == 200

        linhas, total = executarSelect("SELECT forcar_troca_senha FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 1

        response = client.get('/meusProjetos', follow_redirects=False)
        assert response.status_code == 302
        assert '/trocarSenhaObrigatoria' in response.headers['Location']

        client.get('/logout', follow_redirects=True)
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_credencial_vazada_forca_troca_senha():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        csrf_token = get_csrf_token('/cadastro')
        response = client.post('/login', data={
            "csrf_token": csrf_token,
            "siape": cpf,
            "senha": "SenhaDeTesteForte1!",
        }, headers={"Exposed-Credential-Check": "1"}, follow_redirects=True)
        assert response.status_code == 200

        linhas, total = executarSelect("SELECT forcar_troca_senha FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 1

        #Middleware bloqueia qualquer rota e redireciona para a troca obrigatória
        response = client.get('/meusProjetos', follow_redirects=False)
        assert response.status_code == 302
        assert '/trocarSenhaObrigatoria' in response.headers['Location']

        response = client.get('/usuario', follow_redirects=False)
        assert response.status_code == 302
        assert '/trocarSenhaObrigatoria' in response.headers['Location']

        #A própria tela de troca continua acessível, sem loop
        response = client.get('/trocarSenhaObrigatoria', follow_redirects=True)
        assert response.status_code == 200
        assert 'Troca de senha obrigatória'.encode() in response.data

        #Trocar a senha libera o acesso normal na mesma sessão
        csrf_token = get_csrf_token('/trocarSenhaObrigatoria')
        response = client.post('/trocarSenhaObrigatoria', data={
            "csrf_token": csrf_token,
            "senha": "NovaSenhaForte9!",
        }, follow_redirects=True)
        assert response.status_code == 200

        linhas, total = executarSelect("SELECT forcar_troca_senha FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 0

        response = client.get('/meusProjetos', follow_redirects=False)
        assert response.status_code == 200

        client.get('/logout', follow_redirects=True)
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def _login_teste(cpf, senha):
    csrf_token = get_csrf_token('/cadastro')
    response = client.post('/login', data={
        "csrf_token": csrf_token,
        "siape": cpf,
        "senha": senha,
    }, follow_redirects=True)
    assert response.status_code == 200

def test_trocarSenha_sem_sessao():
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get('/trocarSenha', follow_redirects=True)
    assert response.status_code == 200
    assert 'necessário autenticação'.encode() in response.data

def test_trocarSenha_senha_atual_incorreta():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        _login_teste(cpf, "SenhaDeTesteForte1!")

        csrf_token = get_csrf_token('/trocarSenha')
        response = client.post('/trocarSenha', data={
            "csrf_token": csrf_token,
            "senha_atual": "SenhaErrada999!",
            "nova_senha": "OutraSenhaForte2!",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Senha atual incorreta'.encode() in response.data

        linhas, total = executarSelect("SELECT password FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == "SenhaDeTesteForte1!"

        client.get('/logout', follow_redirects=True)
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_trocarSenha_nova_senha_fraca():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        _login_teste(cpf, "SenhaDeTesteForte1!")

        csrf_token = get_csrf_token('/trocarSenha')
        response = client.post('/trocarSenha', data={
            "csrf_token": csrf_token,
            "senha_atual": "SenhaDeTesteForte1!",
            "nova_senha": "fraca",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'mínimo 12 caracteres'.encode() in response.data

        linhas, total = executarSelect("SELECT password FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == "SenhaDeTesteForte1!"

        client.get('/logout', follow_redirects=True)
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_trocarSenha_sucesso():
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        _login_teste(cpf, "SenhaDeTesteForte1!")

        csrf_token = get_csrf_token('/trocarSenha')
        response = client.post('/trocarSenha', data={
            "csrf_token": csrf_token,
            "senha_atual": "SenhaDeTesteForte1!",
            "nova_senha": "NovaSenhaForte9!",
        }, follow_redirects=True)
        assert response.status_code == 200

        linhas, total = executarSelect("SELECT password,forcar_troca_senha FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == "NovaSenhaForte9!"
        assert linhas[1] == 0

        #A nova senha já funciona para logar de novo
        client.get('/logout', follow_redirects=True)
        _login_teste(cpf, "NovaSenhaForte9!")
        client.get('/logout', follow_redirects=True)
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_trocarSenha_credencial_vazada_bloqueia_e_forca_troca():
    #Mesma checagem de credencial vazada usada no login também vale para a troca voluntária:
    #não permite definir a nova senha e força o usuário para o fluxo de troca obrigatória.
    cpf = _cpf_aleatorio()
    email = random_char(7)
    try:
        _garantir_usuario_teste(cpf, email, "SenhaDeTesteForte1!", verificado=1)
        _login_teste(cpf, "SenhaDeTesteForte1!")

        csrf_token = get_csrf_token('/trocarSenha')
        response = client.post('/trocarSenha', data={
            "csrf_token": csrf_token,
            "senha_atual": "SenhaDeTesteForte1!",
            "nova_senha": "OutraSenhaForte2!",
        }, headers={"Exposed-Credential-Check": "1"}, follow_redirects=True)
        assert response.status_code == 200
        assert 'comprometida'.encode() in response.data

        linhas, total = executarSelect("SELECT password,forcar_troca_senha FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == "SenhaDeTesteForte1!" #senha NÃO foi trocada
        assert linhas[1] == 1

        response = client.get('/meusProjetos', follow_redirects=False)
        assert response.status_code == 302
        assert '/trocarSenhaObrigatoria' in response.headers['Location']

        client.get('/logout', follow_redirects=True)
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_log_required_grava_auditoria(caplog):
    #logger_auditoria tem propagate=False em produção (não duplicar em app.log); religa
    #temporariamente só para o caplog conseguir capturar via propagação até a raiz.
    logger_auditoria = logging.getLogger('auditoria_acessos')
    logger_auditoria.propagate = True
    try:
        with caplog.at_level(logging.INFO, logger='auditoria_acessos'):
            #sem parâmetros a rota responde 400, mas passa pelo @log_required antes: basta para auditar
            credenciais = base64.b64encode(usuario_senha).decode("utf-8")
            aplicacao.get('/admin/avaliacoesNegadas', headers={"Authorization": "Basic " + credenciais})
    finally:
        logger_auditoria.propagate = False
    mensagens = [r.message for r in caplog.records if r.name == 'auditoria_acessos']
    assert any('rota=/admin/avaliacoesNegadas' in m and 'metodo=GET' in m for m in mensagens)
    #CPF nunca deve aparecer em texto puro no log de auditoria
    assert not any(usuario in m for m in mensagens)
    assert any(re.search(r'cpf=\d{3}\*+\d{2}\b', m) for m in mensagens)
    #ID numérico do usuário deve estar presente no log
    id_usuario = obterColunaUnica('users', 'id', 'username', usuario)
    assert any(('user_id=' + str(id_usuario)) in m for m in mensagens)

def test_pagina_seguranca():
    response = client.get('/seguranca', follow_redirects=True)
    assert response.status_code == 200
    assert 'Leaked/Exposed Credential Checks'.encode() in response.data
    assert 'Política de senha forte'.encode() in response.data

def test_guardrail_log_required_em_rotas_login_required():
    caminho = WORKING_DIR + 'pesquisa.py'
    with open(caminho, encoding='utf-8') as f:
        linhas_arquivo = f.readlines()
    faltando = []
    for i, linha in enumerate(linhas_arquivo):
        if linha.strip().startswith('@auth.login_required('):
            proxima = linhas_arquivo[i + 1].strip() if i + 1 < len(linhas_arquivo) else ''
            if proxima != '@log_required':
                faltando.append(i + 1)
    assert faltando == [], "Rotas com @auth.login_required sem @log_required nas linhas: %s" % faltando

def test_login_get_renderiza_formulario():
    #Regressão: o link "Entrar" do layout faz GET em /login; a rota precisa aceitar GET
    #além de POST, senão o clique resulta em "405 Method Not Allowed".
    response = client.get('/login', follow_redirects=True)
    assert response.status_code == 200
    assert 'Autenticação'.encode() in response.data

def test_login_tem_link_criar_conta():
    response = client.get('/login', follow_redirects=True)
    assert response.status_code == 200
    assert b'href="/cadastro"' in response.data
    assert 'Criar conta'.encode() in response.data

def test_link_login_logout_no_layout():
    #Nota: em produção (waitress com url_prefix='/cppgi') os links renderizam com esse prefixo;
    #sob app.test_client() o prefixo não é aplicado, então checamos os caminhos sem ele aqui.
    #Sem sessão: mostra Entrar/Cadastre-se, não mostra logout
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get('/submissao', follow_redirects=True)
    assert response.status_code == 200
    assert b'href="/login"' in response.data
    assert b'href="/cadastro"' in response.data
    assert b'href="/logout"' not in response.data

    #Com sessão: mostra logout, não mostra Entrar/Cadastre-se
    cpf = _cpf_aleatorio()
    try:
        _garantir_usuario_teste(cpf, random_char(7), "SenhaDeTesteForte1!", verificado=1)
        with client.session_transaction() as sess:
            sess['username'] = cpf
            sess['cpf'] = cpf
            sess['nome'] = "USUARIO DE TESTE"
        response = client.get('/submissao', follow_redirects=True)
        assert response.status_code == 200
        assert b'href="/logout"' in response.data
        assert b'href="/login"' not in response.data
        with client.session_transaction() as sess:
            sess.clear()
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))


'''
**************************************************************
TESTES: cadastro/edição de editais e janela de submissão (inicio_submissao)
**************************************************************
'''

def _form_edital(nome, inicio, deadline):
    formato = '%Y-%m-%dT%H:%M'
    return {'nome_curto': "TESTE D'EDITAL", 'nome': nome, 'nome_longo': "CONGRESSO D'ÁGUA", 'periodo': '1 a 5',
            'local': 'Juazeiro do Norte', 'situacao': 'N/A', 'isbn': '123', 'logo': 'logo_cppgi.jpg',
            'ficha': 'cppgi_ficha.png', 'mensagem': "Resultado d'água",
            'inicio_submissao': inicio.strftime(formato), 'deadline': deadline.strftime(formato),
            'deadline_avaliacao': deadline.strftime(formato), 'deadline_versao_final': deadline.strftime(formato),
            'deadline_apresentacao': deadline.strftime(formato)}

def test_cadastrar_editar_edital():
    from pesquisa import editalAbertoParaSubmissao, getEditaisAbertos
    nome = "EDITAL D'TESTE " + id_generator(10)
    agora = datetime.datetime.now()
    dados = _form_edital(nome, agora - datetime.timedelta(days=1), agora + datetime.timedelta(days=10))
    dados['csrf_token'] = get_csrf_token('/admin/cadastrar_edital', auth_required=True)
    post_res('/admin/cadastrar_edital', dados)
    linhas, total = executarSelect("SELECT id,periodo,local,mensagem,nome_longo FROM editais WHERE nome=%s", valores=(nome,))
    assert len(linhas) == 1
    id_edital = linhas[0][0]
    try:
        assert linhas[0][1:] == ('1 a 5', 'Juazeiro do Norte', "Resultado d'água", "CONGRESSO D'ÁGUA")
        assert editalAbertoParaSubmissao(id_edital)
        assert id_edital in [e[0] for e in getEditaisAbertos()]

        # início no futuro: some da lista de abertos e a submissão é recusada
        dados = _form_edital(nome, agora + datetime.timedelta(days=2), agora + datetime.timedelta(days=10))
        dados['periodo'] = '6 a 9'
        dados['csrf_token'] = get_csrf_token('/admin/editar_edital/%s' % id_edital, auth_required=True)
        post_res('/admin/editar_edital/%s' % id_edital, dados)
        linhas, total = executarSelect("SELECT periodo FROM editais WHERE id=%s", valores=(id_edital,))
        assert linhas[0][0] == '6 a 9'
        assert not editalAbertoParaSubmissao(id_edital)
        assert id_edital not in [e[0] for e in getEditaisAbertos()]

        # deadline vencido também fecha a janela
        atualizar("UPDATE editais SET inicio_submissao=%s, deadline=%s WHERE id=%s",
                  (agora - datetime.timedelta(days=10), agora - datetime.timedelta(days=1), id_edital))
        assert not editalAbertoParaSubmissao(id_edital)
    finally:
        atualizar("DELETE FROM editais WHERE id=%s", (id_edital,))

def test_cadastrar_edital_inicio_depois_do_deadline():
    nome = "EDITAL INVALIDO " + id_generator(10)
    agora = datetime.datetime.now()
    dados = _form_edital(nome, agora + datetime.timedelta(days=5), agora + datetime.timedelta(days=1))
    dados['csrf_token'] = get_csrf_token('/admin/cadastrar_edital', auth_required=True)
    rv = post_res('/admin/cadastrar_edital', dados)
    assert u'deve ser anterior' in rv.data.decode()
    linhas, total = executarSelect("SELECT id FROM editais WHERE nome=%s", valores=(nome,))
    assert len(linhas) == 0

def test_listar_editais():
    get_res('/admin/editais')

'''
**************************************************************
TESTES: fluxo do avaliador (reenvio, prazo) e certificados em memória
**************************************************************
'''

def _criar_avaliacao_temporaria(modelo_declaracao=''):
    """Edital (avaliação aberta) + trabalho + avaliação não finalizada. Devolve (edital, projeto, token)."""
    agora = datetime.datetime.now()
    token_edital = id_generator(40)
    inserir("""INSERT INTO editais (nome,nome_longo,deadline,deadline_avaliacao,deadline_apresentacao,deadline_versao_final,
               setor,mensagem,token,declaracao_avaliador) VALUES ('EDITAL AVALIACAO TMP','EDITAL AVALIACAO TMP',%s,%s,%s,%s,1,'',%s,%s)""",
            (agora - datetime.timedelta(days=5), agora + datetime.timedelta(days=10), agora + datetime.timedelta(days=30),
             agora + datetime.timedelta(days=20), token_edital, modelo_declaracao))
    edital = executarSelect("SELECT id FROM editais WHERE token=%s", 1, valores=(token_edital,))[0][0]
    titulo = 'TRABALHO TMP ' + id_generator(10)
    inserir("""INSERT INTO editalProjeto (tipo,categoria,modalidade,nome,siape,email,ua,titulo,palavras,resumo,
               arquivo_projeto,arquivo_plano1,arquivo_plano2) VALUES (%s,1,2,'AUTOR TMP','0','x@x','UA',%s,'p','r','TRABALHO.tmp.pdf','','')""",
            (edital, titulo))
    projeto = executarSelect("SELECT id FROM editalProjeto WHERE titulo=%s", 1, valores=(titulo,))[0][0]
    token = id_generator(20)
    inserir("INSERT INTO avaliacoes (idProjeto,token,avaliador,finalizado,aceitou) VALUES (%s,%s,'avaliador@teste.local',0,-1)",
            (projeto, token))
    return edital, projeto, token

def _remover_avaliacao_temporaria(edital, projeto):
    atualizar("DELETE FROM avaliacoes WHERE idProjeto=%s", (projeto,))
    atualizar("DELETE FROM editalProjeto WHERE id=%s", (projeto,))
    atualizar("DELETE FROM editais WHERE id=%s", (edital,))

def _dados_avaliacao(token, csrf_token, nota):
    dados = {"csrf_token": csrf_token, "token": token, "txtNome": "AVALIADOR TMP", "identificado": "0",
             "txtComentarios": "Comentário de teste", "txtRecomendacao": "1"}
    dados.update({"c%d" % i: str(nota) for i in range(1, 9)})
    return dados

def test_avaliar_nao_regrava_avaliacao_finalizada():
    edital, projeto, token = _criar_avaliacao_temporaria()
    try:
        csrf_token = get_csrf_token('/avaliacao?token=' + token)
        client.post('/avaliar', data=_dados_avaliacao(token, csrf_token, 9))
        rv = client.post('/avaliar', data=_dados_avaliacao(token, csrf_token, 1))
        assert u'já foi avaliado' in rv.data.decode()
        linhas, total = executarSelect("SELECT finalizado,c1,c8 FROM avaliacoes WHERE token=%s", valores=(token,))
        assert linhas[0] == (1, 9, 9)
    finally:
        _remover_avaliacao_temporaria(edital, projeto)

def test_avaliar_fora_do_prazo():
    edital, projeto, token = _criar_avaliacao_temporaria()
    try:
        csrf_token = get_csrf_token('/avaliacao?token=' + token)
        atualizar("UPDATE editais SET deadline_avaliacao=%s WHERE id=%s",
                  (datetime.datetime.now() - datetime.timedelta(days=1), edital))
        rv = client.post('/avaliar', data=_dados_avaliacao(token, csrf_token, 9))
        assert u'Prazo de avaliação expirado' in rv.data.decode()
        linhas, total = executarSelect("SELECT finalizado FROM avaliacoes WHERE token=%s", valores=(token,))
        assert linhas[0][0] == 0
    finally:
        _remover_avaliacao_temporaria(edital, projeto)

def test_declaracao_avaliador_nao_finalizada_e_sem_modelo():
    edital, projeto, token = _criar_avaliacao_temporaria(modelo_declaracao='')
    try:
        rv = client.get('/declaracaoAvaliador?token=' + token)
        assert rv.status_code == 403
        atualizar("UPDATE avaliacoes SET finalizado=1 WHERE token=%s", (token,))
        rv = client.get('/declaracaoAvaliador?token=' + token)
        assert rv.status_code == 404
        assert u'modelo de certificado' in rv.data.decode()
        assert client.get('/declaracaoAvaliador?token=inexistente').status_code == 404
    finally:
        _remover_avaliacao_temporaria(edital, projeto)

def test_declaracao_avaliador_pdf_em_memoria():
    from PIL import Image
    from pesquisa import CERTIFICADOS_TEMPLATE_DIR
    modelo = 'modelo_teste_' + id_generator(8) + '.png'
    Image.new('RGB', (40, 30), 'white').save(CERTIFICADOS_TEMPLATE_DIR + modelo)
    arquivos_fixos = [app.config['CERTIFICADOS_FOLDER'] + 'certificado.pdf', CERTIFICADOS_TEMPLATE_DIR + 'qrcode.png']
    antes = {a: os.path.getmtime(a) if os.path.exists(a) else None for a in arquivos_fixos}
    edital, projeto, token = _criar_avaliacao_temporaria(modelo_declaracao=modelo)
    try:
        atualizar("UPDATE avaliacoes SET finalizado=1, nome_avaliador='AVALIADOR TMP' WHERE token=%s", (token,))
        rv = client.get('/declaracaoAvaliador?token=' + token)
        assert rv.status_code == 200
        assert rv.mimetype == 'application/pdf'
        assert rv.data[:4] == b'%PDF'
        depois = {a: os.path.getmtime(a) if os.path.exists(a) else None for a in arquivos_fixos}
        assert depois == antes
    finally:
        _remover_avaliacao_temporaria(edital, projeto)
        os.remove(CERTIFICADOS_TEMPLATE_DIR + modelo)

#Funções que montam SQL só com identificadores fixos no código (ou trechos de "%s"), ou que ficaram fora da
#parametrização por decisão explícita (rotas genéricas salvar/detalhes). Valores de usuário NUNCA entram por concatenação.
EXCECOES_SQL_DINAMICO = {
    ('pesquisa.py', 'obterColunaUnica'),            #identificadores fixos nas chamadas; valor via %s
    ('pesquisa.py', 'salvar'),                      #rota genérica mantida como está (decisão do usuário)
    ('pesquisa.py', 'cadastrar_edital'),            #colunas de CAMPOS_EDITAL
    ('pesquisa.py', 'editar_edital'),
    ('pesquisa.py', '_salvar_modelos_certificado'), #colunas de CERTIFICADOS_EDITAL
    ('pesquisa.py', '_obter_edital'),
    ('app_api.py', 'consultar'),                    #concatena o trecho de filtros_modalidade_area (só %s)
    ('app_api.py', 'totais'),
}

def _sql_dinamico(caminho):
    import ast
    sql = re.compile(r'\b(SELECT|UPDATE|INSERT|DELETE)\b', re.I)
    def literal_sql(n):
        return any(isinstance(x, ast.Constant) and isinstance(x.value, str) and sql.search(x.value) for x in ast.walk(n))
    def seguro(n):
        #",".join(["%s"]*len(itens)): placeholders para IN (...)
        if isinstance(n, ast.Constant):
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'join':
            return all(x.value == '%s' for x in ast.walk(n) if isinstance(x, ast.Constant) and isinstance(x.value, str) and x.value.strip(',') != '')
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            return seguro(n.left) and seguro(n.right)
        return False
    arvore = ast.parse(open(caminho, encoding='utf-8').read())
    achados = []
    for funcao in ast.walk(arvore):
        if not isinstance(funcao, ast.FunctionDef):
            continue
        for n in ast.walk(funcao):
            if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)) and literal_sql(n):
                if isinstance(n.op, ast.Mod) or not (seguro(n.left) and seguro(n.right)):
                    achados.append((os.path.basename(caminho), funcao.name, n.lineno))
            elif isinstance(n, ast.JoinedStr) and literal_sql(n):
                achados.append((os.path.basename(caminho), funcao.name, n.lineno))
    return achados

def test_guardrail_sql_sem_concatenacao():
    achados = []
    for arquivo in ('pesquisa.py', 'app_api.py'):
        achados += [a for a in _sql_dinamico(WORKING_DIR + arquivo) if (a[0], a[1]) not in EXCECOES_SQL_DINAMICO]
    assert achados == [], "SQL montado por concatenação/format (use %%s + valores): %s" % sorted(set(achados))

'''
**************************************************************
TESTES: correções de bugs pré-existentes (certificado individual, notasApresentacoes, cruzarDados,
distribuirSalas sem sala de pôster, avaliacoesNegadas)
**************************************************************
'''

def _auth_headers():
    return {"Authorization": "Basic " + base64.b64encode(usuario_senha).decode("utf-8")}

def test_certificado_individual_grava_token_na_tabela_certa():
    from PIL import Image
    from pesquisa import CERTIFICADOS_TEMPLATE_DIR
    modelo = 'modelo_teste_' + id_generator(8) + '.png'
    Image.new('RGB', (40, 30), 'white').save(CERTIFICADOS_TEMPLATE_DIR + modelo)
    edital, projeto, token = _criar_avaliacao_temporaria()
    try:
        atualizar("UPDATE editais SET certificado_demais=%s WHERE id=%s", (modelo, edital))
        inserir("INSERT INTO certificados_moderador (edital,nome,tipo,token) VALUES (%s,'MODERADOR TMP','moderou','0')", (edital,))
        id_certificado = executarSelect("SELECT max(id) FROM certificados_moderador WHERE edital=%s", 1, valores=(edital,))[0][0]
        #trabalho com o mesmo id do certificado: o bug antigo sobrescrevia o token dele
        token_trabalho_antes = obterColunaUnica('editalProjeto', 'token', 'id', str(id_certificado))
        rv = client.get('/baixarCertificadoIndividual/%s' % id_certificado)
        assert rv.status_code == 200 and rv.mimetype == 'application/pdf'
        token_certificado = obterColunaUnica('certificados_moderador', 'token', 'id', str(id_certificado))
        assert token_certificado not in ('0', '')
        assert obterColunaUnica('editalProjeto', 'token', 'id', str(id_certificado)) == token_trabalho_antes
        #segunda emissão reaproveita o mesmo token (antes era regenerado a cada download)
        client.get('/baixarCertificadoIndividual/%s' % id_certificado)
        assert obterColunaUnica('certificados_moderador', 'token', 'id', str(id_certificado)) == token_certificado
    finally:
        atualizar("DELETE FROM certificados_moderador WHERE edital=%s", (edital,))
        _remover_avaliacao_temporaria(edital, projeto)
        os.remove(CERTIFICADOS_TEMPLATE_DIR + modelo)

def test_notas_apresentacoes_exige_admin():
    assert client.get('/admin/notasApresentacoes/1').status_code == 401
    rv = client.get('/notasApresentacoes/1')
    assert rv.status_code == 308 and rv.headers['Location'].endswith('/admin/notasApresentacoes/1')

def test_cruzar_dados_removida():
    assert client.get('/cruzarDados?ano=2026').status_code == 404

def test_distribuir_salas_sem_sala_de_poster():
    edital, projeto, token = _criar_avaliacao_temporaria()
    try:
        atualizar("UPDATE editalProjeto SET categoria=1, situacao=1 WHERE id=%s", (projeto,))
        rv = client.get('/admin/distribuirSalas?edital=%s' % edital, headers=_auth_headers(), follow_redirects=True)
        assert rv.status_code == 200
        assert u'cadastre uma sala do tipo pôster' in rv.data.decode()
    finally:
        _remover_avaliacao_temporaria(edital, projeto)

def test_avaliacoes_negadas_parametros():
    rv = client.get('/admin/avaliacoesNegadas?edital=1', headers=_auth_headers())
    assert rv.status_code == 400
    assert b'SELECT' not in rv.data
    edital, projeto, token = _criar_avaliacao_temporaria()
    try:
        assert client.get('/admin/avaliacoesNegadas?edital=%s&id=%s' % (edital, projeto), headers=_auth_headers()).status_code == 200
        rv = client.get('/admin/avaliacoesNegadas?edital=%s&id=%s' % (edital + 1, projeto), headers=_auth_headers())
        assert rv.status_code == 404
    finally:
        _remover_avaliacao_temporaria(edital, projeto)

'''
**************************************************************
TESTES: admin "acessar como" outro usuário e "voltar para admin"
**************************************************************
'''

def _usuario_comum_temporario():
    cpf = str(random.randint(10**10, 10**11 - 1))
    _garantir_usuario_teste(cpf, cpf + '@teste.local', 'Senha#Forte123', 1)
    return cpf, int(obterColunaUnica('users', 'id', 'username', cpf))

def _csrf_admin(c):
    rv = c.get('/admin/cadastrar_usuario/1', headers=_auth_headers())
    return re.search(r'name="csrf_token" value="([^"]+)"', rv.data.decode()).group(1)

def test_acessar_como_e_voltar_admin(caplog):
    c = app.test_client()
    H = _auth_headers()
    cpf, id_alvo = _usuario_comum_temporario()
    logger_auditoria = logging.getLogger('auditoria_acessos')
    try:
        csrf = _csrf_admin(c)
        rv = c.get('/admin/cadastrar_usuario/1', headers=H)
        assert ('acessarComo/%d' % id_alvo) in rv.data.decode()
        rv = c.post('/admin/acessarComo/%d' % id_alvo, headers=H, data={'csrf_token': csrf})
        assert rv.status_code == 302
        with c.session_transaction() as s:
            assert s['username'] == cpf
            assert s['impersonador']['username'] == usuario
        #rota de sessão: age como o usuário, com a faixa de aviso
        rv = c.get('/meusProjetos', headers=H)
        assert rv.status_code == 200 and u'Voltar para admin' in rv.data.decode()
        #rota admin com o HTTP Basic do admin: papéis do usuário acessado (403) e a sessão NÃO volta para o admin
        logger_auditoria.propagate = True
        with caplog.at_level(logging.INFO, logger='auditoria_acessos'):
            assert c.get('/admin/editais', headers=H).status_code == 403
            c.get('/minhasIndicacoes', headers=H) #rota do usuário com @log_required
        logger_auditoria.propagate = False
        with c.session_transaction() as s:
            assert s['username'] == cpf
            id_admin = s['impersonador']['user_id']
        assert any(('impersonador_id=%s' % id_admin) in r.message for r in caplog.records if r.name == 'auditoria_acessos')
        #voltar para admin
        rv = c.post('/voltarAdmin', headers=H, data={'csrf_token': csrf})
        assert rv.status_code == 302
        with c.session_transaction() as s:
            assert s['username'] == usuario and 'impersonador' not in s
        assert c.get('/admin/editais', headers=H).status_code == 200
    finally:
        logger_auditoria.propagate = False
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

def test_acessar_como_recusa_admin_e_nao_aninha():
    c = app.test_client()
    H = _auth_headers()
    cpf, id_alvo = _usuario_comum_temporario()
    try:
        csrf = _csrf_admin(c)
        id_admin = int(obterColunaUnica('users', 'id', 'username', usuario))
        c.post('/admin/acessarComo/%d' % id_admin, headers=H, data={'csrf_token': csrf})
        with c.session_transaction() as s:
            assert s['username'] == usuario and 'impersonador' not in s
        assert c.post('/admin/acessarComo/999999999', headers=H, data={'csrf_token': csrf}).status_code == 404
        #voltarAdmin sem acesso ativo: só redireciona
        assert c.post('/voltarAdmin', data={'csrf_token': csrf}).status_code == 302
        #login explícito durante o acesso-como encerra o acesso
        c.post('/admin/acessarComo/%d' % id_alvo, headers=H, data={'csrf_token': csrf})
        c.post('/login', data={'csrf_token': csrf, 'siape': cpf, 'senha': 'Senha#Forte123'})
        with c.session_transaction() as s:
            assert s['username'] == cpf and 'impersonador' not in s
    finally:
        atualizar("DELETE FROM users WHERE username=%s", (cpf,))

'''
**************************************************************
TESTES: /enviar_arquivo com URL pré-assinada do S3 (S3 falso via monkeypatch, sem credenciais AWS)
**************************************************************
'''

class _S3Falso:
    def __init__(self, existe=True):
        self.existe = existe
        self.chamadas = []
    def head_object(self, Bucket, Key):
        self.chamadas.append(('head_object', Key))
        if not self.existe:
            from botocore.exceptions import ClientError
            raise ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, 'HeadObject')
        return {}
    def generate_presigned_url(self, operacao, Params, ExpiresIn):
        self.chamadas.append(('presigned', operacao, Params, ExpiresIn))
        return 'https://s3.exemplo/' + Params['Key'] + '?X-Amz-Expires=' + str(ExpiresIn)

def test_enviar_arquivo_local_nao_consulta_s3(monkeypatch):
    import pesquisa
    falso = _S3Falso()
    monkeypatch.setattr(pesquisa, 's3', falso)
    nome = 'TESTE.' + id_generator(10) + '.pdf'
    with open(ATTACHMENTS_DIR + nome, 'wb') as f:
        f.write(b'%PDF-teste')
    try:
        rv = client.get('/enviar_arquivo/' + nome)
        assert rv.status_code == 200 and rv.data == b'%PDF-teste'
        assert falso.chamadas == []
    finally:
        os.remove(ATTACHMENTS_DIR + nome)

def test_enviar_arquivo_redireciona_para_url_assinada(monkeypatch):
    import pesquisa
    falso = _S3Falso(existe=True)
    monkeypatch.setattr(pesquisa, 's3', falso)
    nome = 'TRABALHO.' + id_generator(10) + '.pdf'
    rv = client.get('/enviar_arquivo/' + nome)
    assert rv.status_code == 302
    assert rv.headers['Location'].startswith('https://s3.exemplo/cppgi/uploads/' + nome)
    assert rv.headers['Cache-Control'] == 'no-store'
    _, operacao, params, expira = falso.chamadas[-1]
    assert operacao == 'get_object' and expira == 60
    assert params['Key'] == 'cppgi/uploads/' + nome
    assert params['ResponseContentType'] == 'application/pdf'

def test_enviar_arquivo_inexistente_e_path_traversal(monkeypatch):
    import pesquisa
    falso = _S3Falso(existe=False)
    monkeypatch.setattr(pesquisa, 's3', falso)
    rv = client.get('/enviar_arquivo/NAOEXISTE.pdf')
    assert rv.status_code == 404 and u'Arquivo não encontrado' in rv.data.decode()
    #"..%2F..%2Fpesquisa.py" vira "pesquisa.py" (secure_filename): não sai de uploads/
    falso.chamadas.clear()
    rv = client.get('/enviar_arquivo/..%2F..%2Fpesquisa.py')
    assert rv.status_code == 404
    assert all(ch[1] == 'cppgi/uploads/pesquisa.py' for ch in falso.chamadas if ch[0] == 'head_object')

def test_uploadCR_envia_versao_final_ao_s3(monkeypatch):
    import io, pesquisa
    enviados = []
    monkeypatch.setattr(pesquisa, 'PRODUCAO', 1)
    monkeypatch.setattr(pesquisa, 'upload_s3', lambda origem, destino: enviados.append(destino))
    edital, projeto, token = _criar_avaliacao_temporaria()
    c = app.test_client()
    try:
        csrf = get_csrf_token_cliente(c, '/avaliacao?token=' + token)
        with c.session_transaction() as s:
            s['username'] = '0' #siape do trabalho criado por _criar_avaliacao_temporaria
        c.post('/uploadCR', data={'csrf_token': csrf, 'idTrabalho': str(projeto),
                                  'arquivo_trabalho': (io.BytesIO(b'docx'), 'final.docx')},
               content_type='multipart/form-data')
        import time
        for _ in range(20): #upload_e_apaga dispara uma thread
            if enviados: break
            time.sleep(0.05)
        final = obterColunaUnica('editalProjeto', 'arquivo_projeto_final', 'id', str(projeto))
        assert final.startswith('FINAL.') and final.endswith('.docx')
        assert enviados == ['cppgi/uploads/' + final]
    finally:
        final = obterColunaUnica('editalProjeto', 'arquivo_projeto_final', 'id', str(projeto))
        if final and os.path.exists(ATTACHMENTS_DIR + final):
            os.remove(ATTACHMENTS_DIR + final)
        _remover_avaliacao_temporaria(edital, projeto)

def get_csrf_token_cliente(c, res):
    rv = c.get(res)
    return re.search(r'name="csrf_token" value="([^"]+)"', rv.data.decode()).group(1)

def test_uploadCR_e_link_exigem_dono_e_prazo(monkeypatch):
    import io, pesquisa
    enviados = []
    monkeypatch.setattr(pesquisa, 'upload_s3', lambda origem, destino: enviados.append(destino))
    edital, projeto, token = _criar_avaliacao_temporaria()
    c = app.test_client()
    def post_final():
        return c.post('/uploadCR', data={'csrf_token': csrf, 'idTrabalho': str(projeto),
                                         'arquivo_trabalho': (io.BytesIO(b'docx'), 'final.docx')},
                      content_type='multipart/form-data')
    def post_link(link):
        return c.post('/cadastrarLinkApresentacao', data={'csrf_token': csrf, 'idTrabalho': str(projeto), 'link': link})
    final = lambda: obterColunaUnica('editalProjeto', 'arquivo_projeto_final', 'id', str(projeto))
    link_atual = lambda: obterColunaUnica('editalProjeto', 'link_apresentacao', 'id', str(projeto))
    try:
        csrf = get_csrf_token_cliente(c, '/avaliacao?token=' + token)
        antes_final, antes_link = final(), link_atual()
        #sem login
        post_final(); post_link('https://exemplo.org/sala')
        assert final() == antes_final and link_atual() == antes_link
        #logado, mas o trabalho é de outro usuário
        with c.session_transaction() as s:
            s['username'] = '11122233344'
        post_final(); post_link('https://exemplo.org/sala')
        assert final() == antes_final and link_atual() == antes_link
        #dono: link javascript: é recusado; https é aceito
        with c.session_transaction() as s:
            s['username'] = '0'
        post_link('javascript:alert(1)')
        assert link_atual() == antes_link
        post_link('https://exemplo.org/sala')
        assert link_atual() == 'https://exemplo.org/sala'
        #dono, mas fora do prazo
        atualizar("UPDATE editais SET deadline_versao_final=%s, deadline_apresentacao=%s WHERE id=%s",
                  (datetime.datetime.now() - datetime.timedelta(days=2), datetime.datetime.now() - datetime.timedelta(days=2), edital))
        post_final(); post_link('https://exemplo.org/outra')
        assert final() == antes_final and link_atual() == 'https://exemplo.org/sala'
    finally:
        f = final()
        if f and f != '0' and os.path.exists(ATTACHMENTS_DIR + f):
            os.remove(ATTACHMENTS_DIR + f)
        _remover_avaliacao_temporaria(edital, projeto)
