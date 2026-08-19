# Operating holdenweb.com

*Written 2026-08-19, against podpack 0.8.0 and a site running on `opal17`.*

The procedures a running site needs and the site's own documentation does not
cover: backups, restores, moving hosts, rotating credentials, upgrading, and
going out of service on purpose. [`README.md`](README.md) covers development;
[`PROJECT-BRIEF.md`](PROJECT-BRIEF.md) covers what the site is; podpack's
[`README.md`](../podpack/README.md) covers the substrate.

Commands marked ✅ were run while writing this. Commands marked ⚠️ were not,
because they need the production host, and each says what remains unverified.

---

## 0. Before touching anything

Three facts that determine what is safe:

1. **`secrets.env` is the site's identity, not merely its credentials.**
   `SECURITY_PASSWORD_SALT` keys every stored password hash; `SECRET_KEY` signs
   every session and every password-reset link. Losing them is not an
   inconvenience — it is a site that can no longer verify a single login.
   **They are never regenerated on a site that has data.**
2. **`.env` is the opposite** — ports, paths, the site name, SELinux flags. It
   is *meant* to be edited, and differs legitimately between hosts.
3. **`config/`, `src/` and the alembic history are in git.** Git is their
   backup. Nothing in this document tries to duplicate it.

## 1. Where everything lives

| What | Where | Backed up by | If lost |
| --- | --- | --- | --- |
| Code, config, migrations | git (`origin`, GitHub) | git | clone again |
| Database | container, `$HOST_DATA_DIR/postgres/pgdata` | `ops/backup.sh` | users, roles, schema version |
| Page content, app data | `$HOST_DATA_DIR/apps/` | `ops/backup.sh` | **the site's content** — seeded once, edited live, nowhere else |
| Credentials and identity | `secrets.env` | `ops/backup.sh` | every password and session, irrecoverably |
| Per-host wiring | `.env` | `ops/backup.sh` (for reference) | rewrite it; nothing is lost |
| Logs | `$HOST_LOG_DIR/` | not backed up, deliberately | history only |

`hostdata/apps` is the one most easily overlooked. An app ships its content and
**seeds it once**; after that the host copy is the live one and the packaged
copy is a historical artefact ([ADR-0008](../podpack/adrs/0008-shipped-app-data-seeds-once.md)).
An app upgrade will not overwrite it — and will not restore it either.

## 2. Deploying a change

```bash
git push main main
```

⚠️ Then, **on the host**, in the site directory:

```bash
./scripts/up.sh
```

`up.sh` always rebuilds and stamps the commit into the image, so `/_status`
answers "is this running the code I am looking at?" exactly. A `-dirty` suffix
in `build_commit` means the image was built from an uncommitted tree.

Ordering is enforced by the stack, not by the operator:
`init-storage` → `postgres` (healthy) → `migrate` → `web`. A schema change is
applied by `migrate` before `web` starts; if `migrate` fails, `web` never
starts against the stale schema, which is the intended behaviour and not a
fault to work around.

> **Unverified from here:** whether the `main` remote (`opal17:apps/second-alma`)
> is bare with a checkout beside it, or takes pushes into a live worktree via
> `receive.denyCurrentBranch=updateInstead`, and whether a `post-receive` hook
> already runs `up.sh`. Confirm once and write the answer in here — it is the
> single most-repeated procedure in the document.

## 3. Verifying a deployment

Never by looking at the front page. The QR code app answered 200 for weeks
while contributing no navigation at all.

```bash
uv run pytest tests/integration --base-url https://holdenweb.com
```

Fifteen tests, driving a real browser, asking each app to do its job — generate
a code, offer both PDF forms, render a page in the site's own stylesheet. The
header names what it tested, so a suite that quietly checked the laptop instead
is visible:

```
integration target: https://holdenweb.com
```

Then, as the administrator, `GET /_status`: it reports the installed apps,
where each keeps its state, the database and role actually connected, and the
commit the image came from. It answers **404 to everyone else**, which is
correct for a page publishing that, and indistinguishable from a missing route
— so podpack also says at every boot when nobody can read it.

## 4. Backups

