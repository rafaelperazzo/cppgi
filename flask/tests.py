from pesquisa import app,executarSelect,config
import pytest
import base64

aplicacao = app.test_client()
usuario = config['DEFAULT']['usuario']
senha = config['DEFAULT']['senha']
usuario_senha = str.encode("%s:%s" %(usuario,senha))

def test_main():
    rv = aplicacao.get('/',follow_redirects=True)
    assert rv.status_code==200

def test_admin():
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    rv = aplicacao.get('/admin',follow_redirects=True,headers={"Authorization": "Basic " + valid_credentials})
    assert rv.status_code==200

def test_admin_edital():
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    rv = aplicacao.get('/admin/9',follow_redirects=True,headers={"Authorization": "Basic " + valid_credentials})
    assert rv.status_code==200

def test_edital_projeto():
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    consulta = """
    SELECT id FROM editais
    """
    editais,total = executarSelect(consulta)
    for edital in editais:
        rv = aplicacao.get('/editalProjeto/' + str(edital[0]),follow_redirects=True,headers={"Authorization": "Basic " + valid_credentials})
        assert rv.status_code==200
    