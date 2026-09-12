# Project brief: holdenweb.com as a podpack site

> **Orientation · for somebody meeting this repository for the first time.**
> Pointers rather than facts wherever possible — every fact repeated here is one
> that can drift out of step with the document that owns it, which is how its
> own predecessor came to be wrong. Reference is [`operations.md`](operations.md),
> procedure is [`ops/`](ops/), and the framework's own documentation is
> authoritative for anything about podpack.

*Rewritten 2026-08-13, when the conversion described below actually landed.
The previous version was written on 2026-08-05 to bring a fresh session up to
speed on a site that had not yet been converted; almost every specific in it
is now wrong, which is why this replaces rather than amends it.*

---

## 1. What this repository is now

**A podpack site.** The system for building sites — the thing the old brief
called "the goal" — exists as its own project at `~/sites/podpack`, and this
repository is one of its two consumers (the other, `~/sites/podpack-demo`,
exists to prove a site can be built by following podpack's documentation
rather than by copying this one).

So the interesting architecture is largely *not* here any more. podpack
supplies the application factory, the app registry, the template search
order, the migration wiring and the container substrate. This repository
supplies: its own chrome, its own routes, its app list, and its content.

**Read podpack's own documentation first** — `README.md` for the plugin API
and the substrate, `creating-a-site.md` for how a site is stood up,
`adrs/` for why each choice was made. This file only covers what is
specific to holdenweb.com.

## 2. The shape of the site

`src/holdenweb/__init__.py` is now 113 lines: a factory that delegates to
`podpack.create_app(site_package="holdenweb", init=_wire)`, and `_wire`,
which attaches the extensions belonging to the site rather than to any
feature — mail and paranoid sessions — per
[ADR-0025](../podpack/adrs/0025-the-site-wires-its-own-extensions.md). Login
is no longer among them: podpack installs flask-security itself
([ADR-0033](../podpack/adrs/0033-login-is-core.md)).

Seven apps are installed, named by import name in `config/app.toml`:

| App | Import name | Mounted | Where it lives |
| --- | --- | --- | --- |
| `main` | `holdenweb` | `/` | this repository, `src/holdenweb/views.py` |
| `pybooks` | `podpack_pages.pybooks` | `/pybooks` | github.com/holdenweb/podpack-pages |
| `blog` | `podpack_pages.blog` | `/blog` | github.com/holdenweb/podpack-pages |
| `notebooks` | `podpack_notebooks` | `/notebooks` | github.com/holdenweb/podpack-notebooks |
| `pages` | `podpack_pages` | `/pages` | github.com/holdenweb/podpack-pages |
| `qrcode` | `podpack_qrcode` | `/qrcode` | github.com/holdenweb/podpack-qrcode |
| `pdf` | `podpack_pdf` | `/pdf` | github.com/holdenweb/podpack-pdf |

`main` is this site's own routes packaged as an app like any other — the
front page, `/config`, `/ip`, and permanent redirects from the pre-podpack
content URLs (including `/python`, now a 301 into the pybooks app). It is
listed first so its front page claims `/` before podpack's fallback can
([ADR-0024](../podpack/adrs/0024-the-front-page-belongs-to-the-site.md)).

### Content is one name space now

`podpack-pages` serves both HTML and Markdown from a single set of
addresses: `/pages/<name>` looks for `md-pages/<name>.md` first and
`html-pages/<name>.html` second, so a page's URL never says which format it
is stored in, and a Markdown page shadows an HTML one of the same name. The
old `/note/<name>`, `/page/<name>/` and `/asset/<path>` URLs 301-redirect
into it.

The content itself ships inside the app and is seeded to the host data
directory on first install, so editing a page on the host changes the site
with no rebuild. **That means the packaged copy is not the live copy**: an
app upgrade will not deliver changed content to a host that already has the
directory, which is podpack's known and deliberate app-data gap.

`HTTPContentSource` was not carried over. It was mothballed per the previous
brief and the abstraction went with it; if content ever needs to come from
elsewhere, that is a change inside `podpack-pages`.

## 3. Running it

