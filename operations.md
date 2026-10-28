# Operating holdenweb.com

> **Reference · for whoever is keeping this site running.** Organised by task,
> to be consulted rather than followed — the procedures it describes live in
> [`ops/`](ops/) and this explains why they are as they are. Much of it is
> podpack's rather than this site's and will move there; the paragraphs that
> name only `podpack`, the substrate or `scripts/` are the ones to take.

*Written 2026-08-19, against podpack 0.8.0 and a site running on `opal17`.
Reviewed 2026-09-21, against podpack 0.9.1 and seven installed apps. The site
this describes is **staging**, `os.holdenweb.com`. Production does not exist
yet, so every mention of it below names a target still to be created
([`ops/DEPLOY.md`](ops/DEPLOY.md)); `holdenweb.com` itself still serves the old
site and answers no `/healthz`.*

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
| Database | container, `$HOST_DATA_DIR/postgres/pgdata` | `scripts/backup.sh` | users, roles, schema version |
| Page content, app data | `$HOST_DATA_DIR/apps/` | `scripts/backup.sh` | **the site's content** — seeded once, edited live, nowhere else |
| Credentials and identity | `secrets.env` | `scripts/backup.sh` | every password and session, irrecoverably |
| Per-host wiring | `.env` | `scripts/backup.sh` (for reference) | rewrite it; nothing is lost |
| Logs | `$HOST_LOG_DIR/` | not backed up, deliberately | history only |

`hostdata/apps` is the one most easily overlooked. An app ships its content and
**seeds it once**; after that the host copy is the live one and the packaged
copy is a historical artefact ([ADR-0008](../podpack/adrs/0008-shipped-app-data-seeds-once.md)).
An app upgrade will not overwrite it — and will not restore it either.

## 2. Deploying a change

From the laptop, to staging or production:

```bash
./ops/deploy.sh staging
```

It publishes the current commit to `refs/heads/deploy/<target>` on GitHub, then
over ssh has the host fetch from its own `origin`, check that commit out
detached in `~/apps/<app>/site`, and run `scripts/up.sh`. Then it polls
`/healthz` and asks the container which commit it is running, failing unless
that is the one deployed. [`ops/DEPLOY.md`](ops/DEPLOY.md) has the one-time
per-target setup, the deploy key the host needs, and the production target.

A real checkout on the host rather than an rsync, because that is what `up.sh`
stamps the image from, so `/_status` answers "is this running the code I am
looking at?" exactly. A `-dirty` suffix in `build_commit` means the image was
built from an uncommitted tree.

Ordering is enforced by the stack, not by the operator:
`init-storage` → `postgres` (healthy) → `migrate` → `web`. A schema change is
applied by `migrate` before `web` starts; if `migrate` fails, `web` never
starts against the stale schema, which is the intended behaviour and not a
fault to work around.

Settled twice. It used to push into a live worktree via
`receive.denyCurrentBranch=updateInstead`; since 2026-09-23 the host fetches
instead, because the push silently did nothing whenever the host's HEAD was
detached ([HW-0034](adrs/0034-the-host-fetches-the-commit-it-is-told-to-run.md)).
Still no bare repo and no `post-receive` hook: the publish delivers, and a human
runs the rebuild knowing they are about to. Staging is `~/apps/os/site`;
production is its own `~/apps/<app>/site`.

### Refreshing a content tree

Content -- the files the pages, pybooks and blog apps serve -- is not in git and
does not ride a deploy; it lives in the host's `hostdata/apps/<app>/<tree>` and
is mirrored in from a staged directory by `ops/refresh-content.sh`, which must
run on the host. `ops/push-content.sh` does the whole thing from the laptop --
the transfer and that remote mirror -- taking a target the same way `deploy.sh`
does:

```bash
ops/push-content.sh staging ~/Projects/Python/orpy/python-classes \
    --app pybooks --tree html-pages --mirror
ops/push-content.sh staging ~/Projects/Python/sitescraper/build \
    --app blog --tree export --mirror
```

