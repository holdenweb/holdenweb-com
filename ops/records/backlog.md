# Backlog: findings awaiting an issue

> **Record · append-only, for whoever is deciding what to fix next.** Never
> followed and never rewritten except to strike an item with its evidence. The
> **Repo** column is the destination: podpack's items become podpack issues, and
> extracting them is a filter on that column rather than a reading of the whole
> list.

*Raised 2026-08-19, while writing [`operations.md`](../../operations.md). Held
here for triage into GitHub Issues — both `holdenweb/holdenweb-com` and
`holdenweb/podpack` have Issues enabled and are currently empty, so nothing has
been filed yet.*

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
| 8 | holdenweb-com | Nothing polls `/healthz` | gap |
| 9 | holdenweb-com | No log rotation | gap |
| 10 | holdenweb-com | No maintenance page | gap |
| 11 | holdenweb-com | Migrations have no tested downgrade | gap |
| 14 | podpack | `backup.sh`'s working-tree guard fails open — **fixed** | security |
| 15 | podpack | `/_status` `stored_files` cannot see a directory | correctness |
| 16 | podpack | Recreating the database leaves a site that can never migrate — **fixed** | operational |
| 18 | podpack | Container paths name holdenweb for every site | cosmetic |
| 19 | podpack | `restore.sh` replaces `.env`, so a restore gives the checkout the backup's `SITE_NAME` — **fixed** | operational |
| 20 | podpack | `backup.sh`'s cross-deployment guard is inert on most sites — **fixed** | security |
| 21 | podpack | `manifest.txt`'s `running build` can never be populated | correctness |
| 22 | podpack | A failed restore leaves a plausible backup that verifies clean — **fixed** | operational |
| 23 | podpack | `restore.sh` could not work on Linux — **fixed** | operational |
| 25 | holdenweb-com | `security/base.html` is a fork of `base.html`, not a child — **fixed** | correctness |
| 26 | podpack | Every `up` builds the same image twice | efficiency |

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

### 9. No log rotation

**Repo:** holdenweb-com. `hostlogs/` grows without limit; the laptop lab's
PostgreSQL log reached 19 MB against 62 MB of data. Nothing prunes it.

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

**Repo:** podpack

*Evidence.* `src/podpack/core.py:295` — `iterdir()` filtered to `p.is_file()`.
Production reports `"stored_files": []` for `pages`, which holds 1.0 MB in
subdirectories.

*Why it matters.* `core.py` says the field sits beside `backs_up` because "an app
claiming to store nothing while listing files is the contradiction podpack warns
about at boot". The boot check itself (`registry.py`, `_check_backup_claim`) has
no such filter and is correct — so `/_status` shows a weaker view than the check
uses. An app declared stateless on that evidence would drop its content from
every backup, silently, until somebody tried to restore.

*Fix.* Count directories too, or rename the field for what it actually reports.

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

**Repo:** podpack

*Evidence.* `substrate/data/compose.yaml:119-120` hardcodes
`/var/lib/holdenweb/apps` and `/var/log/holdenweb/apps`, and
`src/podpack/__init__.py:59-60` defaults to the same. Verified by building a
site called `mysite` from `creating-a-site.md`: it gets holdenweb's paths.

*Why it matters.* Harmless inside a container, but a new site's `/_status`
reports another site's name, and a site with no config file is told to look at
`/etc/holdenweb/app.toml`. The framework carries its first site's identity.

*Fix.* Template the path from the site package, or make it site-neutral.

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

**Repo:** podpack

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

*Fix.* Ask the container instead — `podman inspect` can read
`PODPACK_BUILD_COMMIT` from the running image without any session at all.


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

**Repo:** podpack — observed 2026-08-24 in a full rebuild transcript.

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

*Fix.* `migrate` names the image it needs and does not need to build it —
`depends_on` already orders it after the build that `web` triggers. Removing its
`build:` block should be enough, and wants checking on a host with no image
present at all, since that is the case the duplication was presumably guarding.


---

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
