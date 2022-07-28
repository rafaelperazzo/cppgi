from pesquisa import app,executarSelect,config
import pytest
import base64

aplicacao = app.test_client()
usuario = config['DEFAULT']['usuario']
senha = config['DEFAULT']['senha']
usuario_senha = str.encode("%s:%s" %(usuario,senha))

def get_res(res):
    valid_credentials = base64.b64encode(usuario_senha).decode("utf-8")
    rv = aplicacao.get(res,follow_redirects=True,headers={"Authorization": "Basic " + valid_credentials})
    assert rv.status_code==200

def test_main():
    rv = aplicacao.get('/',follow_redirects=True)
    assert rv.status_code==200

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

