from flask_restful import Resource
from pesquisa import executarSelect,getLinkSala,paraInt
def filtros_modalidade_area(modalidade,area):
    """Trecho SQL e parâmetros dos filtros opcionais de modalidade (4 = todas) e área ("TODAS")."""
    trecho = ""
    valores = ()
    if int(modalidade)!=4:
        trecho = trecho + " AND modalidade=%s "
        valores = valores + (int(modalidade),)
    if area!="TODAS":
        trecho = trecho + " AND ua=%s "
        valores = valores + (area,)
    return trecho,valores

class Submissoes(Resource):
    def consultar(self,consulta,id_edital,modalidade,area):
        filtros,valores = filtros_modalidade_area(modalidade,area)
        consulta = """
        SELECT id,nome,titulo,ua FROM editalProjeto 
        WHERE valendo=1 
        AND tipo=%s""" + filtros + """ ORDER BY id"""
        linhas,total = executarSelect(consulta,valores=(id_edital,) + valores)
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
        """
        linhas,total = executarSelect(consulta,valores=(id_edital,))
        return({'total': total})

    def totais(self,id_edital,modalidade,area):
        filtros,valores = filtros_modalidade_area(modalidade,area)
        consulta = """
        SELECT categoria,count(id) FROM editalProjeto 
        WHERE tipo=%s AND valendo=1
        """ + filtros + " GROUP BY categoria"
        
        linhas,total = executarSelect(consulta,valores=(id_edital,) + valores)
        if int(total)==1:
            try:
                if int(linhas[0][0])==0:
                    dado = {'orais': linhas[0][1],'poster': 0}
                else:
                    dado = {'orais': 0,'poster': linhas[0][1]}
                return(dado)
            except Exception as e:
                dado = {'orais': 0,'poster': 0}
                return(dado)
        try:    
            dado = {'orais': linhas[0][1],'poster': linhas[1][1]}
            return(dado)
        except Exception as e:
            dado = {'orais': 0,'poster': 0}
            return(dado)
        

    def agrupar(self,id_edital):
        consulta = """
            SELECT ua,count(id) FROM `editalProjeto` 
            WHERE valendo=1 and tipo=%s GROUP BY ua ORDER BY ua
            """
        linhas,total = executarSelect(consulta,valores=(id_edital,))
        dados = []
        for linha in linhas:
            dado = {'ua': linha[0],'total': linha[1]}
            dados.append(dado)
        return(dados)

    def agrupar_datas(self,id_edital,modalidade,area):
        consulta = """
        SELECT DATE_FORMAT(data,'%d/%m/%Y'),COUNT(id) 
        FROM editalProjeto 
        WHERE valendo=1 and tipo=%s"""
        filtros,valores = filtros_modalidade_area(modalidade,area)
        consulta = consulta + filtros + """ 
        GROUP BY DATE_FORMAT(data,'%Y-%m-%d');
        """
        linhas,total = executarSelect(consulta,valores=(id_edital,) + valores)
        dados = []
        for linha in linhas:
            dado = {'data': linha[0],'total': linha[1]}
            dados.append(dado)
        
        return(dados)


    def get(self,id_edital,tipo,modalidade,area):
        consulta = """
        SELECT id,nome,titulo,ua FROM editalProjeto 
        WHERE valendo=1 
        AND tipo=%s
        ORDER BY id
        """
        if int(tipo)==1:
            return(self.consultar(consulta,id_edital,modalidade,area))
        elif int(tipo)==2:
            return(self.total(consulta,id_edital))
        elif int(tipo)==3:
            return(self.agrupar(id_edital))
        elif int(tipo)==4:
            return(self.totais(id_edital,modalidade,area))
        elif int(tipo)==5:
            return(self.agrupar_datas(id_edital,modalidade,area))
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

class Avaliacoes(Resource):
    def get(self,id_edital,modalidade,area):
        consulta = """
        SELECT editalProjeto.id,nome,ua,titulo,
        COALESCE(sum(avaliacoes.finalizado),0) as finalizados,
        COALESCE(sum(if(recomendacao=-1,1,0)),0), 
        COALESCE(sum(if(recomendacao=0,1,0)),0),
        COALESCE(sum(if(recomendacao=1,1,0)),0),
        editalProjeto.situacao
        FROM editalProjeto LEFT JOIN avaliacoes on editalProjeto.id=avaliacoes.idProjeto 
        WHERE tipo=%s AND valendo=1
        """
        filtros,valores = filtros_modalidade_area(modalidade,area)
        consulta = consulta + filtros + """
        GROUP BY editalProjeto.id ORDER BY finalizados,editalProjeto.ua,editalProjeto.modalidade,editalProjeto.id
        """
        linhas,total = executarSelect(consulta,valores=(id_edital,) + valores)
        dados = []
        for linha in linhas:
            dado = {'id': linha[0],'autores': linha[1], 'area': linha[2],'titulo': linha[3],'finalizados': int(linha[4]), 'esperando': int(linha[5]),'reprovados': int(linha[6]),'aprovados': int(linha[7]),'situacao': int(linha[8])}
            dados.append(dado)
        
        return(dados)

class Trabalhos(Resource):
    def get(self,id_edital,apresentacao):
        consulta_poster = """SELECT editalProjeto.id,ua,nome,titulo,situacao,
        IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')) as modalid
        ,local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),
        local_apresentacao 
        FROM editalProjeto 
        WHERE valendo=1 AND categoria=1 
        AND tipo=%s ORDER BY ua,modalidade DESC,nome,titulo"""
        consulta_oral = """SELECT editalProjeto.id,ua,nome,titulo,situacao,
        IF(modalidade=0,'RESUMO SIMPLES',IF(modalidade=1,'RESUMO EXPANDIDO','TRABALHO COMPLETO')) as modalid,
        local_apresentacao,DATE_FORMAT(data_apresentacao,'%d/%m/%Y %H:%i'),local_apresentacao 
        FROM editalProjeto 
        WHERE valendo=1 AND categoria=0 AND tipo=%s ORDER BY ua,modalidade DESC,nome,titulo"""
        if paraInt(apresentacao)==1: #vem da URL como texto
            linhas,total = executarSelect(consulta_oral,valores=(id_edital,))
        else:
            linhas,total = executarSelect(consulta_poster,valores=(id_edital,))
        dados = []
        for linha in linhas:
            dado = {'id': linha[0],'autores': linha[2], 'area': linha[1],'titulo': linha[3], 'situacao': int(linha[4]),'modalidade': linha[5],'local_apresentacao': linha[6],'data_apresentacao': linha[7]}
            dados.append(dado)
        return dados

class Apresentador(Resource):
    
    def inicio_sessao(self,sala):
        consulta = """
            SELECT salas,TIME_FORMAT(inicio,'%H:%i') FROM `salas` WHERE salas like %s
        """
        linhas,total = executarSelect(consulta,valores=("%" + str(sala) + "%",))
        for linha in linhas:
            return(linha[1])
        return("")
    
    def get(self,id_submissao):
        consulta = """
        SELECT 
        DATE_FORMAT(data_apresentacao,'%d/%m/%Y'),
        local_apresentacao,
        tipo,
        titulo,
        nome 
        FROM editalProjeto 
        WHERE id=%s
        """
        linhas,total = executarSelect(consulta,valores=(id_submissao,))
        dados = []
        for linha in linhas:
            inicio = self.inicio_sessao(linha[1])
            link = getLinkSala(str(linha[2]),str(linha[1]))
            data_hora = str(linha[0]) + " - " + str(inicio)
            dado = {'data': data_hora,'local': str(linha[1]),'link': link,'titulo': str(linha[3]),'autores': str(linha[4])} 
            dados.append(dado)
        return dados