`--app`/`--tree` name the destination `hostdata/apps/<app>/<tree>`; `--mirror`
removes whatever the source no longer has (off by default -- an incomplete
source with it deletes live content); `--dry-run` prints the plan. Content is
live the moment it lands: the content apps read each file per request, no
restart. To refresh the **local** dev instance instead, run `refresh-content.sh`
directly against the source, same `APP`/`TREE`, no transfer.

## 3. Verifying a deployment

Never by looking at the front page. The QR code app answered 200 for weeks
while contributing no navigation at all.

```bash
uv run pytest tests/integration --base-url https://os.holdenweb.com
```

Twenty-six tests, driving a real browser, asking each app to do its job —
generate a code, offer both PDF forms, render a page in the site's own
stylesheet. The header names what it tested, so a suite that quietly checked
the laptop instead is visible:

```
integration target: https://os.holdenweb.com
```

The browsers it drives are not in the lockfile, so a machine that has never run
this suite — or one whose playwright has just moved, as it did in 47142ae —
reports `Executable doesn't exist` rather than a test failure. Once per machine,
and again after playwright changes:

```bash
uv run playwright install chromium
```

Then, as the administrator, `GET /_status`: it reports the installed apps,
where each keeps its state, the database and role actually connected, and the
commit the image came from. It answers **404 to everyone else**, which is
correct for a page publishing that, and indistinguishable from a missing route
— so podpack also says at every boot when nobody can read it.

## 4. Backups

```bash
./scripts/backup.sh
```
✅ Verified on this site: a 10,649-byte dump of 4 tables, 1.0 MB of content
across 32 entries, and `secrets.env`, in
`~/backups/holdenweb-com/20260820T190011Z/`.

The script is podpack's now, not this site's. It asks `podpack backup plan`
what this site is made of, so **installing an app changes what a backup
contains with no edit here** — and a site that later enables MongoDB gets its
documents dumped because the service catalogue knows how, not because somebody
remembered.

A backup holds the three things the site cannot be rebuilt without:

| | |
| --- | --- |
| `database.pgc` | a `pg_dump`, ownership preserved so the app role still owns its schema |
| `app-data.tar.gz` | `hostdata/apps` — the live content, which exists nowhere else |
| `secrets.env`, `env` | the identity; `secrets.env` must come back verbatim |
| `config.tar.gz`, `plan.json`, `rowcounts.txt`, `manifest.txt` | what the data means and how to check it |

`manifest.txt` records **the commit, the app list and the alembic revision**
together, because podpack's schema is a function of the app list: one alembic
history covers whichever apps are enabled, so a dump restored against a
different list leaves tables no app claims, and the next autogenerate proposes
dropping them.

| Variable | Default | |
| --- | --- | --- |
| `BACKUP_ROOT` | `~/backups/$SITE_NAME` | outside the tree, and the script refuses to write inside it |

Credentials never reach the process arguments: each dump runs inside its own
container using that container's environment, so `ps` shows nothing.

### Scheduling it

On the host, as the site's own user, install [`ops/backup.cron`](ops/backup.cron):

```bash
crontab ops/backup.cron
```

That schedules `backup.sh` (03:17) and `verify-backup.sh` (04:23), both logged
under `~/backups/`. The fragment runs in `$HOME/apps/os/site`; for production,
point it at that app's directory.

Installed on `opal17` on 2026-09-02. The first scheduled run is worth knowing
about: cron's environment carries neither `$HOME/bin` nor `XDG_RUNTIME_DIR`, so
`podman compose` resolved the wrong provider and both scripts reported the
stores down while `podman compose ps` showed them up twenty hours. The cron
file exports both now, and the host also carries a `containers.conf` provider
pin (`ops/records/backlog.md` item 31). Nothing on the laptop can see whether
it is still firing, so on `opal17`:

```bash
tail -n 20 ~/backups/verify.log
```

