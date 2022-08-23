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
        return({'total': total})

    def totais(self,id_edital,modalidade):
        consulta = ""
        if int(modalidade)!=4:
            consulta = """
            SELECT categoria,count(id) FROM editalProjeto 
            WHERE tipo=%s AND valendo=1 AND modalidade=%s
            GROUP BY categoria
            """ %(id_edital,modalidade)
        else:
            consulta = """
            SELECT categoria,count(id) FROM editalProjeto 
            WHERE tipo=%s AND valendo=1 
            GROUP BY categoria
            """ %(id_edital)
        try:
            linhas,total = executarSelect(consulta)
            dado = {'orais': linhas[0][1],'poster': linhas[1][1]}
            return(dado)
        except Exception as e:
            dado = {'orais': 0,'poster': 0}
            return(dado)

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

    def get(self,id_edital,tipo,modalidade):
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
        elif int(tipo)==4:
            return(self.totais(id_edital,modalidade))
        else:
            return([])

class Editais(Resource):
    def get(self):
        consulta = """
        SELECT id,nome_longo FROM editais 
        ORDER BY id
        """
        linhas,total = executarSelect(consulta)
        dados = []
        for linha in linhas:
            dado = {'id': linha[0],'label': linha[1]}
            dados.append(dado)
        return(dados)