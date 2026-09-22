# Backlog: findings awaiting an issue

> **Record · append-only, for whoever is deciding what to fix next.** Never
> followed and never rewritten except to strike an item with its evidence. The
> **Repo** column is the destination: podpack's items become podpack issues, and
> extracting them is a filter on that column rather than a reading of the whole
> list.

*Raised 2026-08-19, while writing [`operations.md`](../../operations.md). Held
here for triage into GitHub Issues — both `holdenweb/holdenweb-com` and
`holdenweb/podpack` have Issues enabled and are currently empty, so nothing has
been filed yet. Items 28 and 29 belong to a third repository,
`holdenweb/podpack-pages`, whose Issues have not been checked.*

Each item names the repository it belongs to, the evidence that it is real, and
what fixing it involves. **Tier 1** was found while writing the playbook;
**Tier 2** is the standing known-gaps register from
[`operations.md` §17](../../operations.md), recorded here so the two lists do not
drift apart.

| # | Repo | Item | Kind |
| --- | --- | --- | --- |
| 5 | holdenweb-com | `PROJECT-BRIEF.md` names the profile `dbport`; it is `postgres-port` — **fixed** | docs |
| 6 | holdenweb-com | `README.md` stale on dependency sources — **fixed** | docs |
| 7 | holdenweb-com | `environment = "local"` in the production config — **fixed** | cosmetic |
| 8 | holdenweb-com | External monitoring: UptimeRobot checks `/healthz` every five minutes over HTTPS and mails on failure, proven by a real outage — **fixed** | gap |
| 9 | holdenweb-com | No log rotation for app logs (PostgreSQL's now rotates) | gap |
| 10 | holdenweb-com | No maintenance page | gap |
| 11 | holdenweb-com | Migrations have no tested downgrade | gap |
| 14 | podpack | `backup.sh`'s working-tree guard fails open — **fixed** | security |
| 15 | podpack | `/_status` `stored_files` cannot see a directory — **fixed** | correctness |
| 16 | podpack | Recreating the database leaves a site that can never migrate — **fixed** | operational |
| 18 | podpack | Container paths name holdenweb for every site — **fixed** | cosmetic |
| 19 | podpack | `restore.sh` replaces `.env`, so a restore gives the checkout the backup's `SITE_NAME` — **fixed** | operational |
| 20 | podpack | `backup.sh`'s cross-deployment guard is inert on most sites — **fixed** | security |
| 21 | podpack | `manifest.txt`'s `running build` can never be populated — **fixed** | correctness |
| 22 | podpack | A failed restore leaves a plausible backup that verifies clean — **fixed** | operational |
| 23 | podpack | `restore.sh` could not work on Linux — **fixed** | operational |
| 25 | holdenweb-com | `security/base.html` is a fork of `base.html`, not a child — **fixed** | correctness |
| 26 | podpack | Every `up` builds the same image twice — **fixed** | efficiency |
| 27 | podpack | Navigation is one level deep, so an app's pages hang off the root | gap |
| 28 | podpack-pages | A link between pages is rewritten to the asset route, losing the site — **fixed** | **correctness** |
| 29 | podpack-pages | A directory has no index, so it cannot be landed on — **fixed** | gap |
| 30 | podpack | No shared decorator for operator-only routes: `/config` hand-rolls the `/_status` guard (`extensions["podpack"].admin` + `abort(404)`), because flask-security's `roles_required` 403s and bypasses the replaceable admin predicate. A `@operator_required` in podpack would remove the copy -- low priority until a third such route wants it — **fixed** | gap |
| 31 | podpack | `configure-host.py` detects a non-v2 `podman compose` provider but only warns; it should pin it in `containers.conf` so cron and ssh-deploy cannot silently fall back to the gate-ignoring `podman-compose` | operational |
| 32 | podpack | `PODPACK_PROXY_HOPS` should be *derived* from `PODPACK_ENVIRONMENT` (0 for local, 1 for staging/production) rather than set and delivered by hand | operational |
| 33 | podpack | The `web` healthcheck pings every 10s (`compose.yaml:160`); widen to 150s for a quiet site and tighten when it matters | operational |
| 34 | holdenweb-com | `/config` serialises the whole Flask config -- `SECRET_KEY`, `MAIL_PASSWORD`, the DB URI -- unredacted even to an admin; redact by key name — **fixed** | security |
| 35 | holdenweb-com | Unverified: does the `os` stack auto-start after an Opalstack host reboot? Rides `loginctl` linger + `restart: unless-stopped`, never seen through a real reboot; a silent no-return is what MON-1 must catch | gap |
| 36 | holdenweb-com | `refresh-content.sh --mirror` deletes live content with no confirmation of its own; `push-content.sh` guards the remote path it drives, but a direct host run of `refresh-content.sh` does not -- give it the same tty-gated typed-`mirror` prompt `restore.sh` and `push-content.sh` use — **fixed** | operational |
| 37 | podpack-notebooks | `notebooks.yaml` points at notebook source files wherever they live (now `~`/absolute paths too), so a published notebook depends on that source staying put through ordinary development. Optionally vendor a local copy into the repo so publication survives churn -- deferred, because it brings name-collision handling and its own curation questions; keep it simple for now | gap |
| 38 | holdenweb-com | `refresh-content.sh`'s `--mirror` prompt was not tty-gated, so a non-interactive mirror aborted -- including the remote path `push-content.sh` drives over ssh — **fixed** | operational |

*Numbers are stable identifiers, so a gap means an item was struck rather than
renumbered.*

**Struck:** **24** — the admin role did survive: signed in on the rebuilt site,
`/_status` answers 200 with JSON (2026-08-24). The 404 that raised it was the
other of the two accounts, exactly as the backup's one role and one membership
suggested. Filed as *possible* and closed as not-a-bug, which is the right way
round for something seen once. **13** — the navigation is now on every page, by way of a
`nav.html` partial the front page, `base.html` and `security/base.html` all
include (2026-08-24). What made it more than a one-line change is filed as 25.
**1** — `MAIL_PASSWORD` was already correct in production;
`configure-host.py --check` reported no credential still at its example value
and `mail check` opened a real SMTP connection (rehearsal 1, 2026-08-23). It had
been carried as the most urgent open item for four days and was not open.
**2** — substrate now at podpack 0.9.0b2 (2026-08-20). **3** — `pp-pdf` carries
one `r*` tag matching its version, on `origin` as well as locally (2026-08-21).
**17** — a build in one checkout does *not* tag another's image. Measured
2026-08-23: identical content built under two site names yields one image ID
with two tags, which is all rehearsal 1's log showed, and podman lists every tag
on an ID. Build differing content and the tags separate onto different IDs
correctly. The item was inferred from log output rather than measured, and was
wrong. **4** — reset links now carry `https://`; `/_status` reports
`proxy.hops_trusted: 1` and `proxy.scheme: "https"`, and a real reset mail was
read (rehearsal 1, 2026-08-23). **12** — ADR-0027's stale profile name
(2026-08-20).

---

## Tier 1 — found 2026-08-19

### 5. `PROJECT-BRIEF.md` names the database-port profile `dbport`

**Repo:** holdenweb-com

**Fixed 2026-08-26.**

*Evidence.* `PROJECT-BRIEF.md:103` — the entry said 96, which had drifted —
gave `podman compose --profile dbport up -d dbport`. `compose.postgres.yaml`
defines the service as `postgres-port` with `profiles: ["postgres-port"]`. The
brief predates the rename.

*Why it matters.* The command as written does nothing and says nothing useful,
in a document whose purpose is briefing somebody who does not already know.

*What shipped, and it was three places rather than one.* The brief's command,
corrected and moved into a fenced block of its own — it was inline in a sentence
that ended with a full stop, which is how a stray `.` reached a live host once
before. `operations.md` §13 carried a note recording this very discrepancy,
which goes with it. And `compose.postgres.yaml:73` still said "see the `dbport`
service below": that file is VERBATIM substrate, so it was fixed in podpack
(`c9c6dfb`) and reaches this site on the next `substrate upgrade`.

### 6. `README.md` is stale on dependency sources

**Repo:** holdenweb-com

**Fixed 2026-08-26.**

*Evidence.* `README.md` — "building currently requires the three path-sourced
dependencies (podpack, podpack-pages, podpack-qrcode, pp-pdf) to be repointed at
git remotes and re-locked". They were already git-sourced, and there were four
of them, not three.

*Why it matters.* It describes a blocker that no longer exists, and miscounts
what it lists — so a reader either does unnecessary work or stops trusting the
document.

*Fix.* Delete the note. It becomes wrong again shortly, when the git sources
are retired in favour of PyPI version specs.

*And it had.* By the time this was struck the note was wrong a third way:
podpack is a PyPI version spec (`podpack>=0.9.0b4`), while podpack-pages,
podpack-qrcode and pp-pdf are still git-sourced under `[tool.uv.sources]`. Three
readings of one sentence, all of them wrong, which is the argument for deleting
rather than re-writing it. Nothing replaces it: `pyproject.toml` says where each
dependency comes from, and says it in a form that cannot go stale.

### 7. `environment = "local"` in the production configuration

**Repo:** holdenweb-com

**Fixed 2026-08-26** in podpack `ec3a58e`, and here by removing the key.

*Evidence.* `config/app.toml:6`. The file is bind-mounted read-only from git,
so production reads the same value the laptop does.

*Two things this entry got wrong*, both found when it came to be fixed. podpack
did **not** read `environment` — nothing in `src/podpack/` referenced the key at
all. And `/_status` did not report it, so the "next person to read it" would
have had to open `app.toml` on the host to see it. The item was real and its
consequences were smaller than recorded.

*Why it matters.* Nothing is broken. But `/_status` on the production host says
the site thinks it is local, and the next person to read it will spend time
establishing that this is harmless.

*Fix.* Either make the value meaningful (per-host, which means it stops being a
committed file's business) or remove it. Removing it is the smaller lie.

*What shipped is the first of those.* `PODPACK_ENVIRONMENT` now lives in `.env`,
per deployment, and the key is gone from `app.toml`.

It decides one thing, and less than was hoped. Compose reads `.env` directly for
its bind mounts and cannot branch on a variable, so this can never *derive*
`HOST_DATA_DIR` and `HOST_LOG_DIR` — only be checked against them.
`prepare-host-dirs.sh` now refuses when a deployment that is not a lab is about
to keep its data inside the checkout, which every deployment created from
`env.example` does: it ships `./hostdata` and `./hostlogs`, and shows
`/srv/<site>/data` only in a comment. The directories are gitignored, so nothing
risks being committed — the data risks a `git clean -fdx`, a fresh clone, or
[`rebuild.sh`](../rebuild.sh), which removes the site directory outright.

Unrecognised values count as **not** local, so a typo refuses rather than
quietly demoting a real deployment to a lab. Unset means local, so no existing
site breaks before its next `substrate upgrade` delivers the line.

*A side finding worth more than this item.* ADR-0037 argues that `.env.example`
must retire because it is a seeded file that can never deliver a new variable to
an existing site. It is not seeded — it has been CONFIG since the substrate
first shipped, with append-only delivery into the live `.env` from the same day.
Measured: `substrate status` on a real site reports `new variables pending:
PODPACK_ENVIRONMENT`. The ADR is still Proposed and decision 4 wants revisiting
on that basis.

---

## Tier 2 — standing gaps, from `operations.md` §17

### 8. Nothing polls `/healthz`

**Repo:** holdenweb-com. The endpoint already answers
`{"database":"ok","status":"ok"}` without authentication — it is what the
container healthcheck uses — so external monitoring has something to ask and
nothing asks it. Today the site being down is noticed by a person. *(Note the
name: `/healthz`, no underscore, unlike `/_status`.)*

**Fixed 2026-09-22.** UptimeRobot checks `https://os.holdenweb.com/healthz`
every five minutes over HTTPS and mails on failure, proven against the real
deployment rather than asserted: postgres stopped, mail received. The site being
down is no longer something a person notices. The one point below still unticked
-- a production `HEALTH_URL` -- rides on a production deployment that does not
exist yet, so it is not an open gap in what is running. Written up in the
README's Monitoring section.

*Progress 2026-09-02, parked here to revisit before there are paying customers.*
The **asking half now exists**: [`ops/poll-health.sh`](../poll-health.sh)
(committed, pushed) fetches `HEALTH_URL` (default `https://os.holdenweb.com/healthz`)
and asserts the body carries `"status":"ok"` rather than trusting the status
code — nginx answers 200 from its own error page with the container gone, so a
200 alone is not health. A non-2xx, a hang past `--max-time`, or a bad TLS
certificate all count as failure; it is silent on success, so a scheduler only
ever fires on a real fault, and `ALERT_CMD` routes the failure message wherever
it is pointed. What is **still outstanding**:

- **A home that is neither the host nor a sleeping laptop.** The poll sees only
  what it sees from where it runs, and a laptop asleep at the polling minute is a
  blind monitor whose silence is indistinguishable from health. An always-on
  vantage is wanted; a hosted uptime service is the strong form, because it also
  alerts when the poll *itself* stops — a dead-man's-switch a self-run cron
  cannot manage.
- **An alert channel wired into `ALERT_CMD`** (ntfy, Pushover, mail) so a 3am
  failure reaches a phone rather than a logfile nobody is reading.
- **A schedule on that machine**, after the host's 03:17/04:23 backup window.
- **The proof the plan asks for:** stop `web`, watch the alert fire, restart,
  watch recovery. Until that has been done once, the poll is a claim.
- **The production `HEALTH_URL`** once a production deployment exists; the
  default targets staging `os.holdenweb.com`.

Rehearsing the fire-and-recover loop from the laptop proves the mechanism; it is
the *standing* home that wants to be always-on.

*Progress 2026-09-22.* The poll has a caller now. `ops/deploy.sh` runs it
against the target after the rebuild (`HEALTH_URL="$hu" poll-health.sh`), and a
non-zero exit is the signal that the deploy did not come up -- described that way
in [`ops/DEPLOY.md`](../DEPLOY.md). So the script is exercised for real on every
deploy rather than sitting unused, and its success path has stopped being a
claim.

It does not close this item, and it is worth saying why rather than letting the
row look healthier than it is: a check at deploy time is not a monitor. It
answers "did this deploy come up?", where the question here is "is the site up
*now*", asked on a schedule from somewhere always on. Between deploys nothing
asks. All five points above stand, and the failure path -- an alert actually
reaching a phone -- is still the untested half.

*Progress 2026-09-22, and this is the big one.* **UptimeRobot now checks
os.holdenweb.com at five-minute intervals** (Steve). That closes the first and
hardest of the five points above, and closes it in the form this item argued
for: a hosted service, not a cron on a laptop, so it also alerts when the poll
*itself* stops — the dead-man's-switch a self-run schedule cannot manage. The
site going down is no longer something a person notices.

What is still owed, in the order it matters:

- **Point it at `/healthz`.** The monitor is SSL plus a 2xx on the site root
  (Steve, 2026-09-22), and measured on the laptop lab the same day -- full
  stack up, `podman compose stop postgres`, probe, restart -- that is not
  enough:

  | | database up | database stopped |
  | --- | --- | --- |
  | `/` | 200 | **200** |
  | `/pages/test` | 200 | **200** |
  | `/login` | 200 | **200** |
  | `/healthz` | 200 | **503** |

  So the monitor as configured reports green straight through a total database
  outage, with login, sessions and password reset broken behind a front page
  that still renders. Changing the monitored URL to
  `https://os.holdenweb.com/healthz` is the whole of the fix, and it needs no
  keyword check: the endpoint answers 503, so the default 2xx test is exactly
  right once it is asking the right question. (`/healthz` keeps its 200 for a
  non-fatal *app* failure by design -- ADR-0030 -- so this catches the fatal
  case, which is the one that takes the site with it. `poll-health.sh` greps
  the body because it also wants the degraded-app case.)

  Recovery was measured too: restarting postgres returned `/healthz` to 200
  within about three seconds, unattended.
- **The fire-and-recover proof: DONE 2026-09-22.** Steve stopped the postgres
  service on the deployment and the outage arrived by email. That is the half a
  monitor can only earn on a real failure, and it has now been earned against
  the real thing rather than the lab.

  The monitor had been moved to `/healthz` first (Steve, 2026-09-22, on the
  strength of the measurement above), which is why the alert fired at all: the
  root would have answered 200 throughout.
- **A production URL**, once a production deployment exists.

`ALERT_CMD` is moot for this path: UptimeRobot carries its own alerting. It
still matters for `poll-health.sh`, which remains the deploy-time gate.

### 9. No log rotation

**Repo:** holdenweb-com. `hostlogs/` grows without limit; the laptop lab's
PostgreSQL log reached 19 MB against 62 MB of data. Nothing prunes it.

*Progress 2026-09-18.* The PostgreSQL half is done, and it was the half that
prompted this: `config/postgresql.conf` sets `logging_collector = on`,
`log_filename = 'postgresql-%a.log'`, `log_rotation_age = 1d` and
`log_truncate_on_rotation = on`, so that log rotates day-of-week and is
overwritten a week later instead of growing. What remains is the app logs:
podpack attaches a plain `logging.FileHandler` (`paths.py:113`), so
`hostlogs/apps/*.log` still grow without limit. The item stands, narrowed to that.

### 10. No maintenance page

**Repo:** holdenweb-com. Stopping `web` yields a 502 from nginx. A planned
window currently has to be handled at the front end, by pointing the Nginx
Proxy Port at a holding page — which works, but is not written down anywhere as
a procedure and has never been rehearsed.

### 11. Migrations have no tested downgrade

**Repo:** holdenweb-com. alembic has the direction, but the site's revisions are
not written or tested for it, so the rollback plan for any release carrying a
schema change is *restore last night's dump*. That is workable and is what
[`operations.md` §15](../../operations.md) says — it is also the reason the backup
before a schema change is the one that matters most.

---

## Raised since — 2026-08-21

*Empty. Nothing raised on this date is still open, and every number issued is
accounted for — either by a section below or by the struck list above.*

---

## Raised 2026-08-23, by the first rebuild rehearsal

*None of these were findable by reading. Each came from running the procedure on
a real host; the run is kept at [`2026-08-23-rehearsal.md`](2026-08-23-rehearsal.md).*

### 14. `backup.sh`'s working-tree guard fails open

**Repo:** podpack — was **the one to fix first**. **Fixed 2026-08-25 in
`442e65e`**, together with item 20: same file, same mistake, one editing session.

*Evidence.* `scripts/backup.sh:54` resolves the destination's parent with
`$(cd "$(dirname ...)" && pwd)` to check it is outside the site directory. When
that parent does not exist, `cd` fails, `&& pwd` never runs, the substitution is
empty, and the comparison is `/` against the site path — no match, no refusal.
Demonstrated. Rehearsal 1 hit the precondition on its first run:
`cd: /home/sholden/backups: No such file or directory`, printed and ignored.

*Why it matters.* The guard exists to stop a directory holding a verbatim copy
of every secret landing inside a git repository — "one careless `git add` away
from being published", in its own comment. A guard that fails open is worse than
no guard, because it is trusted.

*What shipped.* `realpath` by python, which answers for a path that does not
exist — removing the reason `dirname` was there at all — with both values in
assignments so a failure now aborts instead of passing. That also fixed a second
defect on the same line, unmentioned above: it resolved `dirname` of the
destination rather than the destination, so an absolute path naming the site
directory itself resolved to the site's *parent*, matched nothing, and put the
backup straight into the tree.

*Worth noting for whoever reads this next.* The exposure was narrower than it
looks — the seeded `.gitignore`'s line 4 is `secrets.env`, unanchored, which git
matches at any depth. What the defect actually destroyed was the guarantee
[`operations.md` §6](../../operations.md) states flat: "outside the tree, and the
script refuses to write inside it". That sentence is what makes an operator
willing to aim a backup somewhere unusual, and it was true of the intent and
false of the code.

*Still open.* podpack's seeded `.gitignore` has no `backups/` entry, so a new
site has no second line of defence if this guard is ever wrong again.
holdenweb.com added one by hand.

### 15. `/_status` reports `stored_files` as top-level files only

**Repo:** podpack — **fixed 2026-08-26 in `c3d2c0c`.**

*Evidence.* `src/podpack/core.py:295` — `iterdir()` filtered to `p.is_file()`.
Production reports `"stored_files": []` for `pages`, which holds 1.0 MB in
subdirectories.

*Why it matters.* `core.py` says the field sits beside `backs_up` because "an app
claiming to store nothing while listing files is the contradiction podpack warns
about at boot". The boot check itself (`registry.py`, `_check_backup_claim`) has
no such filter and is correct — so `/_status` shows a weaker view than the check
uses. An app declared stateless on that evidence would drop its content from
every backup, silently, until somebody tried to restore.

*What shipped was both.* The filter is gone and the field is `site_content`,
renamed with the fix rather than after it — "files" was the word that made the
filter look correct. Files and directories are listed together with no
distinction drawn: the question the field answers is "is there anything here?",
which is what a backup asks of the directory as a whole.

*The measurement.* `hostdata/apps/pages` on this site holds three directories,
**zero** top-level files and 1.2 MB. The old field reported `[]` for that.

*Corrected while fixing it.* Nothing is dropped from any backup by this today,
and the entry can be read as saying otherwise. `_check_backup_claim` never had
the filter, so a stateless claim contradicted by a subdirectory is still warned
about at every boot, and `backup.sh` still writes `SKIPPED, declared stateless`
into the manifest. Two independent notices would have had to go unread before
data actually went missing. What the defect did was make the *authoring*
decision harder than it needed to be — podpack disagreed with itself, and the
weaker answer was the one on the page people read.

*Left open deliberately.* The listing raises `FileNotFoundError` if the data
directory is missing, where `data_dir_writable` beside it degrades to `false`.
The directory is created at startup, so getting there takes something unusual.

### 16. Recreating the database leaves a site that can never migrate again

**Repo:** podpack — observed on a real deployment 2026-08-24, having been filed
on 2026-08-23 as a milder thing than it is. **Fixed 2026-08-25 in `ac40092`**,
by the narrow route below.

*Evidence.* `db-init/01-create-app-user.sh` runs only while the postgres data
directory is still empty. It is what creates `SCHEMA app AUTHORIZATION <app
role>`, and it sets `search_path = app` **on the role**, which is cluster-level
and outlives any database.

So `dropdb` takes the schema with the database, `createdb` returns one holding
only `public`, and `db-init` never runs again. The role is left pointing at a
schema that no longer exists. Every `CREATE TABLE` then fails, including
alembic's very first:

```
psycopg2.errors.InvalidSchemaName: no schema has been selected to create in
LINE 2: CREATE TABLE alembic_version (
```

Confirmed by query on the affected host: `pg_namespace` had **no `app` row at
all**.

*Why it matters, and it is worse than "grants are discarded".* There is no path
back. `up.sh` cannot fix it, because the only thing that creates the schema is
gated on an empty data directory. The site is permanently unable to migrate, and
the message names neither `app`, nor `db-init`, nor the fact that a bootstrap is
missing — PostgreSQL is reporting that it walked `search_path` and found nowhere
it was allowed to create, which is true and unhelpful. Two evenings went to this
in two different disguises: once as an ownership fault after
`pg_restore --no-owner`, once as an absent schema.

*What shipped.* The narrow fix: `alembic/env.py` asks `current_schema()` before
anything touches the database and refuses when it is NULL, naming the
search_path in force, db-init, the `CREATE SCHEMA` that repairs it, where the
application role's name is written down, and the fact that `restore.sh` avoids
the trap. It refuses rather than repairing — creating the schema needs superuser
rights the migration does not have, and inventing the missing half of a
bootstrap would hide how the site got here. Reproduced against a real
PostgreSQL and the three tests fail against the previous env.py.

*Still open, and worth its own item when someone wants it.* The real fix is a
re-runnable bootstrap, so recreating a database is recoverable rather than
terminal. `db-init` is already idempotent in shape; what stops it is the image
entrypoint's condition, which podpack does not control. A `podpack db bootstrap`
verb would. The site is still down when this fires — `web` is gated on `migrate`
completing — so all that has changed is that the operator now knows why.

*Meanwhile* `restore.sh` avoids the trap entirely by bringing each store up
alone so its own bootstrap runs first, which is why the documented restore path
does not hit this and a hand-run one does.

### 18. Every podpack site's containers are named after holdenweb

**Repo:** podpack — **fixed 2026-08-26 in `77aefce`.**

*Evidence.* `substrate/data/compose.yaml:119-120` hardcodes
`/var/lib/holdenweb/apps` and `/var/log/holdenweb/apps`, and
`src/podpack/__init__.py:59-60` defaults to the same. Verified by building a
site called `mysite` from `creating-a-site.md`: it gets holdenweb's paths.

*Why it matters.* Harmless inside a container, but a new site's `/_status`
reports another site's name, and a site with no config file is told to look at
`/etc/holdenweb/app.toml`. The framework carries its first site's identity.

*What shipped is the second of those, and it is the better one.* The paths are
`/var/lib/podpack/apps`, `/var/log/podpack/apps` and `/etc/podpack/app.toml` —
the framework's own name, identical in every deployment, which is what they
always were in substance. Templating them per site would have made every
deployment's container layout different for no gain.

Not a data migration: the mount destination and `PODPACK_DATA_ROOT` change
together in one file and the host side of each mount is untouched, so a site
takes it through `substrate upgrade` and the next `up.sh` and finds its content
where it left it. That "together" is the risk, and there is now a test that
parses both halves out of `compose.yaml` and compares them.

*Left alone.* ADRs 0004 and 0018 cite `/etc/holdenweb/app.toml` in passing. They
record decisions as they were made and the path was incidental to both.

*Less pressing than it was.* Item 20 used to depend on this one — its guard
rebuilt `/var/lib/${project%%-*}/apps` and so was inert wherever the site name
did not begin `holdenweb`. That guard now asks compose and podman instead and
names no container-internal path at all, so nothing waits on this any more. What
is left is the cosmetic complaint above: a new site's `/_status` reporting
another site's name.


### 19. `restore.sh` replaces `.env`, so a restore onto a different host fails its own check

**Repo:** podpack — inferred 2026-08-23 by reading, confirmed and made worse by
rehearsal 2 on 2026-08-24. **Fixed 2026-08-25 in `2835606`.**

*What the rehearsal added.* It is not only the port. `.env` carries `SITE_NAME`,
which is the compose project name, so a restore into a checkout called
`holdenweb-staging` produced containers and a network called `holdenweb-com` —
the production project — and every later command in that directory acted on it.
Had production been running, `podman compose up -d --force-recreate web` would
have recreated *it* from staging's directory. `backup.sh` then wrote staging's
backup into `~/backups/holdenweb-com/` for the same reason.

*Evidence.* `scripts/restore.sh` keeps the existing `.env` as
`.superseded-<stamp>` and then installs the backup's over it. Its own comment
says the opposite is wanted — ".env is per-host, so a restore onto a *different*
host wants the existing one kept and edited instead" — but the code does not do
that. The closing health check then polls `${WEB_HOST_PORT}` from the restored
file, which is the old host's, and the script exits non-zero.

*Why it matters.* The data is restored correctly and the script reports failure,
which is the safe direction, but it means the documented recovery path ends in a
red exit on exactly the occasion it exists for — moving to a new host. Anyone
following it under pressure has to know the failure is cosmetic, which is a poor
thing to have to know.

*Fix, and it is wider than the port.* `operations.md` §0 already draws the line
this violates: `secrets.env` is the site's identity and must come back verbatim;
`.env` is "the opposite — ports, paths, **the site name**, SELinux flags … meant
to be edited, and differs legitimately between hosts". `restore.sh` restores
both as though both were the site's, and its own comment says otherwise.

So: keep an existing `.env` rather than replacing it, and where there is none —
a fresh clone — write the backup's but name every value in it that belongs to
the *old* host and wants checking: `WEB_HOST_PORT`, `WEB_BIND_ADDR`,
`VOLUME_RW`/`VOLUME_RO`, and `SITE_NAME`. That fixes the port, the bind address
and the SELinux flags in the same motion, all of which
[`rebuild.sh`](../rebuild.sh) currently repairs by hand afterwards.

A deliberate rename wants to stay deliberate. `BACKUP_ROOT` defaults to
`~/backups/${SITE_NAME}`, so changing the name silently moves where backups land
and orphans the history — `verify-backup.sh` with no argument would then find
nothing. An explicit `--site-name` is the right shape for that, not a value
inherited from whichever `.env` happened to win.

*What shipped.* An existing `.env` is kept untouched and the backup's is put
beside it as `.env.from-backup`, with the per-host keys that differ printed. A
checkout with none still takes the backup's — a site without one cannot start —
but every value describing the old machine is named on the way past. The closing
health check now polls this host's port, so a move to a new host no longer ends
in a red exit the operator had to know was cosmetic.

*Still open.* The explicit `--site-name` above. `BACKUP_ROOT` still defaults to
`~/backups/${SITE_NAME}`, so a site name changed by hand still moves where
backups land; keeping `.env` means that can now only happen deliberately, which
is most of the harm gone but not the sharp edge.

Documented meanwhile at [`rebuild.md`](../rebuild.md) Part 3 and `operations.md` §6.


### 20. `backup.sh`'s cross-deployment guard is inert on most sites

**Repo:** podpack — found 2026-08-23 by reading the script after rehearsal 1.
**Fixed 2026-08-25 in `442e65e`.**

*Evidence.* The guard inspects the running container's mounts to prove it
belongs to this directory, and builds the mount path it looks for from the site
name: `/var/lib/${project%%-*}/apps`. The substrate's `compose.yaml` hardcodes
`/var/lib/holdenweb/apps` for **every** site (item 18). So the path matches only
where the site name's first dash-separated segment is literally `holdenweb`:

| `SITE_NAME` | looks for | |
| --- | --- | --- |
| `holdenweb-com` | `/var/lib/holdenweb/apps` | matches — guard active |
| `holdenweb.com` | `/var/lib/holdenweb.com/apps` | no match — guard skipped |
| `mysite` | `/var/lib/mysite/apps` | no match — guard skipped |
| `podpack-demo` | `/var/lib/podpack/apps` | no match — guard skipped |

When it finds nothing, `mounted_from` is empty and the `[[ -n "$mounted_from"
&& ... ]]` test is simply false. No refusal, no warning.

*Why it matters.* Its own comment says pp-testing's copy caught a real
cross-deployment mixup the first time it ran, and describes the failure it
prevents: "a backup that dumps one deployment's database beside another's app
data looks complete, restores without error, and produces a site whose schema
does not match its content." During rehearsal 1 the guard was **inert in the
clone**, which used `SITE_NAME=holdenweb.com` — the one deployment where two
checkouts were live at once is the one where it was not watching.

*What shipped*, and it needed neither of those. The check is now made
source-side: compose says which container is this project's `web` — resolving
its own project name, so the dotted-name lookup stops mattering — and podman
says what that container mounts, compared against this directory's own data
root by python on both sides. No site name and no container-internal path
appears, so fixing item 18 later cannot break it.

It also fails closed now. pp-testing's original had no `-n "$mounted_from"`
clause; the substrate port added one along with a `2>/dev/null || true`, and an
unanswerable question is a refusal again.

*Measured while fixing it.* Of `holdenweb-com`, `holdenweb.com` and `mysite`,
only the first names a container podman can find at all — so on the other two
the guard was not merely mismatching a path, it was inspecting nothing.

### 21. `manifest.txt`'s `running build` can never be populated

**Repo:** podpack — **fixed 2026-08-26 in `185b0f9`.**

*Evidence.* `backup.sh` reads it with an unauthenticated
`curl .../_status`, and `/_status` answers 404 to anyone who is not an
administrator. The `||` fallback therefore always fires, and every manifest ever
written records `UNKNOWN (not readable when this was taken; /_status wants an
admin)`.

*Why it matters.* The manifest lists it under "The three facts that must agree
on restore", and its purpose is real: framework source is baked into the image,
so a checkout that moved on without a rebuild leaves the site serving an earlier
commit, and `git commit:` alone would then name the wrong thing to restore onto.
`verify-backup.sh` does not print the field, which reads like quiet
acknowledgement.

*What shipped* is exactly that, reusing the container id `backup.sh` already
resolves by asking compose — so it survives a normalised project name too.
Measured side by side against the running site: the new expression returned
`edfff24`, the old one its UNKNOWN fallback.

*Overstated, and worth correcting.* `restore.sh:80-89` already compares the
manifest's `git commit:` with the checkout and resolves the *direction* with
`git merge-base --is-ancestor`, so a code-versus-data check did exist. The hole
this field now covers is the case where the image's commit is not an ancestor of
the recorded HEAD — a `-dirty` build, or a checkout that moved on without one.
That case was live while this was being fixed: the running image was stamped
`0047d6b-dirty` against a HEAD of `edfff24`.


### 22. A failed restore leaves a plausible backup that verifies clean

**Repo:** podpack — observed 2026-08-24, rehearsal 2. **Fixed 2026-08-25 in
`2835606`.**

*Evidence.* After the restore aborted (item 23) the site was brought up anyway,
so podpack seeded `pages` from what the package ships. `backup.sh` then archived
that, and — because `SITE_NAME` had come from the restored `.env` (item 19) — it
wrote into **production's** backup directory:

| | good backup | the one the failed rehearsal left |
| --- | --- | --- |
| `app-data.tar.gz` | 1036570 bytes | 1036573 bytes |
| rowcounts | 5 rows across 4 tables | 4 rows across 4 tables |
| `verify-backup.sh` | VERIFIED | VERIFIED |

*Why it matters.* Nothing available distinguishes them. The size is within three
bytes because most of `pages` is shipped and seeded; the row counts differ by
one user. And `verify-backup.sh` with no argument takes `ls | sort | tail -1`,
so the newest — this one — is what anybody reaching for "the latest backup"
gets. A restore from it would produce a site that starts, serves, and has
quietly lost everything a visitor ever wrote.

*Fix.* `manifest.txt` already records `alembic revision` and `installed apps`;
it could also record whether the data was seeded or restored, or simply the
per-app row counts against the previous backup. A weaker but immediate measure:
`verify-backup.sh` could compare against the previous backup in the same
directory and say when a count has gone down.

*What shipped* is that weaker measure, and one thing the entry missed.
`verify-backup.sh` now compares row counts with the previous backup in the same
root and names any table whose count has fallen or which has gone entirely — a
remark, not a failure, because rows are deleted legitimately and a check that
cries wolf is one people learn to skip. And the closing summary now prints
`from host:` and `source directory:`, which were in every manifest already and
which the regex simply left out: on the two archives above that one field reads
`/tmp/restore-rehearsal` against the real deployment's path. The fact was
written down all along and never shown.

*Still open.* `manifest.txt` recording whether the data was seeded or restored,
which is the strong form and would not depend on there being a previous backup
to compare with.

### 23. `restore.sh` could not work on Linux

**Repo:** podpack — **fixed 2026-08-24** in `b5f4577`, recorded because the
shape of it is worth keeping.

*Evidence.* `restore.sh` ran `prepare-host-dirs.sh`, which on Linux hands the
app data directories to the containers' uids with `podman unshare chown`, then
untarred into those directories as the invoking user. Every `mkdir` failed with
`Permission denied`.

*Why it survived.* The chown is gated on `uname -s`, so on macOS the directories
stay owned by the developer and the untar works. Every test the script ever had
ran where the bug cannot appear. It failed the first time it was asked to do the
job it exists for — and `operations.md` §5 had recommended a monthly restore
into a scratch deployment all along, which on the host would have found it.


### 25. `security/base.html` is a fork of `base.html`, not a child

**Repo:** holdenweb-com — separated from 13, which is fixed. **Fixed 2026-08-25
in `97a3d7a`.**

*Evidence.* `templates/security/base.html` repeats `base.html` almost entirely
rather than extending it. It has already drifted: it loads Bootstrap **4.1.3**
from stackpath where the rest of the site loads **4.6.1** from cdnjs, and it
omits popper. So the login, register and password-reset pages render against a
different framework version from every other page on the site.

*Why it matters.* Anything done to one base misses the other unless somebody
remembers. Fixing the navigation needed the same edit in both files, and the
only reason that was safe is that the edit was a one-line `include`; the next
change to the site's chrome will not be.

**What shipped.** It needed no block overrides at all: every
block flask-security's templates use — `content` in 23 of them, `head_scripts`
in the webauthn four, plus `title`, `navbar`, `styles`, `scripts` and the
document skeleton — is already defined in `base.html`. The whole file is now a
comment and one `extends`.

*One thing the entry missed.* The copy carried a maxcdn integrity hash of
`sha384-h0AbiXch…` against Bootstrap 4.1.3, and `base.saved.html` beside it
carried the *same* hash against 4.0.0-beta. Two different files cannot share a
SHA-384, so the version was bumped and the hash left behind — and a browser
honouring SRI refused to run Bootstrap's JavaScript on these pages entirely.
The auth pages were not merely a version behind; their JavaScript was dead.

All four pages were rendered from the running site and looked at, with the
reset token generated in process so no mail was sent.

*Also.* `templates/security/base.saved.html` is deleted. It was the same file
one Bootstrap version further back, referenced by nothing, and it is in git if
it is ever wanted.

*Still open, and pre-existing.* flask-security's form markup carries no
Bootstrap classes, so the inputs and buttons on these pages are unstyled. That
was equally true of the copy.


### 26. Every `up` builds the same image twice

**Repo:** podpack — **fixed 2026-08-26 in `185b0f9`.** — observed 2026-08-24 in a full rebuild transcript.

*Evidence.* `compose.yaml` gives `web` and `migrate` the same
`image: localhost/${SITE_NAME}-web:latest` and **both declare `build:`**. So one
`compose up --build` builds it twice. A rebuild does it four times in all, since
`restore.sh` runs its own `up -d --build` before `up.sh` runs another.

*Why it matters.* Little, on a warm cache — four cached builds cost about twelve
seconds. It matters for what it does to the output: roughly four hundred lines
of `Using cache` between the restore's verification block and the site coming up,
which is where a reader is looking for whether anything went wrong. On a cold
cache, or a host that has just been rebuilt from nothing, it is a genuine
doubling.

*What shipped* is that, and the check was done rather than assumed. The image
was removed outright and `up.sh` run against nothing: one build pass instead of
two, 19s, `holdenweb-com-migrate-1` Created / Started / Exited against the image
`web`'s build had just produced, `/healthz` 200 with `database: ok`, and 15
integration tests passing.

*The measurement.* One cached build pass is 8.3s of the 91s an `up` took warm.
The duplication was two passes per `up` and four per rebuild, since `restore.sh`
runs its own `up -d --build` first.

*What it relies on.* A build being asked for at all. `up.sh` and `restore.sh`
both pass `--build`; a bare `podman compose up` on a host with no image would
try to *pull* the tag and fail — which it would equally have done for `web`
before, so nothing new is exposed.


---

## Raised 2026-08-26, while adding the navigation

### 27. Navigation is one level deep, so an app's pages hang off the root

**Repo:** podpack

*Evidence.* `nav.Section` is a frozen dataclass of exactly two fields, `label`
and `endpoint`. The registry keeps `state.nav` as a flat `list[Section]`
(`registry.py:289`) and extends it with each app's entries as it installs
(`registry.py:425`). `templates/nav.html` renders one `<ul>` of one `<li>` per
entry. There is nowhere for a child to go at any of the three levels.

*Why it matters.* An app with more than one page has no way to group them, so
every function it offers must either claim a top-level slot or be reachable only
from the app's own landing page. `pp_pdf` is the case in hand: its individual
tools link from the root page because the chrome cannot nest them. The nav is
the site's map, and an app that does several things cannot say so on it.

Not urgent — the site works, and the workaround costs a click.

*Fix, and the requirement that shapes it.* `Section` gains children, the
registry keeps whatever tree the apps declare, and the chrome renders it. Two
kinds of graceful degradation are wanted, and the first matters more:

  **At the API.** A `Section` carrying children must still render correctly in
  chrome that knows nothing about them — as its own top-level link. Otherwise
  every site's `nav.html`, and every custom chrome anyone has written, breaks on
  the release that adds this. `nav.html` is a site file, so podpack cannot fix
  them by upgrading.

  **In the browser.** A nested menu that needs JavaScript or hover to reach a
  child is a menu that fails on a phone and for anyone using a keyboard. Plain
  nested `<ul>`s remain usable as a list when nothing else runs.

`_check_nav` (`registry.py:503`) refuses to boot when an entry names an endpoint
no view provides, and must keep doing so for children — that check is why a bad
nav entry is a startup failure rather than `BuildError` on every page of the
site.

ADR-0022 decided nav is contributed by apps and addressed by endpoint, and
nothing here disturbs that; this is the same idea one level further down. Worth
checking whether it wants an ADR of its own or an amendment to that one.

### 28. A link between pages is rewritten to the asset route, losing the site

**Repo:** podpack-pages — found 2026-08-26 while publishing a generated tree of
class notes.

**Fixed** in podpack-pages 0.3.4, published 2026-09-22 and taken here the same
day: the floor in `pyproject.toml` is now `>=0.3.4`. It reaches the deployment on
the next rebuild.
`rewrite_asset_urls` became `rewrite_relative_urls` and takes a `page_url`
beside `asset_url`. A relative value ending `.html` or `.htm` now goes to the
page route with the suffix *dropped* rather than trusted, because the page space
is extensionless and `find_page` appends `.md` before `.html` -- so a link
written to `guide.html` lands on `guide.md` when that is what the tree holds. A
`#fragment` or `?query` is split off before the decision and restored after it,
without which `notes.html#intro` would not be recognised as a page link at all.
`..` is deliberately not normalised: a link that climbs out of a tree is refused
by `check_relative` when it is requested, which is where that judgement belongs.

The rule is a suffix test and nothing more, on Steve's call (2026-09-22): an
HTML document inside a content tree is a page, never an asset. Where it guesses
wrong it is wrong for one link, which is how the behaviour it replaces was wrong
for every one of them.

*Measured before it was written, and worth recording.* No content on this site
changes today. pybooks and notebooks carry no relative HTML links at all --
orpy's own navigation is absolute, which is why it was left alone -- the blog
does not use this rewrite, and `pages` holds two links that climb five levels
outside the tree to content that is not there and stays broken either way. So
this lowers the error rate for the generated trees still to come rather than
repairing anything now, and the evidence is three tests that fail when the rule
is disabled and pass when it is restored.

*Evidence.* `content.rewrite_asset_urls` sends **every** relative `src` or
`href` through `url_for("pages.asset", ...)`. It cannot distinguish a link to a
page from a link to an image, because nothing tells it which is which. Measured
against the shipped function, for a page served at `/pages/python-classes/index`:

| in the HTML | becomes |
| --- | --- |
| `python2/index.html` | `/pages/asset/python-classes/python2/index.html` |
| `style.css` | `/pages/asset/python-classes/style.css` |
| `/pages/python2/index` | unchanged — `/` is in `_ABSOLUTE_PREFIXES` |

The second row is right. The first is not, and the difference is visible:

| | status | site chrome |
| --- | --- | --- |
| `/pages/bsars` | 200 | present |
| `/pages/asset/bsars.html` | 200 | **absent** |

*Why it matters.* A tree of linked HTML — which is what a generator produces —
cannot be published as a set of pages. Follow a relative link and the target
renders as a raw file: no navigation, no chrome, no way back. Follow a
root-relative one and it 404s. The only form that reaches another *rendered*
page is an absolute path naming the page route in full,
`/pages/python-classes/python2/index`, which means the content has to know where
the site mounted the app — the thing ADR-0022 went to trouble to avoid for nav.

*Fix, and the question in it.* A reference to something inside the content trees
that is *itself a page* — `.html` or `.md` — should be rewritten to the page
route with the extension dropped; everything else to the asset route as now.
That is a small change with one real question behind it: whether a `.html` file
in a content tree is ever legitimately an asset rather than a page. If it is,
the split needs saying rather than inferring — a marker directory, a
declaration, or a convention.

Worth doing with 29, since a tree of pages that link to each other also wants
its directories to be landable.

### 29. A directory has no index, so it cannot be landed on

**Repo:** podpack-pages

**Fixed** in podpack-pages 0.3.x and live here since the 0.3.3 pin; confirmed
2026-09-18. `views.py` resolves a directory's slash form to its `index` page
(`name += "index"`, line 105) and 308-redirects the bare form to it when
`is_page_dir` says the directory exists (lines 109-110). So
`/pages/python-classes/` lands, and the bare form redirects there rather than
404ing -- which is also what keeps a relative reference inside an index page
resolving within its own directory.

*Evidence.* `content.find_page` tries exactly two candidates and stops:
`md-pages/<name>.md`, then `html-pages/<name>.html`. So
`/pages/python-classes` raises `ContentNotFound` even when
`html-pages/python-classes/` holds a hundred files, and the root of a published
tree can only be reached by naming its index page explicitly —
`/pages/python-classes/index`.

*Why it matters.* Every generated site has a front door and this one cannot be
opened. It also makes a link to a directory — the ordinary way to write "up" or
"contents" — unresolvable.

*Fix.* Two more candidates after the existing two: `<name>/index.md` and
`<name>/index.html`. Worth settling whether the index name is fixed or
configurable, and whether `/pages/x` and `/pages/x/` should both resolve —
Flask's `<path:name>` captures them differently and only one of them is what a
relative link in the served page will be resolved against.

Pairs with 27: a navigation that can nest wants directories that can be landed
on.

---

## Raised 2026-09-03, chasing the backup-cron failure

### 30. No shared decorator for operator-only routes

**Repo:** podpack

**Fixed** in podpack `9740282`, released as **0.9.3** and taken here the same
day: `/config` carries `@operator_required` and its copy of the guard is gone,
so the duplication this item was about no longer exists in either place.

`@operator_required` refuses a route to anyone the site's own admin predicate
does not admit, and refuses with a 404. flask-security's `roles_required` does
neither thing: it 403s, which confirms the route exists and that this is a
podpack site at all, and it asks about `admin` membership directly, walking
straight past a predicate the site replaced under ADR-0033. `is_operator()`
moved to `auth.py` beside `is_admin`, and podpack's own `/_status` now carries
the decorator rather than an inline guard.

*What it removed here:* nine lines in `src/holdenweb/views.py` that read
`extensions["podpack"].admin`, wrapped the call in `try`/`except` and fell
through to `abort(404)` -- the same guard podpack had, written out a second
time, which is what made this an item rather than a tidy-up.

The behaviour is unchanged and pinned: `test_config_is_not_public` fails if the
decorator is taken off, and an anonymous `GET /config` on a running site answers
404 with the site's own error page. The redaction below it is untouched and
stays the second line of defence -- the guard defends the config's shape, the
redaction defends its secrets.

### 31. `configure-host.py` should pin the compose provider, not just warn

**Repo:** podpack

*Evidence.* `podman compose` is a shim that picks an external provider from
`containers.conf`'s `[engine] compose_providers`; with no such file on the host
(none is shipped or written), podman's built-in default list applies --
docker-compose first, `podman-compose` last -- and **PATH is the only tiebreak**.
An interactive login shell has `~/bin` first and gets `~/bin/docker-compose`
(Compose v2); any stripped or non-login environment cannot resolve
`docker-compose` and falls through to `/usr/bin/podman-compose` -- the Python
tool that rejects `ps --status running --services` and, per gotcha 4 and
ADR-0016, silently ignores `depends_on` ordering gates. None of the substrate
scripts set PATH or a provider (`up.sh:32`, `restore.sh`, `backup.sh`,
`verify-backup.sh` all call a bare `podman compose`), so the provider is decided
entirely by each caller's environment. `configure-host.py:86-96` already runs
`podman compose version` and detects a non-"Docker Compose" provider -- but only
appends a warning string, and only ever sees the interactive environment, so a
green `configure-host.py` says nothing about cron or an ssh deploy.

*Why it matters.* Two unattended paths hit the fallback. The nightly backup cron
did -- now fixed in `holdenweb.com/ops/backup.cron` by prepending `$HOME/bin`,
and by a manual `~/.config/containers/containers.conf` pin on opal17
(2026-09-03). The one still unhardened in-repo is the routine deploy:
`holdenweb.com/ops/deploy.sh:82` runs `ssh host "cd ~/… && ./scripts/up.sh"`, a
non-login shell whose PATH need not include `~/bin` -- and `up.sh:32` runs
`podman compose up -d --build`, which is exactly where the ordering gates live.
If it resolves `podman-compose`, every deploy silently skips init-storage →
postgres-healthy → migrate → web. That is the "failure mode is silence" ADR-0016
flags as unaddressed, on the routine path.

*Fix.* Turn `configure-host.py`'s detection into prevention: write (or merge)
`[engine] compose_providers = ["<abs path to docker-compose>"]` -- a single
absolute path found via `shutil.which("docker-compose")` (default
`~/bin/docker-compose`), with **no** `podman-compose` entry so a missing provider
fails loudly rather than degrading -- into the rootless user's
`~/.config/containers/containers.conf` (merging, or a `.d` drop-in; verify
user-level drop-in support on the host). Not the rendered site tree -- podman
never reads it. Add `compose_warning_logs = false` there too, to silence the
`>>>> Executing external compose provider …` banner. And correct
`configure-host.py:95`'s advice, which names a `PODMAN_COMPOSE_PROVIDER`
environment variable that does not appear to exist -- the real override is
`containers.conf`; confirm on the host before rewriting. Being substrate-shipped,
this makes every deployment safe by construction; keep the byte-identical
repo-root and packaged copies in step.

*Interim, in place now.* `ops/backup.cron` prepends `$HOME/bin` (belt-and-braces)
and opal17 carries the manual `containers.conf` pin, so this host is covered;
item 31 is the durable, every-deployment form. The pin also closes deploy.sh
without touching it, because it is PATH-independent.

### 32. `PODPACK_PROXY_HOPS` should be derived from the environment, not set by hand

**Repo:** podpack

*Evidence.* `PODPACK_PROXY_HOPS` is carried as a standalone value every
deployment must set and keep correct, and it is the one variable podpack cannot
deliver: its documentation lives in `env.example`, a seeded file
`podpack substrate upgrade` never rewrites (SUB-1). The result is manual handling
wherever it matters -- `rebuild.sh` reconciles it by hand (step 3, default 1),
`rebuild.md` Part 4 echoes `PODPACK_PROXY_HOPS=1` into `.env` by hand, and a
fresh site that misses it serves every `_external` URL as `http://`, first
visible in a password-reset mail. That `http://` reset link is the fault this
whole framework exercise began with.

*Why it matters.* The value is not really free -- it is a function of how the
site is deployed. A site reached directly in development sits behind no proxy
(0 hops); a site behind Opalstack's nginx sits behind exactly one (1 hop). And
podpack already knows which it is: Phase-0 item 7 put `PODPACK_ENVIRONMENT` in
`.env` per deployment (`local` vs not-local, unrecognised counting as
not-local). So the hop count is derivable, and a derived value cannot be
forgotten, cannot go undelivered, and cannot drift from the deployment it
describes.

*Fix.* Derive the trusted-hops count from `PODPACK_ENVIRONMENT`: **0 for
`local`, 1 for `staging` or `production`.** Read it where the app configures its
ProxyFix (or equivalent), so `PODPACK_PROXY_HOPS` becomes a computed default
rather than a hand-set variable -- keep an explicit override for the unusual
topology (two proxies, say), but make the common case automatic. Retire the
manual `PODPACK_PROXY_HOPS` handling in `rebuild.sh` and `rebuild.md` once it is
derived, which also removes most of SUB-1's motivation (the undeliverable
commented var). Fits ADR-0037, which already has `configure-host.py` own the
variable set and names the deployment type explicitly.

### 33. The `web` healthcheck pings every 10s -- too often for a quiet site

**Repo:** podpack

*Evidence.* `compose.yaml:160` sets the `web` service healthcheck to
`interval: 10s` (`test: python /app/healthcheck.py`, timeout 5s, retries 6,
start_period 10s), so a site with no users yet health-pings `/healthz` six times
a minute around the clock -- overhead and access-log noise (see LOG-1) out of
all proportion to the traffic. The postgres healthcheck at 5s
(`compose.postgres.yaml:78`) is the startup gate and a separate matter; leave it.

*Fix.* Widen the `web` healthcheck `interval` to **150s** for now, and tighten it
again when the site is busy enough to want fast liveness detection. `compose.yaml`
is byte-identical substrate (podpack canonical + the rendered `holdenweb.com`
copy + the root), so change them together. Nothing currently acts on `web` being
unhealthy -- podman does not auto-restart on it -- so the only cost is how
quickly `podman ps` reflects a wedged container; consider trimming `retries`
too, since 6 x 150s is a 15-minute window to "unhealthy". Fuller form, and it
fits item 32: make the interval a function of `PODPACK_ENVIRONMENT` -- loose for
a quiet or dev site, tight for production -- rather than one hardcoded default.

### 34. `/config` dumps every secret in the Flask config, even to an admin

**Repo:** holdenweb-com

**Fixed 2026-09-03** in `src/holdenweb/views.py`: a shape-only `_redacted()`
covering `SECRET`/`PASSWORD`/`SALT`/`TOKEN`/`KEY` names and the database URI,
reported as `<redacted, N chars>`, with a `test_config_redacts_secret_values`
guard. Keys still show, values do not.

*Evidence.* `src/holdenweb/views.py:71-75` (`get_version`) returns
`{"config": {k: str(v) for (k, v) in current_app.config.items()}}` -- the entire
Flask config unredacted, which includes `SECRET_KEY`, `SECURITY_PASSWORD_SALT`,
`MAIL_PASSWORD` and `SQLALCHEMY_DATABASE_URI` (the database password is in it).
SEC-1 closed the route to non-admins (it now 404s), but the *content* is still
every secret the site holds, handed to any admin session in clear.

*Why it matters.* Defence in depth. The route's guard is the only thing between
these values and the world, and it has regressed once already -- that was SEC-1.
A redacted body means a future guard slip cannot leak the secrets, and an admin
reading `/config` in a browser is not shoulder-surfing them or dropping them into
a screenshot or a support log. It is the principle the codebase applies
everywhere else: report a secret's shape, never its value.

*Fix.* Redact the sensitive keys before serialising -- match on name
(`*SECRET*`, `*PASSWORD*`, `*SALT*`, `*TOKEN*`, `*KEY*`, and
`SQLALCHEMY_DATABASE_URI`) and replace the value with a placeholder or its
length/shape rather than the string. Simplest is a denylist yielding
`<redacted>`; better is the shape indicator the secret tests already use.
podpack's `/_status` is the reference for how much a diagnostic endpoint should
say -- `/config` should not say more.

### 35. Does the `os` stack auto-start after an Opalstack host reboot?

**Repo:** holdenweb-com. Opalstack reboots the shared host for their own
maintenance, on their schedule and not ours -- and whether `os` comes back
without a human depends on `loginctl enable-linger` (so the user's containers run
with no login session) plus `restart: unless-stopped` in `compose.yaml`. Neither
has been seen through an actual host reboot; a rebooted laptop proves nothing,
since the site runs on opal17. If it ever failed, the site would sit down until
someone noticed -- precisely the silence **MON-1** (the external `/healthz` poll)
exists to break. So this pairs with MON-1: confirm the stack returns unattended
after the next host reboot (`podman ps` clean with no manual `up.sh`), keep
linger enabled, and have MON-1 live so a failure to return is caught rather than
stumbled on.

## Raised 2026-09-07

### 36. `refresh-content.sh --mirror` deletes live content with no confirmation

**Repo:** holdenweb-com. This is holdenweb's own `ops/` script, not podpack
substrate -- `refresh-content.sh` lives only at `holdenweb.com/ops/`, so the fix
is one repo.

**Fixed** in `ops/refresh-content.sh`; confirmed 2026-09-18. `--mirror` now asks
before it removes anything and proceeds only on a typed `mirror`, which is the
dangerous half of this item closed.

*The gate did not land with it, though*, and that had a live consequence rather
than being cosmetic. Filed and fixed as 38.

*Evidence.* `ops/refresh-content.sh` takes an optional `--mirror`, and in mirror
mode `podman unshare rsync --delete` removes any file the staged source no longer
has -- straight into the live `hostdata/apps/<APP>/<TREE>` tree a visitor is
served from. The script does it the instant it is told to, with no prompt. Its
new caller `ops/push-content.sh` (a449624) *does* guard `--mirror` with a
tty-gated "type `mirror` to proceed", so a push from the laptop is safe; but a
human ssh'd into opal17 running `refresh-content.sh <dir> --mirror` by hand --
exactly what the local-dev instructions in `README.md` tell you to do -- gets no
such question.

*Why it matters.* The destructive path is one flag from the safe one, and the
mistake it invites is real: a partial or wrong source with `--mirror` silently
deletes whatever it lacks. `scripts/restore.sh` already treats its own
destructive step this way, and `push-content.sh` now does too; the script that
actually does the deleting is the one still missing the guard.

*Fix.* Give `refresh-content.sh` the same confirmation `push-content.sh` and
`restore.sh` use -- when `--mirror` is set *and* stdin is a tty, print what will
be deleted and require the operator to type `mirror` before proceeding; a piped
or non-interactive run (the push-content case, which has already confirmed
upstream) passes straight through. Guarding the script itself, not just its
caller, is what makes the by-hand host run safe.

## Raised 2026-09-10

### 37. Published notebooks depend on their source staying put

**Repo:** podpack-notebooks. `notebooks.yaml` names each notebook by a path to
its `.ipynb` source, and since `build.py` now expands `~` and absolute paths,
that source commonly lives in a working directory elsewhere on the laptop, not
in the repo. So a published notebook is only as durable as that source file:
rename, move or delete it during ordinary development and the next `build.py`
run drops or changes the published page, quietly.

*Why it's left.* The obvious fix is to *vendor* a copy of each published
notebook into the podpack-notebooks repo, so publication is pinned to a
committed artefact rather than a live working file. That is deliberately
deferred: it brings name-collision handling (two sources with the same stem),
a decision about when a vendored copy is refreshed from its source, and the
curation questions that follow — more machinery than the current need warrants.
Steve's call (2026-09-10): keep it simple for now, convert straight from the
sources `notebooks.yaml` points at.

*The trigger to watch for* is a published notebook going stale or vanishing
because its source moved — at which point vendoring (and its collision rules)
earns its keep.

---

## holdenweb's substrate scripts still carry the CDPATH-doubling bug

The six substrate scripts under `scripts/` — `up.sh`, `dev.sh`, `backup.sh`,
`restore.sh`, `verify-backup.sh`, `prepare-host-dirs.sh` — derive their own root
with `here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"`, which doubles
`$here` (and then fails on `cd "$here"`) when `CDPATH` is exported *and* the
script is invoked relatively. `CDPATH` is exported in this laptop's `~/.zshrc`,
so `up.sh` and `dev.sh` — run relatively from the repo root — fail here today;
the host-run backup/restore/verify/prepare scripts are exposed only on a
relative invocation with `CDPATH` set (cron uses an absolute path, so the
scheduled backup is safe). holdenweb's own `ops/refresh-content.sh` is not a
substrate file and was fixed directly (commit 9ad969e), which is what surfaced
this — `just notebooks local` died on the doubled path.

These six are managed podpack substrate files (five `verbatim`, `dev.sh`
`rendered`), so the fix belongs upstream and is there: **podpack commit 7e50f9d**
adds `unset CDPATH` to all six (both the `data/` template and its rendered root
copy). holdenweb installs podpack from PyPI and carries synced copies, so it
receives the fix only when it moves to a podpack release that includes 7e50f9d
and re-syncs the substrate.

*Why it's left.* Patching holdenweb's copies directly would create substrate
drift — `substrate status --check` exists precisely to catch a managed file that
no longer matches podpack — and the next sync would reconcile it away. The
durable path is the upstream fix (done) plus a normal substrate upgrade, not a
per-file patch here.

*The trigger to watch for* is the next podpack bump in `pyproject.toml`: once
holdenweb is on a podpack release carrying 7e50f9d
(`uv lock --upgrade-package podpack` after it is published), run the substrate
upgrade so the six copies refresh to the fixed versions — which also clears the
pre-existing `substrate.json` staleness. Until then, don't run `up.sh`/`dev.sh`
relatively on a shell with `CDPATH` set, or invoke them by absolute path.

---

## Raised 2026-09-18, auditing the open items against the source

### 38. `refresh-content.sh`'s mirror prompt was not tty-gated

**Repo:** holdenweb-com — found 2026-09-18 auditing 36's fix.

**Fixed 2026-09-22** in `ops/refresh-content.sh`: the prompt is now inside
`if [ -t 0 ]`, and the removal is deliberately left outside it.

*Evidence.* 36 asked for "the same tty-gated typed-`mirror` prompt `restore.sh`
and `push-content.sh` use". The prompt landed; the gate did not.
`ops/push-content.sh:80` reads `if [ "$mirror" -eq 1 ] && [ -t 0 ]; then`, while
`refresh-content.sh` carried a bare `read -r -p` and contained no `-t 0` at all.
Measured: with stdin closed, `read` returns 1 and an empty reply, so the script
took its `|| { echo "aborted"; exit 1; }` branch.

*Why it mattered.* `ops/push-content.sh:102` drives the remote half as
`ssh "$sshhost" "cd ~/$path && … ./ops/refresh-content.sh $scratch $mirror_arg"`,
with no pty. So a `--mirror` confirmed locally reached the host and aborted
there, and from cron it aborted outright. Before 36 there was no prompt and that
path simply worked, so the fix had moved the failure rather than removing it.

*The trap in the obvious fix.* Adding `&& [ -t 0 ]` to the outer `if` would skip
`rm -rf "${target:?}"` as well, silently turning a mirror into a merge: the
source's files land, the ones it no longer has stay, and the result is a tree
that never existed anywhere -- the exact state `restore.sh`'s header warns about,
wearing the appearance of success. So the prompt is gated and the removal is not.

*What shipped, and how it was checked.* Against a throwaway `ztest/ztree`: with
stdin closed, `--mirror` ran unprompted, exited 0, and removed a `stale.txt` the
source did not carry; a merge in the same conditions left its stale file in
place; and the pre-fix `read` was confirmed to return 1 on EOF. The ssh path
itself is reasoned from the two scripts rather than run, since confirming it
means mirroring against a real host.

## Filing these

Nothing here has been filed: creating issues is a change to a shared, public
record, and that is the account holder's call rather than a side effect of
writing a document. When the time comes, each section above is already a title
and a body:

```bash
gh issue create --repo holdenweb/holdenweb-com \
  --title "MAIL_PASSWORD is still the example value in production" \
  --body-file - <<'EOF'
...paste the section...
EOF
```

Delete an item from this file once its issue exists, so that this list is
always what is *not* yet tracked.