`loginctl enable-linger` is already required for the containers to survive
logout; the same setting is what lets these run.

### Off the machine

A backup on the machine it protects is not a backup. From the laptop:

```bash
./ops/pull-backups.sh
```

It rsyncs `opal17:backups/os-holdenweb-com/` to
`~/backups/os-holdenweb-com-remote/` (created 0700, source modes preserved).
[Its header](ops/pull-backups.sh) has the crontab line and the production
variable.

That directory contains `secrets.env` in clear. Keep it at 0700 on a disk you
would be willing to lose in the same sentence as your laptop, or encrypt the
copy.

## 5. Proving the backups work

```bash
./scripts/verify-backup.sh          # the most recent backup
./scripts/verify-backup.sh <dir>    # a named one
```
✅ Verified on this site: `4 tables carry data`, `5 rows across 4 tables`,
`32 entries`, exit 0.

It reads every archive right through — using the same tool that would restore
it, in the same container — without applying any of it. The site keeps serving
and nothing it holds is touched. Run it straight after each backup: a truncated
archive found tonight is a non-event, and the same archive found in six weeks
is a disaster.

**Know what this does and does not prove.** It proves the archives are
readable and non-empty. It does **not** prove they apply. The script this
replaced (`ops/restore-rehearsal.sh`) went further — it restored into a scratch
database beside the live one and counted the rows that came back — and the
podpack version deliberately does not, because "restore into a scratch
namespace" is not a thing every backing store spells the same way.

So the deep check is now `scripts/restore.sh` into a **scratch deployment**,
and it is the one worth putting in the calendar:

```bash
git clone <this repo> /tmp/restore-rehearsal && cd /tmp/restore-rehearsal
# edit .env for a spare port, then:
./scripts/restore.sh ~/backups/$SITE_NAME/<stamp> --yes
```

That compares every recorded row count and fails on a mismatch. It has been
exercised end to end on `podpack-demo` — five tables, real uploads, and a
marker planted after the backup that was gone afterwards — and a deliberately
tampered `rowcounts.txt` produced `MISMATCH: expected 99, found 5` and exit 1.

It has since been run against this site's own data, twice, both on `opal17`.
On 2026-08-24, from `20260823T170934Z`, every recorded row count matched
(§17). On 2026-09-03 a full rehearsal went further and verified the site it
rebuilt, which is the run that finally produced a recovery time —
[`ops/records/2026-09-03-rehearsal.md`](ops/records/2026-09-03-rehearsal.md),
with the four earlier attempts and what each of them found.

## 6. Restoring

**Run [`scripts/restore.sh`](scripts/restore.sh).** It is the procedure, not a
helper around it: 279 lines written to be run by somebody who has never seen
this site, from a checkout and a backup directory and nothing else.
[`ops/rebuild.md`](ops/rebuild.md) puts it in context — the control panel before
it, the verification after. This section is the reasoning neither can carry.

Restoring is *rebuild the host, then put the three things back*: the secrets,
the app data, the database. Everything else — `config/`, `src/`, the alembic
history — is in git, and git is its backup.

**Why the script rather than the steps.** The order is not arrangement, it is
the whole difficulty, and every part of it was paid for:

- App data is unpacked **before** the first `compose up`, because
  `init-storage` hands the bind mounts to the containers' unprivileged uids and
  is gated on `service_completed_successfully` — it does not run twice. Files
  unpacked after it are files the app cannot read.
- Each restored app's directory is **removed first**. `tar -xzf` only ever adds,
  so extracting over a live directory leaves anything created since sitting
  beside the restored files: a state that never existed, and a file deleted on
  purpose back from the dead. Measured — a marker planted after a backup
  survived the restore.
- Each store comes up **alone** first, so its own first-run bootstrap creates
  the application role the dump's objects belong to. Bringing the whole stack up
  first lets `migrate` build an empty schema the restore must then demolish —
  and demolishing it with `dropdb` discards `db-init`'s grants permanently,
  since `db-init` runs only while the data directory is empty. That is the trap,
  and it cost an evening in rehearsal 1 doing this by hand.
