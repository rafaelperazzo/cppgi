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
   cp flask/.env.sample flask/.env
   ```

2. Ajuste `flask/.env` com a URL do servidor, modo de produção (`producao = 0/1`), credenciais do banco
   (`database`, `usuario`, `senha`), `DB_PASSWORD` (senha do usuário `cppgi` no MariaDB), `GMAIL_SMTP_PASSWORD`
   e, se for usar upload para S3, as credenciais AWS. A chave de sessão do Flask (`SECRET_KEY`) **não** vem
   do `.env`: é gerada aleatoriamente a cada início do app (`secrets.token_hex(32)`), o que também derruba
   sessões/CSRF ativos a cada restart — aceitável porque o host de produção reinicia diariamente (23h–7h).

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

## Testes

```console
docker-compose exec cppgi python -m pytest -vv -s /home/perazzo/cppgi/tests.py
```

Os testes em `flask/tests.py` usam o cliente de testes real do Flask (`app.test_client()`) contra o banco MySQL
configurado em `flask/.env` — não há camada de mocking. As credenciais de Basic Auth vêm de
`config['DEFAULT']['usuario']`/`['senha']`. Veja `test.sh` para a invocação completa usada em CI/deploy (via
Vault Agent).

## Estrutura do projeto

```
flask/
  pesquisa.py        # app Flask: rotas, auth, helpers de banco, geração de certificados, agendamento
  seguranca_utils.py # funções puras de segurança: senha forte, tokens, headers Cloudflare (ver seção abaixo)
  app_api.py         # API JSON (Flask-RESTful), registrada apenas quando pesquisa.py roda como __main__
  processar.py        # script de cron para e-mails a avaliadores (convite/lembrete/agradecimento)
  auditoria.py, atualizar_email.py, atualizar_tokens.py, calcular_lattes.py  # scripts de manutenção
  modules/            # helpers de apoio (funcoes.py, scoreLattes.py, odtEdit.py, etc.)
  templates/          # views Jinja2 (layout.html + páginas) e templates de certificado/e-mail (sem layout)
  static/             # CSS Tailwind compilado, bundle React legado, libs vendorizadas (chosen.js, tablefilter)
  .env                # configuração local (gitignored, ver acima; a partir de .env.sample)
fonts/                # fontes usadas na geração de certificados (Times New Roman)
share/                # dumps/snapshots do schema do banco
share/migrations/     # scripts SQL incrementais (sem framework de migration; aplicar manualmente)
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

## Autenticação e Segurança

- **Autocadastro** (`/cadastro`): CPF, e-mail, nome completo e senha forte (mínimo 12 caracteres, com
  maiúscula, minúscula, número e caractere especial — validado por `seguranca_utils.senha_forte`). A conta
  só é liberada para login após confirmação por e-mail (`/confirmarEmail/<token>`, token expira em 24h). CPF
  ou e-mail já cadastrados são rejeitados sem criar conta duplicada; ao detectar CPF já existente, o
  e-mail associado é mostrado mascarado (`ra***@dominio.com`) orientando o uso de "Esqueci minha senha".
- **Sessão**: no login (`verify_password`, usado tanto pelo formulário `/login` quanto pelo handshake nativo
  de HTTP Basic Auth), `session['cpf']`, `session['nome']` e `session['email']` são populados; `/logout`
  limpa toda a sessão. `/cadastrarProjeto` exige sessão ativa e usa `session['cpf']`/`session['email']` em
  vez de campos de formulário preenchidos manualmente (a criação implícita de conta que existia nesse fluxo
  foi removida).
- **Login com link para autocadastro**: a tela `/login` mostra "Ainda não tem cadastro? Criar conta",
  apontando para `/cadastro`, para quem tenta entrar sem ter conta.
- **Troca de senha forçada** (`forcar_troca_senha` em `users`, avaliado em todo login bem-sucedido dentro
  de `verify_password`): disparada por dois motivos independentes —
  1. **Credencial vazada (Cloudflare)**: header `Exposed-Credential-Check: 1` (feature "Leaked/Exposed
     Credential Checks" do Cloudflare) presente na requisição de login. **Nota de infraestrutura**: esse
     header só é confiável se a origem não for acessível diretamente pela internet (Authenticated Origin
     Pulls / allowlist de IP do Cloudflare) — sem isso, qualquer cliente pode forjá-lo. `CF-IPCountry`/
     `CF-IPCity` (geolocalização) seguem a mesma lógica; `CF-IPCity` não é um header padrão fora de
     Enterprise/Workers.
  2. **Senha fraca**: a própria senha submetida no login não passa mais em `seguranca_utils.senha_forte`
     (ex. contas antigas criadas com a senha auto-gerada de 8 caracteres). **Atenção ao rollout**: como a
     maioria das contas legadas foi criada com esse padrão de senha curta, essa checagem tende a forçar a
     troca de senha para praticamente toda a base de usuários existente já no primeiro login após o
     deploy — não é um caso raro, é o comportamento esperado.

  Em ambos os casos, um middleware (`@app.before_request`) bloqueia o acesso a qualquer rota até a senha
  ser trocada em `/trocarSenhaObrigatoria`.
- **Troca de senha voluntária** (`/trocarSenha`, link "Trocar minha senha" no card "Senha" da tela
  inicial, visível só logado): exige a senha atual correta (confirmação de identidade), aplica a mesma
  regra de senha forte para a nova senha, e também checa `Exposed-Credential-Check` na própria submissão —
  se disparar, a troca é recusada e a conta é jogada no fluxo de troca obrigatória (`forcar_troca_senha=1`)
  em vez de aceitar a senha potencialmente comprometida.
- **Senhas continuam em texto puro** em `users.password` (decisão explícita, fora do escopo desta entrega)
  — `verify_password` compara diretamente via SQL, sem hashing.
- **Auditoria (`@log_required`)**: decorator aplicado às rotas administrativas/avaliador/monitor
  (`@auth.login_required`) e às rotas de autenticação (`/login`, `/cadastro`, `/confirmarEmail`,
  `/trocarSenhaObrigatoria`, `/logout`, `/cadastrarProjeto`). Registra o ID numérico do usuário
  (`users.id`, populado em `session['user_id']` no login), CPF (**sempre mascarado**, ex. `111******56`,
  via `seguranca_utils.mascarar_cpf`), rota, método HTTP, IP e país/cidade (headers Cloudflare) **só em
  log de arquivo** (`flask/auditoria.log`, logger dedicado com nível `INFO` independente do logger raiz —
  que fica em `ERROR` quando `PRODUCAO=1`), sem tabela no banco.
- **`/seguranca`**: página pública (link no rodapé) que documenta, em dois blocos, os mecanismos de
  segurança de infraestrutura (Cloudflare) e de aplicação — ver `flask/templates/seguranca.html`.

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
- `vault.exec`/`cppgi.exec` — helpers do Vault Agent para gerar credenciais do banco em um `.env` na raiz do
  repo, consumido pelo `docker-compose` real (`MYSQL_PASSWORD`/`MYSQL_ROOT_PASSWORD`) — não confundir com
  `flask/.env`, que é a configuração da aplicação (não necessário para desenvolvimento local).

Demais arquivos `*.sample` (`backup.sh.sample`, `cicd.sh.sample`, `commit.sh.sample`, etc.) são modelos dos
scripts reais (gitignored) — consulte o `.sample` correspondente para entender o que um script não versionado
faz.