```bash
./ops/backup.sh
```
✅ Verified: 10,649-byte dump of 4 tables, 1.0 MB of app data, in
`~/backups/holdenweb-com/2026-08-19T165530Z/`.

It takes the three things a restore needs — the database, `hostdata/apps`, and
`secrets.env` — into one timestamped directory, then **verifies the dump before
claiming success**: `pg_restore --list` parses the whole archive, so a truncated
one fails here rather than during a restore, and an archive containing no table
data is deleted rather than kept.

| Variable | Default | |
| --- | --- | --- |
| `BACKUP_ROOT` | `~/backups/$SITE_NAME` | deliberately **outside** the repository — the directory holds `secrets.env` |
| `BACKUP_KEEP` | 14 | oldest pruned first |

Credentials never appear in the process arguments: the dump runs inside the
container using the container's own environment, so `ps` shows nothing.

### Scheduling it

⚠️ On the host, as the site's own user:

```bash
crontab -e
```

```cron
17 3 * * * cd ~/apps/second-alma && ./ops/backup.sh >> ~/backups/backup.log 2>&1
23 4 * * 0 cd ~/apps/second-alma && ./ops/restore-rehearsal.sh >> ~/backups/rehearsal.log 2>&1
```

`loginctl enable-linger` is already required for the containers to survive
logout; the same setting is what lets these run.

### Off the machine

A backup on the machine it protects is not a backup. ⚠️ From the laptop:

```bash
rsync -a --delete opal17:backups/holdenweb-com/ ~/backups/holdenweb-com-remote/
```

That directory contains `secrets.env` in clear. Keep it at 0700 on a disk you
would be willing to lose in the same sentence as your laptop, or encrypt the
copy.

## 5. Proving the backups work

```bash
./ops/restore-rehearsal.sh          # the most recent backup
./ops/restore-rehearsal.sh <dir>    # a named one
```
✅ Verified both ways: a good backup restores and reports
`rehearsal PASSED: 5 rows, 33 data files, secrets present` (exit 0); a
deliberately truncated dump reports `REHEARSAL FAILED: pg_restore reported an
error` (exit 1). No scratch database is left behind in either case.

It restores into a scratch database beside the live one, counts what came back
from the restored database's own catalogue — so a table added later appears
without editing the script — and drops the scratch database on the way out,
including after a failure. The site keeps serving throughout.

**Rehearse on the laptop where you can.** Copy a backup down and run it against
the lab stack: that exercises the transfer as well as the archive, and the
transfer is the half that fails when it matters.

`pg_restore --exit-on-error` is doing real work here. Without it pg_restore
reports every failure and still exits 0, so a rehearsal would pass on an
archive that restored nothing.

## 6. Restoring

Restoring is *rebuild the host, then put the three things back*. In order:

⚠️ 1. **Clone, and configure the host.**

```bash
git clone <this repo> && cd holdenweb.com
python3 scripts/configure-host.py --port <allocated port>
```

`configure-host.py` writes `.env` and `secrets.env` at 0600, generating fresh
secrets, detecting SELinux from `/sys/fs/selinux/enforce`, and checking the
prerequisites (Compose v2 provider, `podman.socket`, lingering). It **refuses
to overwrite** either file.

> **This site does not have that script yet** — its substrate is pinned at
> podpack 0.7.0 and `configure-host.py` arrived in 0.7.1. See §9.

2. **Replace the generated secrets with the backup's, verbatim.** This is the
   step that makes it a restore rather than a new site:

```bash
install -m 600 <backup>/secrets.env ./secrets.env
```

`.env` and `secrets.env` are independent — `.env` holds no credential — so
keeping the freshly generated `.env` while restoring `secrets.env` wholesale is
correct, and leaves the database name, role and password consistent with the
URI, because all four came from the same file.

3. **Restore the content**, before starting anything:

```bash
./scripts/prepare-host-dirs.sh
tar -xzf <backup>/app-data.tar.gz -C ./hostdata
```

4. **Start the stack.** `db-init` creates the role and database from
   `secrets.env`; `migrate` builds the schema from the alembic history.

```bash
./scripts/up.sh
```