- The rest of the stack comes up **last**, which makes `migrate` a free
  consistency check: alembic finds the restored revision already at head, or
  rolls an older backup forward onto newer code.

**The one decision, and it is the script's first question.** `secrets.env` goes
back verbatim, which is the whole of ADR-0013: `SECURITY_PASSWORD_SALT` is
HMAC'd with every password before hashing, so a fresh salt makes every stored
password unverifiable, and a changed database identity leaves the site unable to
reach its own data. There is no partial answer — either the site keeps its
identity and everyone can still sign in, or it does not and nobody can.

**Where it needs help: a host whose port differs.** Since podpack 0.9.0b4 this
turns on what the checkout already has, and the two cases differ.

A checkout carrying its own `.env` keeps it. The backup's is written beside it
as `.env.from-backup` and the per-host keys that differ are printed, so the
closing health check polls *this* host's port and passes.

A fresh clone has no `.env` to keep, so the backup's is installed whole — with
every value in it that describes the old host named on the way past. The health
check then polls the old `WEB_HOST_PORT`, and the script exits non-zero with the
data correctly restored. Fix `WEB_HOST_PORT` and re-run `up.sh`.

`secrets.env` is replaced either way and the one displaced is kept as
`.superseded-<stamp>`; that is ADR-0013 and is not negotiable. Backlog #19,
struck.

**Then verify with §3**, against the host you just built. A suite pointed at the
old deployment passes and proves nothing.

## 7. Moving to another server

The whole procedure with continuity in mind. The database is small — 10 KB
dumped — so the unavoidable window is seconds, and everything else can be done
while the old host serves.

**Phase 1 — build the new host. No downtime, no hurry.**

⚠️ [`ops/rebuild.md`](ops/rebuild.md) Parts 1–4 on the new machine, taking the
RESTORE branch, using last night's backup. Then verify
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
./scripts/backup.sh                          # old host: the final, authoritative backup
```

Copy that backup across, run [`ops/rebuild.md`](ops/rebuild.md) 4.2 on the new
host, and start `web` there. Then repoint the front end:

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
first place. Rotate — not merely re-enter — whenever the value may have leaked,
and remember a rotation is only safe once the *old* password is revoked.

**In the Google account, first.** App Passwords exist only where 2-Step
Verification is on, for the account the site sends as — the username `mail
check` (step 3) prints. At `myaccount.google.com/apppasswords`, create a new one
(name it, say, `holdenweb SMTP`) and copy its sixteen letters. Do **not** revoke
the old one yet: a typo in the new value would otherwise lock the site out of
mail with nothing to fall back to. Revoking is step 4, once the new password is
proven live.

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
4. **Now revoke the old App Password** at `myaccount.google.com/apppasswords` —
   delete the previous entry. Until you do, the superseded (or leaked) password
   still authenticates; revoking is what turns a second working key into a
   rotation.

`MAIL_PASSWORD` is declared in `config/app.toml` under `[site] secrets`, so the
site refuses to boot without it rather than discovering its absence when a
visitor asks for a password reset.

> **Outstanding:** this belongs to whichever host is built next, production
> among them. `configure-host.py` fills `secrets.env` from the example, and the
> example carries `MAIL_PASSWORD=lab-only-not-a-real-password` — so a new host
> **boots**, because the `[site] secrets` check asks only that the name is set,
> and then cannot send a password-reset mail. `configure-host.py` reports a
> credential still at its example value as a finding; step 3's `mail check` is
> what proves the replacement works. Run it on any new host before trusting
> login.

If you are rotating because the value may have leaked — an editor state file
cached it, a backup went astray — deleting or tightening that copy is part of
the job too, or the replacement leaks by the same route. Rotating and revoking
(step 4) limits the damage; the stray copy is what caused it.

## 9. Rotating the other secrets

| Secret | Rotatable | What it costs |
| --- | --- | --- |
| `MAIL_PASSWORD` | freely | nothing; §8 |
| `POSTGRES_PASSWORD` (superuser) | with care | `\password` on the live role, and edit `secrets.env` for a future rebuild; no restart — the app never uses it |
| `POSTGRES_APP_PASSWORD` | with care | **also** update `SQLALCHEMY_DATABASE_URI`, which embeds it — the two disagreeing is a site that starts and cannot reach its data |
| `SECRET_KEY` | technically | every session and every in-flight password-reset link is void; users are logged out |
| `SECURITY_PASSWORD_SALT` | **no** | every stored password becomes unverifiable. There is no way back but a reset for every account |

Changing an application password is two changes that must agree — the role in
the running cluster and the value in `secrets.env` — so make them together and
in this order. Set the role's password with psql's `\password`, **not**
`ALTER ROLE … PASSWORD '<value>'`: `\password` prompts for the value, hashes it
in the client and sends only the hash, so the plaintext never reaches the
process arguments (where `ps` or `podman top` would show it) nor, should
statement logging ever be turned on, the server log.

```bash
# 1. Set the new password on the application role, interactively.
#    No -T: \password needs a terminal. Connect as the superuser; pg_hba trusts
#    the container's local socket, so no password is asked:
podman compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
#    then at the psql prompt, naming the application role, and \q when done:
#      \password <the POSTGRES_APP_USER value>

