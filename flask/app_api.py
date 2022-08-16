from flask_restful import Resource
from pesquisa import executarSelect

class Submissoes(Resource):
    def consultar(self,consulta,id_edital):
        consulta = """
        SELECT id,nome,titulo,ua FROM editalProjeto 
        WHERE valendo=1 
        AND tipo=%s
        ORDER BY id
        """ %(id_edital)
        linhas,total = executarSelect(consulta)
        dados = []
        for linha in linhas:
            dado = {'id': linha[0],'nome': linha[1],'titulo': linha[2],'ua': linha[3]}
            dados.append(dado)
        return(dados)
    
    def total(self,consulta,id_edital):
        consulta = """
        SELECT id,nome,titulo,ua FROM editalProjeto 
        WHERE valendo=1 
        AND tipo=%s
        ORDER BY id
        """ %(id_edital)
        linhas,total = executarSelect(consulta)
        return(total)

    def agrupar(self,id_edital):
        consulta = """
            SELECT ua,count(id) FROM `editalProjeto` 
            WHERE valendo=1 and tipo=%s GROUP BY ua ORDER BY ua
            """ %(id_edital)
        linhas,total = executarSelect(consulta)
        dados = []
        for linha in linhas:
            dado = {'ua': linha[0],'total': linha[1]}
            dados.append(dado)
        return(dados)

    def get(self,id_edital,tipo):
        consulta = """
        SELECT id,nome,titulo,ua FROM editalProjeto 
        WHERE valendo=1 
        AND tipo=%s
        ORDER BY id
        """ %(id_edital)
        if int(tipo)==1:
            return(self.consultar(consulta,id_edital))
        elif int(tipo)==2:
            return(self.total(consulta,id_edital))
        elif int(tipo)==3:
            return(self.agrupar(id_edital))
        else:
            return([])