5. **Restore the data over that schema.** The dump carries the same schema, so
   load it into a database that has one only by dropping and recreating first:

```bash
podman compose exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
podman compose exec -T postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error' < <backup>/database.pgc
podman compose restart web
```

The dump preserves ownership, and the role it names was recreated by `db-init`
from the same `secrets.env`, so the objects land owned correctly. If you are
ever restoring under a *different* role name, add `--no-owner` — and know that
you have changed the site's database identity.

6. **Verify** with §3.

## 7. Moving to another server

The whole procedure with continuity in mind. The database is small — 10 KB
dumped — so the unavoidable window is seconds, and everything else can be done
while the old host serves.

**Phase 1 — build the new host. No downtime, no hurry.**

⚠️ Steps 1–5 of §6 on the new machine, using last night's backup. Then verify
it without exposing it: `WEB_BIND_ADDR=127.0.0.1` keeps it on loopback, and an
SSH tunnel lets the integration suite reach it.

```bash
ssh -L 9000:127.0.0.1:<new port> newhost
uv run pytest tests/integration --base-url http://127.0.0.1:9000
```

A new host that has never passed the integration suite is not a candidate.

**Phase 2 — the switch.** The site has no read-only mode, so the window is
honest downtime rather than degraded service:

```bash
podman compose stop web                      # old host: stop accepting writes
./ops/backup.sh                              # old host: the final, authoritative backup
```

Copy that backup across, run step 5 of §6 on the new host, and start `web`
there. Then repoint the front end:

- **Staying inside Opalstack**: the Nginx Proxy Port application's port
  assignment is the only thing that changes. `WEB_HOST_PORT` in `.env` on the
  new host must match what they allocate.
- **Moving the domain**: drop the DNS TTL to 300 seconds *at least a day
  before* the move, or the switch is invisible for as long as the old TTL says.

**Phase 3 — after.** Leave the old host stopped but intact for a week; it is a
better rollback than any backup. Then run §5 against the new host's first
backup, because a backup regime that has not been rehearsed *on this machine*
has not been rehearsed.

Two things that must **not** change in the move: `SECURITY_PASSWORD_SALT` and
`SECRET_KEY`. `SITE_NAME` should not either — it names the compose project and
the image, and changing it makes `podman ps` on the new host describe something
that looks like a different site.

## 8. Changing the mail password

Gmail App Passwords are the usual case: revoked, rotated, or never right in the
first place.

1. Edit `MAIL_PASSWORD` in `secrets.env` on the host. Keep it to
   `[A-Za-z0-9_-]`: **`$` is expanded by compose in `secrets.env` as well as
   `.env`**, so a password containing `$HOME` arrives as something else and
   fails to authenticate with nothing said. Gmail wants its 16 letters with the
   spaces removed.
2. Restart, because `env_file` is read when a container starts:
   ```bash
   podman compose up -d web
   ```
3. Verify before a visitor does:
   ```bash
   podman compose exec web flask --app holdenweb mail check
   ```
   ✅ The command exists in the running container. It reports the server, the
   username and the *shape* of the password — never its value — then opens a
   real SMTP connection and exits non-zero on failure. The shape check exists
   because a perfectly good password taken from `passwords.google.com` instead
   of the App Passwords page fails identically to a wrong one.

`MAIL_PASSWORD` is declared in `config/app.toml` under `[site] secrets`, so the
site refuses to boot without it rather than discovering its absence when a
visitor asks for a password reset.

> **Outstanding:** `MAIL_PASSWORD` on the production host was last seen holding
> the example value. Until it is changed, password reset cannot work.

## 9. Rotating the other secrets

| Secret | Rotatable | What it costs |
| --- | --- | --- |
| `MAIL_PASSWORD` | freely | nothing; §8 |
| `POSTGRES_PASSWORD` (superuser) | with care | edit `secrets.env`, `ALTER ROLE … PASSWORD`, restart |
| `POSTGRES_APP_PASSWORD` | with care | **also** update `SQLALCHEMY_DATABASE_URI`, which embeds it — the two disagreeing is a site that starts and cannot reach its data |
| `SECRET_KEY` | technically | every session and every in-flight password-reset link is void; users are logged out |
| `SECURITY_PASSWORD_SALT` | **no** | every stored password becomes unverifiable. There is no way back but a reset for every account |