# 2. Edit secrets.env to the SAME new value, in BOTH lines that carry it:
#      POSTGRES_APP_PASSWORD=…
#      SQLALCHEMY_DATABASE_URI=…://<app-user>:<here>@postgres:5432/<db>
#    Keep it to [A-Za-z0-9_-]: secrets.env $-expands (§8's trap), and those
#    characters are URI-safe, so the connection string needs no escaping. A
#    generator that already obeys both: python3 -c 'import secrets; print(secrets.token_urlsafe(24))'

# 3. Recreate the containers that read the URI, so web reconnects with it:
podman compose up -d

# 4. Verify: /healthz reports the database ok, and a login works.
```

Do this promptly, end to end: between step 1 and step 3 the running `web` still
carries the old password, so *new* database connections fail until it is
recreated — existing pooled connections keep working, which is why the site does
not drop the instant you run `\password`, but do not leave it half-rotated.

The superuser (`POSTGRES_PASSWORD`) rotates the same way — `\password` for
`$POSTGRES_USER` — with one wrinkle: the cluster set that password from the
variable at first init and never re-reads it, so `\password` changes the live
cluster while the `secrets.env` edit only keeps a *future* rebuild-from-empty
consistent. The application is never given this credential, so nothing needs
restarting for it.

Take a backup first, and rehearse it afterwards: a backup taken before the
change restores against a `db-init` that will recreate the *old* password from
the *old* `secrets.env`, which is exactly why the two are archived together.

## 10. Updating podpack and the apps

Everything this site installs comes from PyPI — `podpack` and the four app
distributions alike. There is no `[tool.uv.sources]` block and no git source
left (9cd7a82, 2026-09-16), so an upgrade is an ordinary version bump:

```bash
uv lock --upgrade-package podpack-pages
uv sync
```

Two heavier traps went with the same change: a container build that resolved
against whatever happened to be on a remote at build time, and needing git and a
network in the build to do it. Working locally on an app no longer means pushing
before re-locking here — it means releasing it.

**The cache trap did not go with them, though**, and this section said it had
until 2026-09-22: that `--refresh-package` mattered only for git sources, since
"a registry version has no ref to cache". uv caches the index *listing* as well,
and a listing fetched before a release does not contain it. With podpack-pages
0.3.4 already on `pypi.org/simple` — the wheel and the sdist both visible to
`curl` — `uv lock` refused twice:

    Because only podpack-pages<=0.3.3 is available and your project depends on
    podpack-pages>=0.3.4, we can conclude that your project's requirements are
    unsatisfiable.

`--refresh-package podpack-pages` did not shift it. This did:

```bash
uv cache clean podpack-pages
uv lock
```

The tell is a refusal naming a version you know is published, and the way to
earn it is to run `uv lock` once *before* the release lands — that is the run
that caches a listing without it, which is exactly what happened here.

To move everything at once, which is how the security advisories in 47142ae
were cleared, drop the package name:

```bash
uv lock --upgrade
```

That is a larger change than it looks. It moved 28 packages, three of them
across a major version, and playwright among them — so the suite in §3 could
say nothing until its browsers were fetched. Run the unit tests, deploy to
staging, then run §3 against staging before letting such a lock go further.

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

Then commit and push, and on the host:

```bash
./scripts/up.sh
```

Verify with §3.

> ✅ **Current as of 2026-09-21**: `substrate.json` records podpack **0.9.1**,
> matching the installed library, and `podpack substrate status --check` exits
> 0. It trailed at 0.9.0b5 for five days after the site moved to 0.9.1, which
> is how the `unset CDPATH` fix to the six scripts arrived late (47142ae).
> The check is the thing to run. This note is a snapshot, and it is now the
> third one on this page to have been left behind by the tree it describes —
> which is the argument for the monthly line in §16, and for the check.

**What an app upgrade does not do:** deliver changed content. App data seeds
once; the host copy is the live one from then on. Content changes are made on
the host, and are what `scripts/backup.sh` archives.

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

### Confirming accounts, now that sign-up is public

Public registration is on and gated by email confirmation
(`SECURITY_CONFIRMABLE`): a registrant gets no session until they follow the
`https://` link mailed to them, and flask-security refuses login to any account
whose `confirmed_at` is unset. A public registrant reaches it by the mailed link;
an account left without one for any other reason cannot sign in until it is set.
So before trusting login on the deploy that first turns confirmation on, check
that no existing account was left behind -- on the 2026-09-03 deploy every one
already carried a `confirmed_at`, but the check costs nothing and the failure it
guards is a locked-out admin.