Locally, either with `scripts/dev.sh` (it sources `dev.env` and runs
`flask --app holdenweb run --debug`) or with the Flask CLI and an explicit
environment as below. The repo's `.env` is *container* wiring
(`HOST_DATA_DIR` is compose's variable, not `PODPACK_DATA_ROOT`):

```bash
SECRET_KEY=dev-only SECURITY_PASSWORD_SALT=dev-only-salt \
SQLALCHEMY_DATABASE_URI=sqlite:////tmp/holdenweb-dev.db \
PODPACK_CONFIG=config/app.toml \
PODPACK_DATA_ROOT=./hostdata/apps PODPACK_LOG_ROOT=./hostlogs/apps \
uv run alembic upgrade head && uv run flask --app holdenweb run --port 8460
```

In containers, with podpack's substrate:

```bash
./scripts/prepare-host-dirs.sh   # once
./scripts/up.sh                  # always rebuilds, stamps the commit
```

`/_status` answers most questions about a running instance: which apps are
installed and where their state lives, which commit the image was built
from, and which database and role it is actually connected as.

**The database publishes no port.** Nothing inside the suite needs one, and
it was the only number two sites still had to coordinate — which duly
clashed with podpack-demo. Forward one when a host-side `psql` or
`alembic revision --autogenerate` wants it, on a number nominatable per
invocation
([ADR-0027](../podpack/adrs/0027-the-database-port-is-published-only-on-request.md)):

```bash
podman compose --profile postgres-port up -d postgres-port
```

Or on a port of your choosing, which is the point of it:

```bash
POSTGRES_HOST_PORT=5439 podman compose --profile postgres-port up -d postgres-port
```

## 4. Things specific to this site worth knowing

- **The alembic history can build a database from empty.** It could not
  until 2026-08-13: its only revision baselined a schema production already
  had, so a fresh database (the container lab's included) got nothing from
  `upgrade head`. There is now a real root revision creating `user`, `role`
  and `roles_users`, with the old baseline re-parented onto it and its
  `ALTER COLUMN`s guarded — they are PostgreSQL-only syntax and were fatal
  on SQLite.
- **`user` and `role` keep flask-security's unprefixed table names**, so
  podpack warns about them at boot. Renaming means a production data
  migration; the warning is the cheaper option for now.
- **The `main` app's nav contributes only Home.** Python and Blog are the
  pybooks and blog apps' own nav entries now
  ([ADR-0022](../podpack/adrs/0022-nav-is-contributed-and-addressed-by-endpoint.md));
  both `/pybooks` and `/blog` are served. podpack still refuses to boot on a
  nav entry naming an endpoint no view provides.
- **`/python/` is now a permanent (301) redirect into the pybooks app**, as
  are the old `/pages/python-classes` deep links. The `static/python/web/`
  tree it used to serve is gone; the Python course content lives in
  `podpack-pages` and is pushed to the host, not shipped in this repository.
- **`scripts/` belongs to podpack** — `backup.sh`, `configure-host.py`,
  `dev.sh`, `prepare-host-dirs.sh`, `restore.sh`, `up.sh` and
  `verify-backup.sh`. Personal experiments go in `scratch/`, which is
  gitignored; the MongoDB lab lives there now as `scratch/podman/`.

## 5. What is left

1. **Push this branch's dependencies' repositories**, and then this branch.
   All four dependencies resolve from git already
   (`podpack`, `podpack-pages`, `podpack-qrcode`, `podpack-pdf`), which is what
   lets the container build succeed.
2. **Merge `podpack` to `main`** and deploy. Production is stamped at the
   old baseline revision, so it needs no schema change; the deployment
   change is real, though — uwsgi is gone and gunicorn calls the factory.
3. **Decide about MongoDB.** The lab in `scratch/podman/` still works. The
   open question is whether podpack should offer it as an optional backing
   service — see the note at the end of §6.
4. **The package-upgrade workflow**, deliberately postponed until the site
   was fully operational, which as of 2026-08-13 it is.

## 6. Working preferences, still true

- **Verify by running.** Everything claimed here was checked against a live
  stack. The conversion's two worst bugs — an alembic history that could not
  bootstrap, and a substrate guard that followed symlinks out of the site —
  were both found by running the thing, not by reading it.
- **Comments explain why, not what.** The code and the ADRs both do this;
  match the density.
- **Config belongs to the host and to version control**; secrets to the
  environment.
- **Flag concerns, then finish the job.** Prefer being told about a problem
  alongside completed work rather than being asked about it first.

*On MongoDB as a podpack facility:* it is not an app — an app is a blueprint
with endpoints, and a database is a backing service like PostgreSQL, which
lives in the substrate rather than the app list. The shape that would work is
a compose service under a profile, enabled by a site setting
`COMPOSE_PROFILES=mongo` in `.env` so that `depends_on` still resolves, with
the client wired into `app.extensions` by the site's own `init` exactly as
mail and login are. What it would cost is a second persistence story that
podpack's promises do not currently cover: one `db.metadata`, one migration
history, `/_status` reporting one database.
