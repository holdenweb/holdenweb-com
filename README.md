# holdenweb.com

> **Introduction · for any reader.** What this site is and what it is made of.
> Deliberately the one document here that does not pick an audience.

A [podpack](https://github.com/holdenweb/podpack) site. The site itself is
small by design: `config/app.toml` names the installed apps, this package
supplies the chrome (`templates/`, `static/`) and the site's own routes, and
podpack supplies the factory, the app registry and the migration wiring.

| Feature | Comes from |
| --- | --- |
| front page, `/config`, `/ip`, `/python`, legacy redirects | this package (`src/holdenweb/views.py`, installed as the app `main`) |
| HTML/Markdown content at `/pages/<name>` | `podpack-pages` |
| QR code generator at `/qrcode/` | `podpack-qrcode` |
| PDF booklet maker and page splitter at `/pdf/` | `pp-pdf` |
| login, mail, session policy | wired by this package's `init` (`_wire`) |

Content is served from a **single name space**: `/pages/<name>` searches the
Markdown tree before the HTML tree, so a page's address never says which
format it is stored in. The old `/note/`, `/page/` and `/asset/` URLs
redirect permanently.

## Run the site locally

No dev server script: the Flask CLI runs the real factory. Secrets and
wiring come from the environment (the repo's `.env` holds *container*
wiring — `HOST_DATA_DIR` is compose's variable, not `PODPACK_DATA_ROOT`, so
keep the two schemes apart by being explicit):

```bash
SECRET_KEY=dev-only SECURITY_PASSWORD_SALT=dev-only-salt \
SQLALCHEMY_DATABASE_URI=sqlite:////tmp/holdenweb-dev.db \
PODPACK_CONFIG=config/app.toml \
PODPACK_DATA_ROOT=./hostdata/apps PODPACK_LOG_ROOT=./hostlogs/apps \
uv run alembic upgrade head
```

```bash
SECRET_KEY=dev-only SECURITY_PASSWORD_SALT=dev-only-salt \
SQLALCHEMY_DATABASE_URI=sqlite:////tmp/holdenweb-dev.db \
PODPACK_CONFIG=config/app.toml \
PODPACK_DATA_ROOT=./hostdata/apps PODPACK_LOG_ROOT=./hostlogs/apps \
uv run flask --app holdenweb run --port 8460
```

The first command is needed once per fresh database: the alembic history
builds the schema from empty (port 8460 because 8456 is the production
container's local port). Visit `/_status` to see every installed app, where
its state lives, and which database the site is actually connected to.

## Run the site in containers

The container substrate is podpack's, copied per its creating-a-site guide:

```bash
./scripts/prepare-host-dirs.sh   # once: creates .env, secrets.env, host dirs
./scripts/up.sh                  # always: rebuilds, stamps the commit
```

Uses `podman compose` (the Compose v2 provider — **not** `podman-compose`,
which ignores the ordering gates this stack relies on). Ports and paths live
in `.env`; credentials in `secrets.env`, which must be restored verbatim on
a new host. The `migrate` service applies the alembic history before `web`
starts.

Note: building currently requires the three path-sourced dependencies
(podpack, podpack-pages, podpack-qrcode, pp-pdf) to be repointed at git
remotes and re-locked — a path source cannot survive a container build.

## Database schema changes

One alembic history for the whole site. The metadata alembic compares
against is built by importing the models of every app `config/app.toml`
lists — including this package's own `User`/`Role` — with no Flask app
involved. **Always autogenerate with the full app list enabled**: with an
app missing, alembic faithfully proposes dropping its tables.

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

`alembic/env.py` reads `SQLALCHEMY_DATABASE_URI` from the environment (the
same variable the app uses) so the two can never disagree about which
database they mean.

## Tests

```bash
uv run pytest
```

The suite builds the real site from the shipped `config/app.toml`, so it
exercises the configuration that deploys.

## Verifying a deployment

Unit tests need no server and run in two seconds. The integration suite drives
a real browser against a **running** site, and is how a deployment is checked:

```bash
uv run playwright install chromium                 # once per machine
uv run pytest tests/integration
```

No argument needed: it reads `WEB_HOST_PORT` and `WEB_BIND_ADDR` from the
site's own `.env` — the file that decided where the site listens in the first
place — so it is right on every host by construction. Point it elsewhere with
`--base-url https://staging.holdenweb.com` or `SITE_URL=…`, and the header
always names what it tested:

```
integration target: http://127.0.0.1:8461
```

Which means a plain `uv run pytest` runs them too when a site is reachable,
and reports connection failures when it is not. If you want only the fast
suite, name it: `uv run pytest tests/test_routes.py tests/test_commands.py`.

The suite asks each app to do its job rather than merely answer: the QR code
app generates a code, the PDF tools offer both forms, the pages app renders
content wearing the site's own stylesheet. A route returning 200 only proves
the blueprint registered — the QR code app answered 200 for weeks while
contributing no navigation entry at all.
