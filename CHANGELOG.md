	2025-01-21 10:32:52 -0300	fix: /distribuirSalas - Ajustando a ordenação da distribuição para levar em consideração as áreas e subáreas cnpq
	2025-01-21 10:07:28 -0300	fix: admin.html - ajustado a sequencia de passos que devem ser seguidos no pos-avaliação
	2025-01-21 09:49:42 -0300	fix: /premiacao - Cálculo da média alterada para considerar os primeiros dois avaliadores com recomendação positiva
	2024-12-04 09:45:12 -0300	fix: rota meusPareceres com erro no SQL: idProjeto é uma coluna ambigua. Corrigido para avaliacoes.idProjeto
	2024-11-18 10:37:12 -0300	fix: envio de email para avaliadores apenas quando o status da submissão estiver indefinido.
	2024-11-18 10:24:28 -0300	feat: Adicionado recurso para atualizar a situação das submissões que tiverem mais do que 2 avaliações
	2024-11-14 10:20:47 -0300	chore: gitignore ajustado
	2024-11-12 16:21:00 -0300	fix: gitignore
	2024-11-12 16:20:55 -0300	fix
	2024-11-12 16:19:15 -0300	fix: listar_consultores_edital com erro no SQL
	2024-11-12 16:16:17 -0300	fix: listar_consultores_edital com erro no SQL
	2024-11-12 16:15:42 -0300	fix: listar_consultores_edital com erro no SQL
	2024-11-01 13:31:53 -0300	fix: colocado o target para os links das imagens dos certificados na rota /admin
	2024-11-01 10:28:04 -0300	fix: formulário de avaliação com texto de ajuda para avaliador
	2024-11-01 10:23:14 -0300	fix: formulário de avaliação com texto de ajuda para avaliador
	2024-11-01 10:20:56 -0300	feat: formulario de avaliação apenas avalia se o trabalho não estiver identificado, com mensagem informativa para o avaliador
	2024-11-01 10:19:47 -0300	feat: formulario de avaliação apenas avalia se o trabalho não estiver identificado
	2024-11-01 09:33:07 -0300	chore: ajustes no texto do formulario de avaliação
	2024-11-01 09:29:27 -0300	feat: adicionado campo de identificação no formulário de avaliação
	2024-10-03 09:45:15 -0300	feat: incluídos campos de acessibilidade no form de cadastro de trabalho
	2024-09-13 09:51:30 -0300	fix: removido metodo get do salvar_projeto
	2024-09-11 15:18:54 -0300	fix: incluídos csfr nos forms
	2024-09-11 14:41:51 -0300	fix: local do csrf - logo apos o app
	2024-09-11 14:40:55 -0300	fix: preencher dados automaticamente a partir do cpf informado
	2024-09-11 11:05:45 -0300	fix: removendo . e - do cpf
	2024-09-11 10:57:41 -0300	chore: incluída lista de projetos associados
	2024-09-11 09:52:46 -0300	chore: acesso a api pesquisa
	2024-09-10 15:52:01 -0300	fix: codigo de voluntario mudou para 0
	2024-09-10 15:27:38 -0300	fix: visibilidade dos tipo de vinculo e fomento
	2024-09-10 14:47:42 -0300	fix: ajustado disabled do tipo de vinculo
	2024-09-10 14:46:02 -0300	fix: tipo_vinculo padrão em /cadastrarProjeto
	2024-09-10 14:42:26 -0300	fix: função submit do form cadastrarProjeto
	2024-09-10 12:56:19 -0300	fix: form CadastrarProjeto
	2024-09-10 12:53:16 -0300	fix: form CadastrarProjeto
	2024-09-09 16:01:07 -0300	fix: Inseridos novos campos no cadastrarProjeto
	2024-09-09 12:57:30 -0300	fix: Incluídos vinculo, tipo de vínculo e agencia de fomento no cadastrarProjeto
	2024-09-09 12:46:41 -0300	fix: Corrigido Layout da submissão de trabalhos, trechos que não dependem de ajustes no pesquisa.py
	2024-09-09 12:34:56 -0300	fix: submissão apenas em pdf
	2024-09-06 11:03:55 -0300	fix: Adicionada permissão de anais no formulário de cadastro
	2023-11-29 10:29:01 -0300	chore: Scripts de cicd, atualizar_db e commit funcionando
	2023-11-07 13:46:09 -0300	incluido icone de docx na rota anais
	2023-10-23 13:51:50 -0300	solicitação de versão final corrigida!
	2023-10-19 15:15:27 -0300	adicionados demais certificados
	2023-10-19 14:50:06 -0300	Correções no envio dos certificados para apresentadores
	2023-10-17 09:25:31 -0300	modificada funcionalidade de versão final para arquivo editável
	2023-10-16 07:27:48 -0300	ajustando recurso de envio de versão final
	2023-10-04 07:40:31 -0300	incluida lista de links dos avaliadores
	2023-10-03 15:00:16 -0300	acessos registrados em algumas rotas
	2023-10-03 14:28:48 -0300	logs de acessos
	2023-10-03 14:06:35 -0300	incluída opção para rodar sob um proxy reverso
	2023-10-03 11:00:55 -0300	falha tecnica
	2023-10-03 10:59:44 -0300	versão corrigida
	2023-10-03 10:56:24 -0300	emails ajustados
	2023-10-03 09:46:50 -0300	incluido link de sala
	2023-09-29 16:13:09 -0300	mais ajustes nos e-mails
	2023-09-29 14:59:56 -0300	email com instruções para os apresentadores modificado
	2023-09-06 13:54:30 -0300	incluido alguns excepts
	2023-09-06 13:44:51 -0300	api com resultados
	2023-08-29 14:38:13 -0300	ajustado convite para avaliação
	2023-06-12 15:09:32 -0300	incluido backup.sh
	2023-06-12 14:28:30 -0300	Database agora no config.ini
	2023-01-30 09:28:04 -0300	Corrigido anais - nome->titulo
	2022-10-20 10:49:06 -0300	Corrigido link de autenticacao
	2022-10-20 09:42:00 -0300	Incluídos certificados dos demais participantes
	2022-09-28 10:14:54 -0300	corrigida data das avaliaçooes orais
	2022-09-28 09:57:19 -0300	Corrigido bug das avaliacoes orais
	2022-09-27 09:26:49 -0300	Incluído acesso às avalições das apresentações
	2022-09-22 16:41:18 -0300	Trabalhos premiados disponiveis
	2022-09-22 16:38:44 -0300	Ajustes nos trabalhos aprovados
	2022-09-22 16:06:21 -0300	Pequenos ajustes
	2022-09-22 09:35:58 -0300	Corrigido o criterio de desempate dos premiados
	2022-09-22 08:08:14 -0300	6 premiados
	2022-09-21 11:25:28 -0300	E-mail de informações corrigido para thread
	2022-09-21 11:19:35 -0300	Threads dos processamentos de e-mails corrigidas
	2022-09-21 11:08:27 -0300	Solicitar versão final - corrigido
	2022-09-21 11:01:04 -0300	Incluída lista de trabalhos premiados
	2022-09-20 21:26:26 -0300	falhas no auth
	2022-09-20 19:52:47 -0300	ultima
	2022-09-20 16:16:19 -0300	threads nos emails
	2022-09-20 16:11:20 -0300	removida thread para email
	2022-09-20 15:52:52 -0300	bcc para recipients
	2022-09-20 15:33:07 -0300	ajustes no email para moderador
	2022-09-20 15:24:27 -0300	Bloqueando reavaliação de apresentação
	2022-09-20 14:23:06 -0300	Mais ajustes
	2022-09-20 14:21:40 -0300	Email com instruções avaliadores modificado
	2022-09-20 14:19:29 -0300	Ajustado email com instruções para autores
	2022-09-19 16:06:42 -0300	Ajustes no mapa
	2022-09-19 13:39:44 -0300	Mapa geral atualizado
	2022-09-19 11:21:51 -0300	Corrigido Mapa de Avaliadores
	2022-09-16 16:47:06 -0300	Bugs no cadastrar usuario
	2022-09-16 16:33:31 -0300	resultados alterados novamente
	2022-09-16 16:30:33 -0300	resultados com local/data
	2022-09-16 16:28:47 -0300	Bugs corrigidos
	2022-09-16 16:26:32 -0300	Bugs corrigidos
	2022-09-16 15:01:14 -0300	ordenação
	2022-09-16 14:55:07 -0300	Ordenação do local_apresentação
	2022-09-16 14:52:55 -0300	Ordenação do local_apresentação
	2022-09-16 13:48:49 -0300	Ajustes na premiação e distribuição por salas
	2022-09-14 15:44:34 -0300	pagina de resultados - br
	2022-09-14 15:41:08 -0300	pagina de resultados
	2022-09-14 10:48:27 -0300	Ajuste na página de resultados
	2022-09-14 10:30:09 -0300	Ajustada rota de resultados
	2022-09-12 11:29:49 -0300	Instruções de apresentação alteradas para formato presencial
	2022-09-09 13:59:23 -0300	Removido log do template do avaliador
	2022-09-06 10:14:26 -0300	API de avaliações
	2022-08-30 16:21:00 -0300	Formato da data da api modificada
	2022-08-26 15:14:34 -0300	Adicionada API de datas
	2022-08-25 15:28:18 -0300	incluída lista de trabalhos no painel
	2022-08-25 15:14:39 -0300	API com lista de trabalhos
	2022-08-25 11:03:58 -0300	Corrigido problema dos filtros modalidade e ua
	2022-08-25 09:36:40 -0300	Painel de estatisticas
	2022-08-24 10:32:39 -0300	busca no editalProjeto
	2022-08-23 16:30:43 -0300	incluído react painel
	2022-08-23 15:41:55 -0300	Incluida area na api
	2022-08-23 14:25:09 -0300	Incluido filtro por modalidade na api
	2022-08-23 10:09:04 -0300	Ajuste na api totais
	2022-08-22 16:03:33 -0300	API - orais e posters
	2022-08-19 16:28:00 -0300	Corrigido bug do jquery
	2022-08-18 15:35:16 -0300	Incluido cors
	2022-08-16 16:25:19 -0300	incluída api com lista de editais
	2022-08-16 15:43:48 -0300	Iniciada a API
	2022-08-04 09:41:31 -0300	OK Merge branch 'develop' of github.com:rafaelperazzo/cppgi
	2022-08-03 15:20:02 -0300	Inserido menu
	2022-08-03 14:55:13 -0300	1.1.6 Merge branch 'develop'
	2022-08-03 14:54:58 -0300	corrigido bug na lista de editais
	2022-08-03 10:18:06 -0300	Ajuste nos testes
	2022-08-03 10:14:28 -0300	1.1.5 Merge branch 'develop'
	2022-08-03 10:14:14 -0300	Incluídas as opções de envio dos emails com instruções
	2022-08-03 09:36:12 -0300	Corrigida localização dos arquivos
	2022-08-02 16:42:14 -0300	1.1.4 Merge branch 'develop'
	2022-08-02 16:42:02 -0300	Correções na pagina principal
	2022-08-02 10:30:32 -0300	1.1.2 Merge branch 'develop'
	2022-08-02 10:30:29 -0300	Merged 1.1.2
	2022-08-02 10:22:02 -0300	Visual modificado
	2022-08-01 19:06:19 -0300	1.1.1 Merge branch 'develop'
	2022-08-01 19:06:03 -0300	Pronto para produção
	2022-08-01 15:58:40 -0300	certificado avaliador OK
	2022-08-01 10:47:34 -0300	editalProjeto com jquery OK
	2022-07-31 11:11:00 -0300	Incluido jquery para atualizar dados de forma genérica
	2022-07-30 11:26:43 -0300	Mais ajustes no editalprojeto
	2022-07-30 09:42:22 -0300	datatables editalProjeto
	2022-07-30 09:10:59 -0300	Alterada opção inserir avaliador
	2022-07-29 16:27:55 -0300	Teste: Inserir e conferir avaliador
	2022-07-29 15:59:28 -0300	Teste: inserir avaliador
	2022-07-29 10:23:33 -0300	Ajustes nos testes
	2022-07-29 10:03:47 -0300	Atualizado para flask 2.1.3
	2022-07-28 16:18:05 -0300	1.0.2 Merge branch 'develop'
	2022-07-28 16:17:53 -0300	logo atualizada
	2022-07-28 16:03:03 -0300	1.0.1 Merge branch 'develop'
	2022-07-28 16:02:51 -0300	Incluido captcha
	2022-07-28 14:09:39 -0300	1.0.0 Merge branch 'develop'
	2022-07-28 14:08:58 -0300	Iniciados testes automatizados. os primeiros
	2022-07-28 14:06:07 -0300	Iniciados testes automatizados...
	2022-07-28 11:31:28 -0300	Incluido no-reply
	2022-07-28 11:18:43 -0300	Corrigido problema no editalProjeto
	2022-07-27 16:37:45 -0300	Imagem de fundo dos certificados como base64
	2022-07-27 11:20:36 -0300	Certificado de apresentador modificado
	2022-07-26 19:03:40 -0300	Incluído o flask-crontab
	2022-07-26 18:59:07 -0300	Migrado para python3
	2022-07-26 18:28:19 -0300	primeiro develop
	2022-07-26 17:19:44 -0300	Função para enviar png fora do static
	2022-07-26 16:18:53 -0300	Capcha no formulário de submissão
	2022-07-24 18:41:25 -0300	Validação de cpf
	2022-07-24 15:34:48 -0300	Incluido parcialmente o gerenciamento do usuarios_salas
	2022-07-24 11:21:12 -0300	Incluído gerenciamento de usuários
	2022-07-23 18:43:13 -0300	Pequenos ajustes visuais
	2022-07-23 17:14:46 -0300	Listagem geral dos trabalhos aprovados
	2022-07-23 13:27:17 -0300	Cadastro e listagem de sessões
	2022-07-22 19:08:53 -0300	Inclída lista geral de avaliações por edital
	2022-07-22 15:39:42 -0300	Corrigida declaração do avaliador
	2022-07-22 15:18:35 -0300	Alterada declaracao avaliador
	2022-07-22 14:07:23 -0300	Certificado avaliador em PDF
	2022-07-22 12:25:41 -0300	Finalizada tela para cadastro de avaliador
	2022-07-21 19:51:09 -0300	Iniciando jquery no inserir avaliador
	2022-07-21 16:45:38 -0300	Opção de enviar e-mail para avaliadores no front-end
	2022-07-21 15:53:58 -0300	Lista de avaliadores inserida
	2022-07-21 12:57:33 -0300	editalProjeto agora pode ser editado
	2022-07-21 10:33:48 -0300	Concluída a página admin
	2022-07-20 18:08:45 -0300	Corrigido parcialmente atualização dos templates de certificados
	2022-07-20 15:20:45 -0300	Lista de editais com ajax - ajustado
	2022-07-20 15:19:59 -0300	Lista de editais com ajax
	2022-07-20 09:52:53 -0300	Cadastro de edital corrigido!
	2022-07-20 09:21:10 -0300	Tentando correção do cadastrar edital
	2022-07-19 16:09:59 -0300	Cadastro de edital iniciado
	2022-07-19 11:37:20 -0300	Incluída lista de editais
	2022-07-19 09:25:17 -0300	Link para editalProjeto corrigido
	2022-07-19 09:20:12 -0300	Mais ajustes visuais
	2022-07-18 16:19:06 -0300	Ajustes visuais no meusProjetos
	2022-07-18 11:39:25 -0300	Visual do admin,meusProjeto ajustado
	2022-07-18 11:25:15 -0300	Ajustes no envio de e-mail para avaliadores
	2022-07-18 09:02:06 -0300	Incluido config.ini.sample
	2022-07-18 08:58:57 -0300	Versão para CPPGI 2022
	2022-07-15 16:12:45 -0300	Envio de trabalho -> PRONTO
	2022-07-15 11:11:22 -0300	Credenciais incluídas no e-mail de submissão
	2022-07-14 16:04:24 -0300	Iniciando modernização
	2022-06-17 09:51:55 -0300	Ajustado Dockerfile
	2022-06-15 13:46:28 -0300	incluidos scripts
	2022-06-15 11:06:25 -0300	Primeiro commit