# Deploying: laptop → staging → production

Development happens on the laptop. [`ops/deploy.sh`](deploy.sh) moves a
committed revision outward — to **staging** (`os.holdenweb.com`) first, then to
**production** once staging has been seen working.

**The host fetches.** `deploy.sh` pushes the commit to GitHub on a per-target
deploy ref, then over ssh has the host fetch from its own `origin`, check that
exact commit out, and run `scripts/up.sh` — which stamps it into the image, so
`/_status` reports the `build_commit` actually running. Each target is still a
git remote, but only as the address: its scp-style URL says which host and which
directory (HW-0001), and nothing is pushed to it. See
[HW-0034](../adrs/0034-the-host-fetches-the-commit-it-is-told-to-run.md) for why
it works this way.

## One-time setup, per target

On the Opalstack host (staging is the app `os`, so `~/apps/os`):

```bash
mkdir -p ~/apps/os ~/apps/os/data ~/apps/os/logs
```

```bash
cd ~/apps/os && git clone git@github.com:holdenweb/holdenweb-com.git site
```

That needs a **passphraseless, read-only deploy key** for this repository in the
host's `~/.ssh` — a deploy key rather than an account key so a compromised host
cannot push anywhere, and passphraseless because `deploy.sh`'s `git fetch` runs
over ssh with no tty and no agent to unlock anything. Check it before you rely
on it:

```bash
ssh opal17 'cd ~/apps/os/site && git fetch --prune origin && echo ok'
```

`data` and `logs` are siblings of `site`, never inside it: the site's own
content and the database live outside the checkout, so a `git checkout` (or a
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
WEB_HOST_PORT=<Opalstack Nginx Proxy Port>
WEB_BIND_ADDR=127.0.0.1
COMPOSE_FILE=compose.yaml:compose.postgres.yaml
GUNICORN_WORKERS=2
```

`PODPACK_PROXY_HOPS` is deliberately not in that list any more. podpack derives
the trusted-hop count from `PODPACK_ENVIRONMENT` above, so a non-local target
reads `X-Forwarded-Proto` and builds `https://` URLs without being told
([ADR-0039](https://github.com/holdenweb/podpack/blob/main/adrs/0039-the-hop-count-follows-the-deployment.md)).
Set it only for a second proxy, or to `0` where a non-local target has nothing
in front of it. A host on a podpack older than that decision still needs
`PODPACK_PROXY_HOPS=1`; `ops/rebuild.md` Part 4 is the check that says which
case you are in.

On the laptop, add the remote. Its URL is where `deploy.sh` and
`push-content.sh` read the host and path from; neither pushes to it:

```bash
git remote add staging opal17:apps/os/site
```

## Migrating a host that was set up the old way

The staging checkout was created with `git init` and populated by pushes, so it
has no `origin`. **Do not re-clone it** — `.env` and `secrets.env` live in that
directory and are not in git. On the host:

```bash
cd ~/apps/os/site && git remote add origin git@github.com:holdenweb/holdenweb-com.git
```

```bash
cd ~/apps/os/site && git fetch --prune origin && git config --unset receive.denyCurrentBranch
```

The next `./ops/deploy.sh staging` leaves HEAD detached at the deployed commit,
which is from then on the normal state of a deploy checkout.

## Deploying

```bash
./ops/deploy.sh --dry-run staging   # print what it would do, touch nothing
```

```bash
./ops/deploy.sh staging             # publish, fetch, rebuild, prove
```

It refuses a dirty tree (commit first, or `--allow-dirty`); warns if the commit
is not on `origin/main`, which is a note rather than a bar because the deploy ref
is `deploy/staging` and unmerged work is exactly what staging is for; polls the
target's `/healthz` via [`ops/poll-health.sh`](poll-health.sh); and finally asks
the container which commit it is running and fails unless that is the commit you
deployed. A non-zero exit at either of the last two is the signal to look.

## Adding production

Create its Opalstack app (say `~/apps/hw`), repeat the host setup with
`SITE_NAME=hw-holdenweb-com` and its own deploy key, add the laptop remote
`git remote add production opal17:apps/hw/site`, and fill in the `production`
health URL in [`deploy.sh`](deploy.sh)'s `health_url()`. Then
`./ops/deploy.sh production` delivers the same commit staging proved, on the ref
`deploy/production`.