See who lacks it:

```bash
podman compose exec -T web flask --app holdenweb shell <<'PY'
from podpack.auth import user_datastore
for u in user_datastore.user_model.query.all():
    print(u.email, "confirmed" if u.confirmed_at else "UNCONFIRMED")

PY
```

If any read UNCONFIRMED, set a timestamp -- grandfathering accounts made before
there was a step to follow. Mind the blank line after the loop: `flask shell` is
a REPL, so the loop needs one to close before the dedented `db.session.commit()`,
or it stops with an IndentationError:

```bash
podman compose exec -T web flask --app holdenweb shell <<'PY'
from datetime import datetime, timezone
from podpack import db
from podpack.auth import user_datastore
n = 0
for u in user_datastore.user_model.query.filter(user_datastore.user_model.confirmed_at.is_(None)):
    u.confirmed_at = datetime.now(timezone.utc)
    n += 1

db.session.commit()
print(f"confirmed {n} account(s)")
PY
```

It is idempotent -- an account that already has a `confirmed_at` is not in the
loop -- so re-running it is safe.

## 13. Logs, disk, and reaching the database

```bash
podman compose logs -f web                    # the server
podman compose logs migrate                   # why a deployment stopped
tail -f hostlogs/apps/<app>/<app>.log         # an app's own log
tail -f hostlogs/postgres/postgresql.log      # the database
```

