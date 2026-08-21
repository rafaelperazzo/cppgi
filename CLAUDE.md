# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CPPGI is a Flask-based event/research-management system (in Portuguese) used by UFCA for managing research
project submissions, peer-review/evaluation workflows, presentation scheduling, and certificate generation for
academic events (e.g. SEPEC/CONPESQ). It runs as a Docker Compose stack: a `cppgi` Flask app container + a
`db_cppgi` MariaDB container.

## Running the stack

```console
docker-compose up -d                 # start app (port 9010) + mariadb (port 33306)
docker-compose restart cppgi         # restart the app after editing flask/*.py (no rebuild needed; bind-mounted)
docker-compose logs -f cppgi
```

- `flask/` is bind-mounted into the container at `/home/perazzo/cppgi`, and `fonts/` at `/fonts` — code edits take
  effect on container restart, no image rebuild required (rebuild only needed for `requirements.txt`/`Dockerfile`
  changes).
- The app entrypoint is `flask/pesquisa.py`, served via `waitress` on port 80 inside the container, mounted under
  the `/cppgi` URL prefix.
- Local runtime config lives in `flask/.env` (gitignored; copy from `flask/.env.sample`). At the top of
  `pesquisa.py`, right after the imports, a bootstrap step decides where config comes from: if the real
  container/process environment variable `PRODUCAO` (uppercase, distinct from the `producao` key inside
  `.env`) is `1`, it calls `load_ssm_parameters()` (walks all AWS SSM Parameter Store params under
  `/pesquisa`, `WithDecryption=True`, and injects them into `os.environ`, one AWS API call per env — needs
  IAM credentials on the container, e.g. instance profile/role, not sourced from `.env`); otherwise it calls
  `load_dotenv()` (loads `flask/.env` into `os.environ`). Either way, `config = {'DEFAULT': os.environ}`
  right after, so every existing `config['DEFAULT']['CHAVE']` access site (~20 of them, plus `tests.py`,
  which imports `config` from `pesquisa`) keeps working unchanged, reading whichever source populated
  `os.environ`. SSM parameter names must match the `.env` key names exactly (case-sensitive, e.g.
  `/pesquisa/AWS_S3_BUCKET`, `/pesquisa/DB_PASSWORD`). If SSM lookup fails (`ClientError`/`BotoCoreError`),
  `load_ssm_parameters()` re-raises — startup fails hard in that case, by design (no silent fallback to
  defaults). `docker-compose.yml.sample`'s `cppgi` service shows the `PRODUCAO=1` env var; without it (or
  with `PRODUCAO=0`/unset) the app always uses `.env`, which is what local dev does today (no such var is
  set in the local `docker-compose.yml`).
  This replaces the former `config.ini` + `senhas.pass` (3-line file: DB password, Gmail SMTP password,
  Flask session secret key) — DB password and Gmail SMTP password are now the `DB_PASSWORD`/
  `GMAIL_SMTP_PASSWORD` keys (in `.env` or under the SSM prefix). `app.config['SECRET_KEY']` (Flask
  session/CSRF signing key, formerly the 3rd line of `senhas.pass`) is instead regenerated with
  `secrets.token_hex(32)` on every process start, from neither `.env` nor SSM (explicit product decision —
  the production host reboots daily at 23h/7h, so a daily session/CSRF invalidation on restart is
  acceptable; do not "fix" this back to a static key without checking with the user first).
