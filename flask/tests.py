from pesquisa import app,executarSelect,config,WORKING_DIR,id_generator,atualizar,ATTACHMENTS_DIR,obterColunaUnica
import pytest
import base64
import os

aplicacao = app.test_client()
client = aplicacao
usuario = config['DEFAULT']['usuario']
senha = config['DEFAULT']['senha']
usuario_senha = str.encode("%s:%s" %(usuario,senha))

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

def test_0_cadastrar_projeto():
    titulo = id_generator(40)
    nome = str(id_generator(30)).upper()
    response = client.post("/cadastrarProjeto", data={
        "destino": "9",
        "tipo_trabalho": "1",
        "tipo_apresentacao": "1",
        "autores": nome,
        "identificacao": "00000000000",
        "email": "email@email.com",
        "grande_area": "Ciências da Vida",
        "titulo": titulo,
        "palavras": "android",
        "resumo": "Resumo do trabalho",
        "arquivo_trabalho": open(WORKING_DIR + "teste.pdf","rb"),
    },follow_redirects=True)
    assert response.status_code == 200
    consulta = """
    SELECT max(id) FROM editalProjeto
    """
    linhas,total=executarSelect(consulta)
    last_id = linhas[0][0]
    consulta = """
    SELECT nome,arquivo_projeto FROM editalProjeto WHERE id=%s
    """ %(last_id)
    linhas,total = executarSelect(consulta)
    arquivo_projeto = linhas[0][1]
    assert linhas[0][0]==nome
    assert linhas[0][1]!="0"
    assert os.path.exists(ATTACHMENTS_DIR + arquivo_projeto)==True
    
def test_1_adicionar_avaliador():
    id_projeto = get_last_id('editalProjeto')
    get_res('/listar_consultores/' + str(id_projeto))
    edital = obterColunaUnica('editalProjeto','tipo','id',str(id_projeto))
    get_res('/avaliacoesNegadas?edital=' + str(edital) + '&id=' + str(id_projeto))
    data={
        "txtEmail": "test@ufca.edu.br",
        "txtProjeto": str(id_projeto),
        "avaliador_sugerido": "0",
        "avaliador_area": "0",
    }
    post_res('/inserirAvaliador',data)

def test_2_avaliar():
    pass

def test_3_verificar_avaliacao():
    pass

'''
def test_4_remover_submissao_teste():
    consulta = """
    SELECT max(id) FROM editalProjeto
    """
    linhas,total=executarSelect(consulta)
    last_id = linhas[0][0]
    consulta = """
    SELECT nome,arquivo_projeto FROM editalProjeto WHERE id=%s
    """ %(last_id)
    linhas,total = executarSelect(consulta)
    arquivo_projeto = linhas[0][1]
    consulta = """
    DELETE FROM editalProjeto where id=%s
    """ %(last_id)
    atualizar(consulta)
    
    if os.path.exists(ATTACHMENTS_DIR + arquivo_projeto):
        os.remove(ATTACHMENTS_DIR + arquivo_projeto)
    consulta = """
    SELECT * FROM editalProjeto WHERE id=%s
    """ %(last_id)
    linhas,total = executarSelect(consulta)
    assert total==0
    assert os.path.exists(ATTACHMENTS_DIR + arquivo_projeto)==False
'''

def test_5_meusProjetos():
    pass

