# CPPGI - Plataforma Yoko Eventos

Sistema de gerenciamento de eventos científicos / acadêmicos (submissão de trabalhos, avaliação por pares,
distribuição em sessões/salas e geração de certificados) usado pela UFCA em eventos como o SEPEC/CONPESQ.

Construído em Flask (Python) com banco de dados MariaDB, executado via Docker Compose.

## Stack

- **Backend**: Flask + `flask_httpauth` (HTTP Basic Auth com papéis `admin`/`avaliador`/`monitor`),
  `flask_restful` (API JSON), `Flask-Mail`, `Flask-Uploads`, `Flask-WTF` (CSRF).
- **Banco de dados**: MariaDB 10.5.8, com acesso via SQL puro (`mariadb`/`MySQLdb`), sem ORM.
- **Geração de documentos**: Pillow (certificados em PDF/PNG) e `pdfkit`/`wkhtmltopdf` (declarações HTML→PDF).
- **Frontend**: Jinja2 + Tailwind CSS v4 (compilado via CLI standalone, sem Node/npm).
- **Servidor**: `waitress`, montado sob o prefixo `/cppgi`.

## Requisitos

- Docker e Docker Compose
- Uma rede Docker externa chamada `web` (`docker network create web`)

## Configuração inicial

1. Copie os arquivos de exemplo e ajuste conforme o ambiente:

   ```console
   cp docker-compose.yml.sample docker-compose.yml
   cp flask/config.ini.sample flask/config.ini
   ```

2. Crie `flask/senhas.pass` (não versionado) com 3 linhas, lidas em ordem por `pesquisa.py` e pelos scripts de
   cron:

   ```
   <senha da aplicação>
   <senha SMTP do Gmail>
   <chave secreta de sessão do Flask>
   ```

3. Ajuste `flask/config.ini` (seção `[DEFAULT]`) com a URL do servidor, modo de produção (`producao = 0/1`) e,
   se for usar upload para S3, as credenciais AWS.

## Executando o stack

```console
docker-compose up -d                 # inicia app (porta 9010) + mariadb (porta 33306)
docker-compose restart cppgi         # reinicia o app após editar flask/*.py (sem rebuild, é bind mount)
docker-compose logs -f cppgi
```

- `flask/` é montado no container em `/home/perazzo/cppgi`, e `fonts/` em `/fonts` — alterações no código têm
  efeito após reiniciar o container, sem necessidade de rebuild da imagem (rebuild só é necessário ao alterar
  `requirements.txt`/`Dockerfile`).
- Entrypoint da aplicação: `flask/pesquisa.py` (servido via `waitress`, prefixo `/cppgi`).
  `flask/wsgi.py` é o entrypoint WSGI alternativo.

## Testes

```console
docker-compose exec cppgi python -m pytest -vv -s /home/perazzo/cppgi/tests.py
```

Os testes em `flask/tests.py` usam o cliente de testes real do Flask (`app.test_client()`) contra o banco MySQL
configurado em `config.ini` — não há camada de mocking. As credenciais de Basic Auth vêm de
`config['DEFAULT']['usuario']`/`['senha']`. Veja `test.sh` para a invocação completa usada em CI/deploy (via
Vault Agent).

## Estrutura do projeto

```
flask/
  pesquisa.py        # app Flask: rotas, auth, helpers de banco, geração de certificados, agendamento
  app_api.py         # API JSON (Flask-RESTful), registrada apenas quando pesquisa.py roda como __main__
  processar.py        # script de cron para e-mails a avaliadores (convite/lembrete/agradecimento)
  auditoria.py, atualizar_email.py, atualizar_tokens.py, calcular_lattes.py  # scripts de manutenção
  modules/            # helpers de apoio (funcoes.py, scoreLattes.py, odtEdit.py, etc.)
  templates/          # views Jinja2 (layout.html + páginas) e templates de certificado/e-mail (sem layout)
  static/             # CSS Tailwind compilado, bundle React legado, libs vendorizadas (chosen.js, tablefilter)
  config.ini / senhas.pass  # configuração local (gitignored, ver acima)
fonts/                # fontes usadas na geração de certificados (Times New Roman)
share/                # dumps/snapshots do schema do banco
*.sh.sample           # modelos dos scripts reais (gitignored) de deploy/backup/cron usados em produção
```

## Frontend / Tailwind

CSS é Tailwind v4, compilado com a **CLI standalone** (sem Node/npm). Fonte em
`flask/static/css/tailwind.input.css`; saída compilada e versionada em `flask/static/css/tailwind.css` (referenciada
com `_external=True` pois algumas páginas são renderizadas via `pdfkit`, que exige URL absoluta).

Reconstrua após editar `tailwind.input.css` ou adicionar novas classes utilitárias nos templates:

```console
./.tailwindcli -i flask/static/css/tailwind.input.css -o flask/static/css/tailwind.css --minify
```

O binário `.tailwindcli` não é versionado — baixe o release standalone para sua plataforma em
[tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss/releases) se estiver ausente.

## Fluxo de dados de um ciclo de evento

O conceito central é o **edital** (chamada/edição do evento):

```
submissão (/cadastrarProjeto)
  → convite/atribuição de avaliadores (cron processar.py, /inserirAvaliador)
  → avaliação (/avaliacao, /avaliar)
  → resultados/agendamento (/resultados, /distribuirSalas, /programacao)
  → operação no dia da apresentação (/mapa, /horario/<sala>, upload via /uploadCR)
  → certificados e e-mails pós-evento (/gerarCertificadoAvaliador, /certificadoApresentacoes,
    /enviarCertificados/<edital>)
```

## Banco de dados

MariaDB 10.5.8, iniciado com `--sql_mode=""` (modo relaxado — atenção a problemas de modo estrito que não
aparecem localmente). Schema de referência em `share/2025-02-20T19.04-cppgi.sql`. `atualizar_db.sh` restaura um
backup de produção no container local (**operação destrutiva** sobre os dados locais).

## Deploy / produção

Deploy automatizado via GitHub Actions (`.github/workflows/update.yml`): a cada push de uma tag `v*.*.*` na
branch `master`, o workflow conecta via SSH ao host de produção, faz `git pull origin master --tags` e reinicia
o serviço (`systemctl restart cppgi.service`).

Scripts operacionais (não fazem parte do código da app, usados em deploy/cron no host de produção):

- `cron.sh`, `cron.avaliador.sh`, `cron.final.sh` — chamadas agendadas (curl/docker-compose run) por edital para
  e-mails de avaliadores, lembretes de apresentação, etc.
- `flask/cron` — crontab instalado dentro do container (limpeza de temporários, execução diária de
  `processar.py`, backup horário via `backup-mysql.sh`).
- `pos_avaliacoes.sh` — etapa em lote pós-avaliação.
- `vault.exec`/`cppgi.exec` — helpers do Vault Agent para gerar credenciais do banco em `.env` para o
  docker-compose real (não necessários para desenvolvimento local).

Demais arquivos `*.sample` (`backup.sh.sample`, `cicd.sh.sample`, `commit.sh.sample`, etc.) são modelos dos
scripts reais (gitignored) — consulte o `.sample` correspondente para entender o que um script não versionado
faz.
