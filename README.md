# holdenweb.com

> **Introduction · for any reader.** What this site is and what it is made of.
> Deliberately the one document here that does not pick an audience.

A [podpack](https://github.com/holdenweb/podpack) site. The site itself is
small by design: `config/app.toml` names the installed apps, this package
supplies the chrome (`templates/`, `static/`) and the site's own routes, and
podpack supplies the factory, the app registry and the migration wiring.

| Feature | Comes from |
| --- | --- |
| front page, `/config`, `/ip`, legacy redirects | this package (`src/holdenweb/views.py`, installed as the app `main`) |
| HTML/Markdown content at `/pages/<name>` | `podpack-pages` (the `pages` app) |
| Python course at `/pybooks/` (the "Python" nav entry) | `podpack-pages` (the `pybooks` app) |
| Blog at `/blog/` (the "Blog" nav entry) | `podpack-pages` (the `blog` app) |
| Jupyter notebooks at `/notebooks/` (the "Notebooks" nav entry) | `podpack-notebooks` |
| QR code generator at `/qrcode/` | `podpack-qrcode` |
| PDF booklet maker and page splitter at `/pdf/` | `podpack-pdf` |
| login | `podpack` core (ADR-0033) |
| mail, session policy | wired by this package's `init` (`_wire`) |

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


## Updating site content

The content apps — `pages`, `pybooks`, `blog`, `notebooks` — serve files from the host's
`hostdata/apps/<app>/<tree>`, not from git. Each area is built by its own tool
on the laptop and delivered straight into that tree: `ops/push-content.sh`
rsyncs the built directory up and runs `ops/refresh-content.sh` on the host,
which owns the container-subuid dance. Content is live the moment it lands —
`podpack_pages` reads the file on every request, so no restart is involved.

### The four areas

| Area | Served at | Host tree | Built on the laptop by | One line |
| --- | --- | --- | --- | --- |
| Python course | `/pybooks` | `pybooks/html-pages` | orpy `build.py --fragments` → `~/Projects/Python/orpy/python-classes` | `just pybooks staging` |
| Blog | `/blog` | `blog/export` | blogscraper `python -m blogscraper export` → `~/Projects/Python/blogscraper/build` | `just blog staging` |
| Notebooks | `/notebooks` | `notebooks/html-pages` | podpack-notebooks `uv run build.py` → `~/sites/podpack-notebooks/build/html-pages` | `just notebooks staging` |
| Prose pages | `/pages` | `pages/md-pages` and `pages/html-pages` | no builder — written by hand in `~/sites/holdenweb-content/pages` | `just pages staging` |

Those source directories are the defaults; a builder that writes elsewhere is
accommodated by `ORPY_BUILD`, `SITESCRAPER_BUILD`, `NOTEBOOKS_BUILD` or
`PAGES_SOURCE` rather than by editing the recipe.

Two things about those defaults that have each cost an afternoon.
`SITESCRAPER_BUILD` names a builder now called **blogscraper**; the variable
keeps the old name, and `~/Projects/Python/sitescraper` does not exist, so a
command naming it fails at `push-content.sh:53`. And `ORPY_BUILD`'s default,
`~/Projects/Python/orpy/python-classes`, is a **symlink** that orpy's
`templating/out` points at, itself gitignored inside orpy -- so the Python
course takes two gitignored hops before it reaches a host tree. `PAGES_SOURCE`
is the one source that is version-controlled. Swap `staging` for `local` to refresh this
checkout's own `hostdata` instead of the deployed site.

### The commands those recipes run

The same pair, spelled out. The left column runs **on the laptop** and needs
nothing else; the right column runs **on the box that serves the site** — for
staging that is `opal17`, in the site directory, which is what the left column
is doing over ssh.

| Area | On the laptop, to staging | On the box that serves |
| --- | --- | --- |
| Python course | `ops/push-content.sh staging ~/Projects/Python/orpy/python-classes --app pybooks --tree html-pages` | `APP=pybooks TREE=html-pages ops/refresh-content.sh <staged-dir>` |
| Blog | `ops/push-content.sh staging ~/Projects/Python/blogscraper/build --app blog --tree export` | `APP=blog TREE=export ops/refresh-content.sh <staged-dir>` |
| Notebooks | `ops/push-content.sh staging ~/sites/podpack-notebooks/build/html-pages --app notebooks --tree html-pages` | `APP=notebooks TREE=html-pages ops/refresh-content.sh <staged-dir>` |
| Prose pages | `ops/push-content.sh staging ~/sites/holdenweb-content/pages/md-pages --app pages --tree md-pages` | `APP=pages TREE=md-pages ops/refresh-content.sh <staged-dir>` |
| Prose pages | `ops/push-content.sh staging ~/sites/holdenweb-content/pages/html-pages --app pages --tree html-pages` | `APP=pages TREE=html-pages ops/refresh-content.sh <staged-dir>` |

Append `--mirror` to either to remove whatever the source no longer has. It is
off by default in both, because an incomplete source with `--mirror` deletes a
visitor's content, and an interactive run asks you to type `mirror` before it
deletes anything. `--dry-run` prints the plan and changes nothing; both scripts
take it, so `just <area> staging --dry-run` previews a push and
`just <area> local --dry-run` previews a local refresh. It is worth the
keystrokes before a `--mirror`: the plan is printed under the file counts at
both ends, and "this removes 721 files and puts 719 back" is a different
decision from "this removes nothing" — which is not something the confirmation
prompt can tell you.


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

## Monitoring

[UptimeRobot](https://uptimerobot.com) checks `https://os.holdenweb.com/healthz`
every five minutes over HTTPS and mails when it fails. It is the only thing
watching the site *between* deploys — everything above is a point-in-time check
that a person runs.

**It asks `/healthz` rather than the front page, and that is the whole value of
it.** Measured on the laptop lab with the stack up and `podman compose stop
postgres`:

| | database up | database stopped |
| --- | --- | --- |
| `/` | 200 | 200 |
| `/pages/test` | 200 | 200 |
| `/login` | 200 | 200 |
| `/healthz` | 200 | **503** |

A monitor on the site root reports green straight through a total database
outage: the front page still renders while login, sessions and password reset
are all broken. `/healthz` answers 503, so a plain 2xx test is exactly right and
no keyword check is needed. Proven against the real deployment on 2026-09-22 —
stopping postgres produced the alert mail; on the lab, restarting it returned
`/healthz` to 200 within about three seconds, unattended.

One case it does not catch, by design: a **non-fatal app** failure keeps the 200
(ADR-0030), so the blog reporting itself unhealthy does not take the site's
status down. That is what [`ops/poll-health.sh`](ops/poll-health.sh) is for — it
greps the body for `"status":"ok"` rather than trusting the status code, and
`ops/deploy.sh` runs it after every rebuild, so a deploy that does not come up
healthy fails there rather than quietly.