Disk is worth watching, though PostgreSQL's log is now bounded:
`config/postgresql.conf` writes `postgresql-Mon.log` through
`postgresql-Sun.log` and truncates each on reuse, so a week is the most that
accumulates. Bounded is not small — the seven files in this laptop's lab total
93 MB. The app logs under `hostlogs/apps/` have no rotation at all, and the
setting reaches a host only on a deploy followed by a postgres restart.

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
git revert <commit> && ./ops/deploy.sh staging     # push, rebuild, health-check
```

**A schema change does not roll back with the code.** alembic has the
`downgrade` direction, but the site's revisions are not written or tested for
it. If a release includes a migration, the rollback plan is *restore last
night's dump* ([`ops/rebuild.md`](ops/rebuild.md) 4.2) — which is why the
backup before a schema change is
the one that matters most, and why §5 exists.

## 16. The calendar

| When | What |
| --- | --- |
| Every five minutes | the health poll (§18), unattended — **not running yet** |
| Every deployment | §3 — the integration suite, against the real host |
| Nightly | `scripts/backup.sh`, then `scripts/verify-backup.sh` |
| Monthly | `scripts/restore.sh` into a scratch deployment — the only deep check (§5) |
| Monthly | copy a backup to the laptop and rehearse it *there* (§5) |
| Monthly | `uv run podpack substrate status`; upgrade if behind |
| Before any schema change | a backup, and a rehearsal of it |
| Yearly | move the site somewhere, on purpose, while nothing is wrong |

## 17. Known gaps

Recorded rather than hidden. None is urgent; all are real.

- **No maintenance page.** Stopping `web` gives a 502 (§11).
- ~~**No log rotation.**~~ **Closed:** `config/postgresql.conf` rotates on
  day-of-week filenames with truncation, so Postgres logs are bounded to a week
  (seven files). Reaches os on the next deploy plus a postgres restart; podpack's
  substrate carries the same change to other sites on their next upgrade.
- **App logs are not rotated.** The closure above is PostgreSQL's alone: podpack
  attaches a plain `logging.FileHandler` (`paths.py:113`), so
  `hostlogs/apps/*.log` still grows without limit (backlog item 9).
- ~~**No monitoring**, until §18 is actually set up.~~ **Closed 2026-09-22**:
  UptimeRobot checks `https://os.holdenweb.com/healthz` every five minutes and
  mails on failure, proven against the real deployment — postgres stopped, mail
  received (backlog item 8).
- ~~**Password-reset links go out as `http://`.**~~ **Closed 2026-08-24**:
  `.env` sets `PODPACK_PROXY_HOPS=1`, the container reads it, and `/_status`
  reports `scheme: https`. **And closed again, differently, 2026-09-22**: the
  count is now derived from `PODPACK_ENVIRONMENT`, so a rebuild cannot forget
  it and the explicit line is redundant rather than load-bearing
  (podpack ADR-0039, backlog item 32). Two things follow. This host keeps its
  line until somebody removes it, and it still wins, so nothing changes on the
  next deploy. And the rebuild no longer *sets* the value: `ops/rebuild.sh`
  asks the running site what it concluded and fails if that is zero, which
  catches the misconfiguration however it arose. Not `base_url`, which was
  recorded as the fix for two days and feeds nothing that builds these links.
  The host in the link is already right and must stay dynamic: Opalstack owns
  the binding. `ops/records/backlog.md` item 4 has the whole correction.
- ~~**`config/app.toml` says `environment = "local"` in production.**~~
  **Closed**: the dead `environment` key was removed from `config/app.toml`
  (commit 1929993).
- **Migrations have no tested downgrade** (§15).
- ~~**`restore.sh` has never been run against this site's data.**~~ **Closed
  2026-08-24.** It has now, on the Opalstack host, from
  `20260823T170934Z`: `app.alembic_version` 1, `app.role` 1, `app.roles_users`
  1, `app.user` 2 — every count matching what the backup recorded, and the app
  data unpacked without error. It took three attempts to get there, and the two
  that failed were worth more than the one that worked: the first found that
  `restore.sh` could not run on Linux at all, and the second that a document
  describing it can be wrong in ways only a real host reveals.
- ~~**`README.md` is stale** on dependency sources: it warns that four path
  sources need repointing at git remotes, which was done some time ago.~~
  **Closed**: that warning is gone from `README.md`.
- ~~**The substrate is a version behind**~~ **Closed 2026-09-21**:
  `substrate.json` records `0.9.1`, matching the installed library, and
  `substrate status --check` exits 0 (§10). It had closed once before and
  reopened when the site moved to 0.9.1 without the matching `substrate
  upgrade`, so the line to trust is the check, not this one.
- ~~**CI has never run.**~~ **Closed 2026-09-21**: every run since the workflow
  was added in July failed, and none of them ran a test. `SQLALCHEMY_DATABASE_URI:
  sqlite:///:memory:` is not a string to YAML — the trailing colon makes it a
  mapping — so the file never parsed, and GitHub reported `failure` with zero
  jobs, naming the workflow by its path rather than its `name:`, which is what
  it does when it cannot read one. Two months of pushes went untested, and the
  trap was that the Actions list was never empty: some forty runs appeared
  there, each red for a reason nobody opened. Quoting the value fixed it
  (a64dac5).
  What now runs is the unit suite against SQLite; the site runs PostgreSQL, and
  podpack's own `ci.yml` has the service-container pattern if that gap is worth
  closing. The lesson is the general one: a check nobody has watched fail is a
  claim, not a check.

---

## 18. Noticing that the site is down

Today a person notices. Everything else in this document assumes somebody
already knows something is wrong, which makes this the gap that lengthens every
other procedure.

`/healthz` answers `{"database":"ok","status":"ok"}` without authentication —
it is what the container healthcheck polls — so there is nothing to build.
**Note the name: `/healthz`, no underscore.** `/_status` is the other one, it
is richer, it requires an operator, and it is not what to poll.

### Two checks, because they fail differently

1. **From outside**, against `https://os.holdenweb.com/healthz`, expecting 200
   *and* `"status":"ok"` in the body. Matching the body is not fussiness: nginx
   will happily return 200 from its own error page with the container gone.
   This is the one that catches DNS, the proxy and a broken certificate, none of
   which anything on the host can see. It is
   [`ops/poll-health.sh`](ops/poll-health.sh), run from the laptop or another
   machine (its header has the crontab line and the target variable); a hosted
   uptime service would do the same, independently of your own machines.

2. **On the host**, which catches the opposite case — a `web` container that is
   unhealthy behind a proxy still answering convincingly. Five-minutely, and
   quiet unless it fails:

   ```cron
   */5 * * * * cd ~/apps/os/site && . ./.env && \
     curl -fsS --max-time 10 "http://${WEB_BIND_ADDR:-127.0.0.1}:${WEB_HOST_PORT}/healthz" \
     | grep -q '"status":"ok"' \
     || echo "holdenweb /healthz failed at $(date -Is)" \
     | mail -s "holdenweb.com unhealthy" steve@holdenweb.com
   ```

   ⚠️ Not yet installed, and it depends on §8 being done first: the mail it
   sends goes through the same credential the site does.

### Prove it before believing it

Stop `web`, wait for the interval, and confirm the alert arrives. Then start it
again. A monitor nobody has seen fire is in exactly the position a backup
nobody has restored was in before §5 existed — and that comparison is the
reason this section says so rather than assuming.

## 19. Troubleshooting: what a message means

When a line prints that you do not recognise, look it up rather than guess.
[`ops/messages.html`](ops/messages.html) — **The 3am Almanac** (published at
https://claude.ai/code/artifact/c51a17b1-44f9-4d85-be38-155e1745543d) — is a
searchable catalogue of every message this system is likely to emit: from the
deploy and backup scripts, the app at boot, PostgreSQL, and the
`git`/`uv`/`podman` tools. Paste the line you are staring at and it narrows to
the entry, telling you where it comes from, how serious it is, and what to do —
filterable by severity, and by whether it fires on the laptop or the host.

On the host, where there is no browser, the same catalogue is
[`ops/MESSAGES.md`](ops/MESSAGES.md) — grep it. Both are generated from
`ops/messages.json` by `ops/build-messages.py`; edit the JSON and re-run to keep
them current.