Changing an application password is two changes that must agree, so make them
together:

```bash
podman compose exec -T postgres sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER ROLE \"$POSTGRES_APP_USER\" PASSWORD '"'"'<new>'"'"'"'
# then edit BOTH POSTGRES_APP_PASSWORD and SQLALCHEMY_DATABASE_URI in secrets.env
podman compose up -d
```

Take a backup first, and rehearse it afterwards: a backup taken before the
change restores against a `db-init` that will recreate the *old* password from
the *old* `secrets.env`, which is exactly why the two are archived together.

## 10. Updating podpack and the apps

Four dependencies, all currently from git remotes: `podpack`, `podpack-pages`,
`podpack-qrcode`, `pp-pdf`. A git source resolves to what is **on the remote**,
so working locally on any of them means pushing before re-locking here.

```bash
uv lock --upgrade-package podpack --refresh-package podpack
uv sync
```

`--refresh-package` is not optional: without it uv serves a cached git ref and
the lock silently does not move. Once the apps are on PyPI and the
`[tool.uv.sources]` block goes, this becomes an ordinary version bump.

Then bring the substrate forward — a podpack release often carries container
files with it:

```bash
uv run podpack substrate status     # what the site has, versus what is installed
uv run podpack substrate diff       # file by file
uv run podpack substrate upgrade
```

Managed files sync three-way and never clobber a site edit; a genuine conflict
writes `<file>.new` and exits non-zero. `config/app.toml`, `alembic/versions/`,
`secrets.env` and the site's own scripts are never written.

Then: commit, `git push main main`, `./scripts/up.sh` on the host, §3.

> ✅ **This site is behind.** `substrate.json` pins podpack **0.7.0**, and 0.8.0
> is published. Upgrading brings `scripts/configure-host.py` — which §6 depends
> on — along with the artefact-sourced substrate and the `$`-in-a-value warning.

**What an app upgrade does not do:** deliver changed content. App data seeds
once; the host copy is the live one from then on. Content changes are made on
the host, and are what `ops/backup.sh` archives.

**Rehearse on the laptop lab first.** `podman compose up -d` locally runs the
same images from the same lockfile, and a migration that fails there fails
before it touches production.

## 11. Taking the site out of service

There is **no maintenance-page facility**, and inventing one at the moment you
need it is not the time. What actually exists:

```bash
podman compose stop web          # the site is down; nginx answers 502
podman compose start web         # back
```

The database keeps running, so backups and psql still work while the site is
down — which is the point during a migration or a restore.

For a *planned* window where a 502 is not acceptable, the front end is the
place to intervene: point the Nginx Proxy Port at a static holding page for the
duration. That is Opalstack's configuration, not this stack's, and the
containers need not stop at all.

Complete stop, including the database:

```bash
podman compose down              # containers gone; hostdata untouched
```

`down` removes containers; it does not remove `hostdata`. The distinction
matters — **`rm -rf hostdata` is what destroys the database**, and only
`podman unshare rm -rf hostdata/postgres` can do it on Linux, because the files
belong to a subuid you cannot read.

## 12. Users and administrators

flask-security's own commands, in the running container:

```bash
podman compose exec web flask --app holdenweb users create you@example.com --active
podman compose exec web flask --app holdenweb roles create admin
podman compose exec web flask --app holdenweb roles add you@example.com admin
```
✅ `users`, `roles` and `mail` are all present in the container's CLI.

`--active` is the one to remember: without it the account exists and cannot
sign in. Membership of `admin` is what `/_status` requires.

## 13. Logs, disk, and reaching the database

```bash
podman compose logs -f web                    # the server
podman compose logs migrate                   # why a deployment stopped
tail -f hostlogs/apps/<app>/<app>.log         # an app's own log
tail -f hostlogs/postgres/postgresql.log      # the database
```

Disk is worth watching: the local lab's PostgreSQL log reached 19 MB against
62 MB of data. Nothing rotates these by default.

