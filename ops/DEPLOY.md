# Deploying: laptop → staging → production

Development happens on the laptop. [`ops/deploy.sh`](deploy.sh) moves a
committed revision outward — to **staging** (`os.holdenweb.com`) first, then to
**production** once staging has been seen working. Each target is a git remote
pointing at a receiving checkout on its Opalstack host; pushing to it updates
the working tree in place, and `scripts/up.sh` rebuilds from the pushed commit
so `/_status` reports the exact `build_commit` running.

## One-time setup, per target

On the Opalstack host (staging is the app `os`, so `~/apps/os`):

```bash
mkdir -p ~/apps/os/site ~/apps/os/data ~/apps/os/logs
cd ~/apps/os/site
git init -b main
git config receive.denyCurrentBranch updateInstead   # a push updates the work-tree
```

`data` and `logs` are siblings of `site`, never inside it: the site's own
content and the database live outside the checkout, so a push (or a
`git clean`) can never take them with it. That is also what
`PODPACK_ENVIRONMENT=staging` enforces — `prepare-host-dirs.sh` refuses to put
data inside a working tree unless the environment is `local`.

Create the host's `.env` and `secrets.env` with `scripts/configure-host.py`
(it generates secrets and writes 0600), then set in `.env`:

```
SITE_NAME=os-holdenweb-com          # <app>-<site>: dots/underscores → dashes
PODPACK_ENVIRONMENT=staging         # any non-local value
HOST_DATA_DIR=../data               # → ~/apps/os/data
HOST_LOG_DIR=../logs                # → ~/apps/os/logs
PODPACK_PROXY_HOPS=1                # or reset-password mail goes out as http://
WEB_HOST_PORT=<Opalstack Nginx Proxy Port>
WEB_BIND_ADDR=127.0.0.1
COMPOSE_FILE=compose.yaml:compose.postgres.yaml
GUNICORN_WORKERS=2
```

On the laptop, add the remote (its URL is the single source of truth
`deploy.sh` reads the host and path from):

```bash
git remote add staging opal17:apps/os/site
```

The first `git push staging HEAD:main` populates the checkout. If it complains
that `main` is unborn on the host, run `git symbolic-ref HEAD refs/heads/main`
in `~/apps/os/site` once, then push again.

## Deploying

```bash
./ops/deploy.sh --dry-run staging   # print what it would do, touch nothing
./ops/deploy.sh staging             # push HEAD, rebuild, poll /healthz
```

It refuses a dirty tree (commit first, or `--allow-dirty`), warns if the commit
is not on `origin/main`, and after the rebuild polls the target's `/healthz`
via [`ops/poll-health.sh`](poll-health.sh) — a non-zero exit there means the
deploy did not come up and is the signal to look.

## Adding production

Create its Opalstack app (say `~/apps/hw`), repeat the host setup with
`SITE_NAME=hw-holdenweb-com`, add the laptop remote
`git remote add production opal17:apps/hw/site`, and fill in the `production`
health URL in [`deploy.sh`](deploy.sh)'s `health_url()`. Then
`./ops/deploy.sh production` delivers the same commit staging proved.
