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
- Local runtime config lives in `flask/config.ini` (gitignored; copy from `config.ini.sample`) and
  `flask/senhas.pass` (gitignored, not present in sample form — a 3-line file: app password, Gmail SMTP password,
  Flask session secret key, read line-by-line by `pesquisa.py` and the cron scripts).
- `vault.exec` / `cppgi.exec` are Hashicorp Vault agent helpers used to template DB credentials into `.env` for
  docker-compose in the real deployment; not needed for local dev unless integrating with Vault.

## Tests

```console
docker-compose exec cppgi python -m pytest -vv -s /home/perazzo/cppgi/tests.py
```

(see `test.sh` for the full Vault-agent-driven invocation used in CI/deploy). Tests in `flask/tests.py` hit a real
running Flask test client (`app.test_client()`) against the real MySQL database configured in `config.ini` —
there's no mocking layer. HTTP Basic Auth credentials for tests come from `config['DEFAULT']['usuario']` /
`['senha']` in `config.ini`.

`flask/teste.py` is an ad hoc manual scratch script, not part of the pytest suite.

## Architecture

**Monolithic Flask app.** `flask/pesquisa.py` (~3400 lines) defines the Flask app, almost all ~90 `@app.route`
view functions, DB helpers, and the `__main__` entrypoint that starts `waitress`. There is no blueprint
separation — everything lives in this one module, and most other Python files in `flask/` import shared
state/helpers directly from it (`from pesquisa import executarSelect, ...`). When making changes, search
`pesquisa.py` first; it is the source of truth for routing, auth, and most business logic.

Key pieces inside `pesquisa.py`:
- App/config setup at the top: working dirs, `config.ini` loading, Flask-Mail, Flask-Uploads, CSRF, CORS, logging
  (level depends on `producao` flag in `config.ini`).
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
  `/emailSolicitarAvaliacao`) on a cron trigger (Mon/Fri 07:00 America/Fortaleza), capped by an `end_date` equal to
  `deadline_avaliacao` of the most recent `edital` (`obterDeadlineAvaliacaoUltimoEdital()`, `ORDER BY id DESC LIMIT
  1`) — the job stops firing once that edition's evaluation deadline passes. The job is only registered and
  started inside the `if __name__ == "__main__":` block and only when `PRODUCAO==1`, so it doesn't run when
  `pesquisa.py` is imported (e.g. by `tests.py`) or in non-production config. Admins can toggle it on/off at
  runtime via `/toggleSchedulerAvaliadores` (linked from `admin.html`), which no-ops with a flash message if the
  job was never registered.

**Other top-level `flask/*.py` modules**, all importing from `pesquisa.py` rather than being self-contained:
- `app_api.py` — Flask-RESTful `Resource` classes (`Submissoes`, `Editais`, `Avaliacoes`, `Trabalhos`,
  `Apresentador`), registered onto `pesquisa.py`'s `api` object only inside `pesquisa.py`'s `if __name__ ==
  "__main__"` block (i.e. the JSON API routes only exist when the app is run as the main process via
  `waitress`, not when imported e.g. for tests via the Flask test client without going through `__main__`).
- `processar.py` — standalone script (run via cron, not a route) for emailing evaluators (invite/reminder/thanks)
  for a given `edital`, keyed by CLI args.
- `auditoria.py`, `atualizar_email.py`, `atualizar_tokens.py`, `calcular_lattes.py` — standalone maintenance
  scripts (user provisioning/audits, Lattes-CV scoring) run manually or via cron, each re-reading
  `senhas.pass`/`config.ini` independently rather than sharing app state.

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
