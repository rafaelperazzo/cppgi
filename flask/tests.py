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
        assert 'inválido ou expirado'.encode() in response.data
        linhas, total = executarSelect("SELECT email_verificado FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 0

        #Token válido confirma, e não pode ser reutilizado depois
        atualizar("UPDATE users SET token_verificacao_expira=%s WHERE username=%s",
                  (datetime.datetime.now() + datetime.timedelta(hours=1), cpf))
        response = client.get('/confirmarEmail/' + token, follow_redirects=True)
        assert response.status_code == 200
        assert 'confirmado com sucesso'.encode() in response.data
        linhas, total = executarSelect("SELECT email_verificado FROM users WHERE username=%s", 1, valores=(cpf,))
        assert linhas[0] == 1

        response = client.get('/confirmarEmail/' + token, follow_redirects=True)
        assert response.status_code == 200
        assert 'inválido ou expirado'.encode() in response.data
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
            get_res('/avaliacoesNegadas')
    finally:
        logger_auditoria.propagate = False
    mensagens = [r.message for r in caplog.records if r.name == 'auditoria_acessos']
    assert any('rota=/avaliacoesNegadas' in m and 'metodo=GET' in m for m in mensagens)
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