- `vault.exec` / `cppgi.exec` are Hashicorp Vault agent helpers used to template DB credentials into a
  separate `.env` at the repo root (`MYSQL_PASSWORD`/`MYSQL_ROOT_PASSWORD`) for `docker-compose` itself in
  the real deployment — not to be confused with `flask/.env` (the app's own config); not needed for local
  dev unless integrating with Vault.

## Tests

```console
docker-compose exec cppgi python -m pytest -vv -s /home/perazzo/cppgi/tests.py
```

(see `test.sh` for the full Vault-agent-driven invocation used in CI/deploy). Tests in `flask/tests.py` hit a real
running Flask test client (`app.test_client()`) against the real MySQL database configured in `flask/.env` —
there's no mocking layer. HTTP Basic Auth credentials for tests come from `config['DEFAULT']['usuario']` /
`['senha']` in `flask/.env`.

`flask/teste.py` is an ad hoc manual scratch script, not part of the pytest suite.

## Architecture

**Monolithic Flask app.** `flask/pesquisa.py` (~3400 lines) defines the Flask app, almost all ~90 `@app.route`
view functions, DB helpers, and the `__main__` entrypoint that starts `waitress`. There is no blueprint
separation — everything lives in this one module, and most other Python files in `flask/` import shared
state/helpers directly from it (`from pesquisa import executarSelect, ...`). When making changes, search
`pesquisa.py` first; it is the source of truth for routing, auth, and most business logic.

Key pieces inside `pesquisa.py`:
- App/config setup at the top: working dirs, `.env` loading (via `dotenv_values`), Flask-Mail, Flask-Uploads,
  CSRF, CORS, logging (level depends on `producao` flag in `.env`).
- `executarSelect` / `executarSelect2` / `atualizar` / `inserir`: thin raw-SQL helpers over `MySQLdb` — almost all
  DB access in this codebase is hand-written SQL via these helpers, not an ORM.
- `flask_httpauth.HTTPBasicAuth` (`auth`) with `get_user_roles` driving `@auth.login_required(role=[...])` checks
  (roles: `admin`, `avaliador`, `monitor`) gating most administrative/evaluator routes.
- Certificate generation (`gerarCertificado*` functions): builds PDFs/PNGs from templates in
  `flask/documentos/` using Pillow + `fonts/Times_New_Roman*.ttf`, plus `pdfkit`/`wkhtmltopdf` for HTML→PDF
  declarations.
- Session/room-distribution logic (`distribuir`, `distribuirIgualmente`, `getSlots`, `getSessoesSalas`) for
  scheduling presentations into rooms/time slots for an `edital` (call for submissions/event edition).
- `flask_apscheduler.APScheduler` (`scheduler`, initialized near the Flask-Mail setup): runs
  `job_enviar_email_avaliadores` (wrapping `enviar_email_avaliadores`, also reachable manually via
  `/emailSolicitarAvaliacao`) on a cron trigger (Fridays only, 07:59 America/Fortaleza), capped by an `end_date`
  equal to `deadline_avaliacao` of the most recent `edital` (`obterDeadlineAvaliacaoUltimoEdital()`, `ORDER BY id
  DESC LIMIT 1`) — the job stops firing once that edition's evaluation deadline passes. The job is only
  registered/started at all if the current time falls within the 35 days before that `deadline_avaliacao` (i.e.
  `deadline_avaliacao - 35 days <= now <= deadline_avaliacao`); outside that window `scheduler.add_job`/
  `scheduler.start()` are skipped entirely for the process lifetime (re-evaluated only on the next restart). The
  job is only registered and started inside the `if __name__ == "__main__":` block and only when `PRODUCAO==1`,
  so it doesn't run when `pesquisa.py` is imported (e.g. by `tests.py`) or in non-production config. Admins can
  toggle it on/off at runtime via `/toggleSchedulerAvaliadores` (linked from `admin.html`), which no-ops with a
  flash message if the job was never registered. A second job, `job_solicitar_versao_final` (id
  `solicitar_versao_final`, wrapping `/solicitarVersaoFinal/<edital>`'s logic via the shared
  `buscarPendentesVersaoFinal()` + `processar_emails_versao_final()` helpers), runs on a separate cron cadence —
  Mondays only, 10:55 America/Fortaleza — scoped to a declarative trigger window — `start_date` =
  `deadline_avaliacao + 1 day` and `end_date` = `deadline_versao_final`, both of the most recent `edital`
  (`obterUltimoEdital()`, `ORDER BY id DESC LIMIT 1`). Unlike the first job, this one is always registered (when
  `PRODUCAO==1` and an edital exists); APScheduler itself computes no next-fire-time outside the start/end
  window, so no manual pre-registration gate is needed. Both jobs share one `scheduler.start()` call.

**Other top-level `flask/*.py` modules**, all importing from `pesquisa.py` rather than being self-contained:
- `app_api.py` — Flask-RESTful `Resource` classes (`Submissoes`, `Editais`, `Avaliacoes`, `Trabalhos`,
  `Apresentador`), registered onto `pesquisa.py`'s `api` object only inside `pesquisa.py`'s `if __name__ ==
  "__main__"` block (i.e. the JSON API routes only exist when the app is run as the main process via
  `waitress`, not when imported e.g. for tests via the Flask test client without going through `__main__`).
- `processar.py` — standalone script (run via cron, not a route) for emailing evaluators (invite/reminder/thanks)
  for a given `edital`, keyed by CLI args.
- `auditoria.py`, `atualizar_email.py`, `atualizar_tokens.py`, `calcular_lattes.py` — standalone maintenance
  scripts (user provisioning/audits, Lattes-CV scoring) run manually or via cron, each re-reading `.env`
  independently rather than sharing app state.

**Templates & static assets**: `flask/templates/` (Jinja2, named after routes/concepts, e.g.
`certificado_avaliador.html`, `avaliacao.html`) and `flask/static/` (a built React app's static bundle alongside
hand-written HTML/JS/CSS, e.g. `tablefilter` vendor lib, `comum.js`). `static/` already contains compiled JS/CSS
bundles for that React app and for tooling vendored in (chosen.js, tablefilter).

Application-facing pages (everything `pesquisa.py` renders that isn't a certificate/declaration/e-mail body, see
below) extend `flask/templates/layout.html`, a shared Tailwind-based layout (institutional header, flashed
messages, footer). Certificates (`certificado_*.html`), declarations rendered for PDF/print
(`a4.html`, `orientador.html`, `declaracao_avaliador.html`, `declaracao_evento.html`, anything extending
`BASE_documento.html`/`BASE_certificado.html`), and e-mail bodies (`email_*.html`, plus a few templates rendered
into `Message(html=...)` like `confirmacao_submissao.html`/`confirmacao_avaliacao.html`/`certificado_submissao.html`
— grep `render_template` call sites for `html=texto_email` before assuming a template is browser-only) are
deliberately **not** on this layout: they need self-contained inline-style HTML for `pdfkit`/e-mail clients, not an
external stylesheet.

## Frontend / Tailwind

CSS is Tailwind v4, compiled with the **standalone Tailwind CLI** (no Node/npm in this repo). Source is
`flask/static/css/tailwind.input.css` (theme tokens + `@layer components` for shared classes like `.btn-primary`,
`.form-input`, `.alert-warning`, `.table-base` — used across templates instead of repeating long utility chains);
output is the compiled, committed `flask/static/css/tailwind.css`, which `layout.html` links with `_external=True`
(some pages render through `pdfkit`, which needs an absolute URL, not a relative `/static/...` path).

Rebuild after editing `tailwind.input.css` or adding new utility classes to templates:
```console
./.tailwindcli -i flask/static/css/tailwind.input.css -o flask/static/css/tailwind.css --minify
```
The `.tailwindcli` binary itself is gitignored (download the standalone release for your platform from
`tailwindlabs/tailwindcss` releases if missing).

**Data flow for an event cycle** (the core domain concept is an `edital` — a call/edition of the event):
submission (`/cadastrarProjeto`) → evaluator assignment/invites (`processar.py` cron, `/inserirAvaliador`) →
evaluation (`/avaliacao`, `/avaliar`) → results/scheduling (`/resultados`, `/distribuirSalas`, `/programacao`) →
presentation day operations (`/mapa`, `/horario/<sala>`, file uploads via `/uploadCR`) → post-event certificates
and emails (`/gerarCertificadoAvaliador`, `/certificadoApresentacoes`, `/enviarCertificados/<edital>`).

## Database

MariaDB 10.5.8, started with `--sql_mode=""` (relaxed SQL mode — be aware when writing new queries, strict-mode
issues won't surface locally). Schema snapshot for reference is at `share/2025-02-20T19.04-cppgi.sql`. Backups are
pulled from the production server via `atualizar_db.sh` (restores into the local `db_cppgi` container — this is a
destructive operation against local data, confirm before running).

## Operational scripts (not part of app code, used for deploys/cron on the prod host)

- `cron.sh`, `cron.avaliador.sh`, `cron.final.sh` — scheduled curl/docker-compose-run calls per `edital` for
  evaluator emails, presentation reminders, etc.
- `flask/cron` — crontab installed inside the app container (cleanup of temp files, daily `processar.py` runs,
  hourly `backup-mysql.sh`).
- `pos_avaliacoes.sh` — post-evaluation batch step.
- `*.sample` files (`docker-compose.yml.sample`, `backup.sh.sample`, `cicd.sh.sample`, `commit.sh.sample`, etc.) are
  templates for the real (gitignored) deployment scripts — check the corresponding `.sample` to understand what an
  untracked script does.
