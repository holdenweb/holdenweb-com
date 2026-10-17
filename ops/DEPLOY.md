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

Production is an Opalstack application on `opal17`, checked out at
`~/apps/${OS_APP}/site`, and it starts **FRESH**: an empty site, its content
published with `just`, its administrator made by hand.

`${OS_APP}` is that application's name, as the panel shows it, and nothing
below writes it any other way. The commands read it from the shell, so it is
set wherever they run: on `opal17` in step 2, and on the laptop in step 3.

Not a restore of staging. A staging backup restored into a fresh clone
installs staging's `.env` and `secrets.env`, so production would come up as
compose project `os-holdenweb-com` — the name of the staging stack already
running on this host — and would share staging's `SECRET_KEY` and password
salt, so a reset link staging issued would work on production.

Until step 7, `holdenweb.com` still reaches the old site. Nothing before then
can be checked at the public address, and `deploy.sh` has no production health
URL to poll — deliberately, since polling the old site would fail every deploy.

> **Not yet run end to end** (2026-10-17). Each step says what it should
> produce; where that differs, it is a finding — write it here.

### 1. The application — *Opalstack panel*

Create the application (Nginx Proxy Port), and note its name — that is
`${OS_APP}` — and the port it allocates. **Leave the `holdenweb.com` site
alone** — that is step 7.

### 2. Build the site — *on opal17*

The staging deploy key already serves: same host, same user, same repository.
Prove it before cloning anything:

```bash
git ls-remote git@github.com:holdenweb/holdenweb-com.git refs/heads/main
```

*Expect:* one sha, then `refs/heads/main`. `Permission denied (publickey)`
means this host has no key for the repository — see *One-time setup* above.

Then follow [`rebuild.md`](rebuild.md) Parts 2 and 3, taking `MODE=FRESH`,
from the application's directory and with this configuration in place of the
block at its top. Part 0 rehearses a site that exists; Part 1 is step 1 here.

```bash
export OS_APP=
export WEB_PORT=
export SITE_REPO=git@github.com:holdenweb/holdenweb-com.git
export SITE_DIR=site
export MODE=FRESH
export PROJECT="${OS_APP}-holdenweb-com"
export ENVIRONMENT=production
export SITE_HOST=holdenweb.com
```

```bash
: "${OS_APP:?}" "${WEB_PORT:?}" "${PROJECT:?}" "${ENVIRONMENT:?}" && echo "configuration loaded: $PROJECT"
```

*Expect:* `configuration loaded: <the app's name>-holdenweb-com`. A bare
`-holdenweb-com` means `OS_APP` was set after the block was pasted; paste the
whole block again, so `PROJECT` is rebuilt from it.

```bash
cd "$HOME/apps/${OS_APP:?}"
```

`OS_APP` and `WEB_PORT` are step 1's name and port, and `OS_APP` comes first
because `PROJECT` is built from it — the `<app>-<site>` rule that named
staging `os-holdenweb-com`. `SITE_DIR=site` because that is the path the
laptop's `production` remote names.

Then, still in `~/apps/${OS_APP}/site`, [`rebuild.md`](rebuild.md)
Part 4 — the hop count must say `1`, and `mail check` must reach Gmail — then
5.1, the administrator, and 5.2's `curl`. **Stop before 5.3**: it tests
`https://$SITE_HOST`, which is still the old site.

### 3. The first deploy — *on the laptop*

Step 1's name again, in this shell; steps 3 and 6 use it here:

```bash
export OS_APP=
```

The remote, once per clone:

```bash
git remote add production "opal17:apps/${OS_APP:?}/site"
```

If `git remote -v` already lists `production` at some other path, correct it
instead:

```bash
git remote set-url production "opal17:apps/${OS_APP:?}/site"
```

Deploy a commit staging is already running, or deploy it there first.

```bash
ops/deploy.sh --dry-run production
```

```bash
ops/deploy.sh production
```

*Expect:* `no health URL configured for production; verify it by hand`, then
`production is healthy, and running <sha>`. Only the second means anything
yet: it asked the container.

### 4. Content — *on the laptop*

```bash
just pages production
```

```bash
just pybooks production
```

```bash
just blog production
```

```bash
just notebooks production
```

Each publishes one tree from where the [`.justfile`](../.justfile) says its
source lives; a missing source says so and changes nothing. The default is a
merge, which on an empty site is the same as `--mirror`.
[`operations.md` §2](../operations.md) says what each tree is.

### 5. Look at it before anyone else can — *laptop, through a tunnel*

⚠️ This is [`operations.md` §7](../operations.md)'s phase-1 check, never yet
run. Set the port here too, then hold the tunnel open in one terminal:

```bash
export WEB_PORT=
```

```bash
ssh -N -L "9000:127.0.0.1:${WEB_PORT:?}" opal17
```

and run the suite in another:

```bash
uv run pytest tests/integration --base-url http://127.0.0.1:9000
```

*Expect:* a header naming `http://127.0.0.1:9000`, and a pass. Unverified: the
site sets `Secure` cookies once `PODPACK_ENVIRONMENT` is not `local`, and the
tunnel is plain HTTP, so a sign-in failure here may be the tunnel rather than
the site. Note which tests fail, and run them again after step 7.

### 6. Backups — *on opal17, then the laptop*

Before the site holds anything worth keeping. [`operations.md`
§4](../operations.md) installs the schedule with `crontab ops/backup.cron`,
which **replaces** the crontab — on this host, staging's schedule. Add
production's lines instead:

```bash
crontab -e
```

Append the two schedule lines from [`backup.cron`](backup.cron), with
`apps/os/site` changed to `apps/${OS_APP}/site` — the name itself, since cron
has no `OS_APP` — and each minute moved (say `47 3` and `53 4`), so the two
sites' runs do not interleave in one log.

```bash
crontab -l | grep -c scripts/backup.sh
```

*Expect:* `2`. Then prove it once by hand, from `~/apps/${OS_APP}/site` —
[`rebuild.md`](rebuild.md) 5.5:

```bash
./scripts/backup.sh && ./scripts/verify-backup.sh
```

The off-machine copy, from the laptop, in step 3's shell. The project name is
step 2's, not the `hw-holdenweb-com` [`pull-backups.sh`](pull-backups.sh)'s
header suggests:

```bash
SITE_NAME="${OS_APP:?}-holdenweb-com" ops/pull-backups.sh
```

### 7. The cutover — *Opalstack panel*

⚠️ Never yet done. In the panel, change the site that serves `holdenweb.com`
so that its root route points at `${OS_APP}` instead of the old
application. Leave the old application in place for a week: it is a better
rollback than any backup ([`operations.md` §7](../operations.md), phase 3).

```bash
curl -s https://holdenweb.com/healthz
```

*Expect:* `{"database":"ok","status":"ok"}`. The old site answers no
`/healthz`, so anything else means the switch has not taken.

### 8. Finish — *on the laptop*

Give `deploy.sh` its health URL, in `health_url()`:

```
    production) echo "https://holdenweb.com/healthz" ;;
```

Commit that, and deploy again to prove the poll:

```bash
ops/deploy.sh production
```

*Expect:* the poll passes, then `production is healthy, and running <sha>`.
Then [`rebuild.md`](rebuild.md) 5.2's browser check of `/_status`, signed in as
step 2's administrator; 5.3 against the real address —

```bash
uv run pytest tests/integration --base-url https://holdenweb.com
```

— and 5.4, the password-reset mail whose link must begin `https://`. Last, the
header of [`operations.md`](../operations.md), which says production does not
exist yet.