The database publishes **no port**. When a host-side `psql` or an
`alembic revision --autogenerate` needs one:

```bash
podman compose --profile postgres-port up -d postgres-port
POSTGRES_HOST_PORT=5439 podman compose --profile postgres-port up -d postgres-port
podman compose --profile postgres-port rm -sf postgres-port
```

A shell variable beats the one in `.env`, so a one-off number needs no edit and
no restart of anything else. Most of the time no port is wanted at all:

```bash
podman compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

> `PROJECT-BRIEF.md` §3 still calls this profile `dbport`. It is
> `postgres-port`, in both the profile and the service name — the brief predates
> the rename.

## 14. When it will not come up

| Symptom | Cause | Fix |
| --- | --- | --- |
| `migrate` fails, postgres reports **healthy** | SELinux; `db-init` unreadable, so the app role was never created | `VOLUME_RW=:Z`, `VOLUME_RO=,z` in `.env` |
| `service web depends on undefined service postgres` | `COMPOSE_FILE` does not name the overlay | `COMPOSE_FILE=compose.yaml:compose.postgres.yaml` |
| Ordering ignored, containers race | `podman-compose`, not `podman compose` | install the Compose v2 provider |
| Containers die at logout | lingering off | `loginctl enable-linger <uid>` |
| `Cannot connect to Podman socket` | socket not enabled | `systemctl --user enable --now podman.socket` |
| Site authenticates against nothing; no error | a `$` in a value in `.env` or `secrets.env` | regenerate from `[A-Za-z0-9_-]` |
| alembic dies in `configparser` | a `%` in the database password, on a substrate older than 0.7.1 | upgrade the substrate |
| `/_status` 404s for you | not in `admin` | §12; the boot log says so too |
| `address already in use` | another deployment holds the port | change `WEB_HOST_PORT` / `POSTGRES_HOST_PORT` |
| Code changes have no effect | `restart` instead of rebuild — `src/` is baked into the image | `./scripts/up.sh` |
| `PermissionError` during `pytest` collection | pytest walked into `hostdata/postgres/pgdata` | `testpaths = ["tests"]` — already set here |

## 15. Rolling back

A deployment is a commit and an image, so a rollback is both:

```bash
git revert <commit> && git push main main     # then ./scripts/up.sh on the host
```

**A schema change does not roll back with the code.** alembic has the
`downgrade` direction, but the site's revisions are not written or tested for
it. If a release includes a migration, the rollback plan is *restore last
night's dump* (§6 step 5) — which is why the backup before a schema change is
the one that matters most, and why §5 exists.

## 16. The calendar

| When | What |
| --- | --- |
| Every deployment | §3 — the integration suite, against the real host |
| Nightly | `ops/backup.sh` |
| Weekly | `ops/restore-rehearsal.sh`, and eyes on the log |
| Monthly | copy a backup to the laptop and rehearse it *there* (§5) |
| Monthly | `uv run podpack substrate status`; upgrade if behind |
| Before any schema change | a backup, and a rehearsal of it |
| Yearly | move the site somewhere, on purpose, while nothing is wrong |

## 17. Known gaps

Recorded rather than hidden. None is urgent; all are real.

- **No maintenance page.** Stopping `web` gives a 502 (§11).
- **No log rotation.** `hostlogs/` grows without limit.
- **No monitoring.** Nothing notices that the site is down except a person.
  `/healthz` already answers `{"database":"ok","status":"ok"}` without
  authentication — it is what the container healthcheck polls — so an external
  check has something to ask for and nothing asks it. Note the name: it is
  `/healthz`, with no underscore, unlike `/_status`.
- **`base_url` is not set** in `config/app.toml`. Absolute URLs — password-reset
  links among them — are then built from the request, which is right only as
  long as the proxy passes the host and scheme faithfully.
- **`config/app.toml` says `environment = "local"` in production.** podpack
  reads the value but does nothing with it, so nothing is broken; it will
  mislead a reader.
- **Migrations have no tested downgrade** (§15).
- **`README.md` is stale** on dependency sources: it warns that four path
  sources need repointing at git remotes, which was done some time ago.
- **The substrate is a version behind** (§10).
