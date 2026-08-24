# Backlog: findings awaiting an issue

*Raised 2026-08-19, while writing [`operations.md`](../operations.md). Held
here for triage into GitHub Issues — both `holdenweb/holdenweb-com` and
`holdenweb/podpack` have Issues enabled and are currently empty, so nothing has
been filed yet.*

Each item names the repository it belongs to, the evidence that it is real, and
what fixing it involves. **Tier 1** was found while writing the playbook;
**Tier 2** is the standing known-gaps register from
[`operations.md` §17](../operations.md), recorded here so the two lists do not
drift apart.

| # | Repo | Item | Kind |
| --- | --- | --- | --- |
| 5 | holdenweb-com | `PROJECT-BRIEF.md` names the profile `dbport`; it is `postgres-port` | docs |
| 6 | holdenweb-com | `README.md` stale on dependency sources | docs |
| 7 | holdenweb-com | `environment = "local"` in the production config | cosmetic |
| 8 | holdenweb-com | Nothing polls `/healthz` | gap |
| 9 | holdenweb-com | No log rotation | gap |
| 10 | holdenweb-com | No maintenance page | gap |
| 11 | holdenweb-com | Migrations have no tested downgrade | gap |
| 13 | holdenweb-com | Only the front page renders the site navigation | correctness |
| 14 | podpack | `backup.sh`'s working-tree guard fails open | **security** |
| 15 | podpack | `/_status` `stored_files` cannot see a directory | correctness |
| 16 | podpack | Recreating the database discards `db-init`'s grants | fragility |
| 18 | podpack | Container paths name holdenweb for every site | cosmetic |
| 19 | podpack | `restore.sh` replaces `.env`, so a restore gives the checkout the backup's `SITE_NAME` | **operational** |
| 20 | podpack | `backup.sh`'s cross-deployment guard is inert on most sites | **security** |
| 21 | podpack | `manifest.txt`'s `running build` can never be populated | correctness |
| 22 | podpack | A failed restore leaves a plausible backup that verifies clean | **operational** |
| 23 | podpack | `restore.sh` could not work on Linux — **fixed** | operational |

*Numbers are stable identifiers, so a gap means an item was struck rather than
renumbered.*

**Struck:** **1** — `MAIL_PASSWORD` was already correct in production;
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

*Evidence.* `PROJECT-BRIEF.md:96` gives
`podman compose --profile dbport up -d dbport`. `compose.postgres.yaml` defines
the service as `postgres-port` with `profiles: ["postgres-port"]`. The brief
predates the rename.

*Why it matters.* The command as written does nothing and says nothing useful,
in a document whose purpose is briefing somebody who does not already know.

*Fix.* One-line correction, both occurrences on that line.

### 6. `README.md` is stale on dependency sources

**Repo:** holdenweb-com

*Evidence.* `README.md:64` — "building currently requires the three
path-sourced dependencies (podpack, podpack-pages, podpack-qrcode, pp-pdf) to be
repointed at git remotes and re-locked". They are already git-sourced
(`pyproject.toml:34-38`), and there are four of them, not three.

*Why it matters.* It describes a blocker that no longer exists, and miscounts
what it lists — so a reader either does unnecessary work or stops trusting the
document.

*Fix.* Delete the note. It becomes wrong again shortly, when the git sources
are retired in favour of PyPI version specs.

### 7. `environment = "local"` in the production configuration

**Repo:** holdenweb-com

*Evidence.* `config/app.toml:6`. The file is bind-mounted read-only from git,
so production reads the same value the laptop does. podpack reads `environment`
and does nothing with it.

*Why it matters.* Nothing is broken. But `/_status` on the production host says
the site thinks it is local, and the next person to read it will spend time
establishing that this is harmless.

*Fix.* Either make the value meaningful (per-host, which means it stops being a
committed file's business) or remove it. Removing it is the smaller lie.

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
[`operations.md` §15](../operations.md) says — it is also the reason the backup
before a schema change is the one that matters most.

---

## Raised since — 2026-08-21

### 13. Only the front page renders the site navigation

**Repo:** holdenweb-com

*Evidence.* `sections` — the navigation podpack assembles from the installed
apps and puts in front of every template — is referenced in exactly one of this
site's templates, `src/holdenweb/templates/index.html:14`. In both
`templates/base.html:60` and `templates/security/base.html:59` the
`{% block navbar %}` is present and **empty**. podpack's own fallback
`base.html:32` does render it.

*Why it matters.* A site that writes no `base.html` gets the navigation; this
site wrote one and silently lost it. So every page other than `/` — the two
`pp_pdf` forms, everything under `/pages`, all the flask-security pages, and
404 — offers no route to the other installed apps. The logo links to `/` and
the bluebar handles login, so nothing is a dead end, but installing an app
currently adds it to one page's menu rather than to the site's.

*Fix.* Render `sections` in the `navbar` block, with podpack's
`src/podpack/templates/base.html:32` as the reference for markup and endpoint
handling.

Two things fall out of the same edit, and are the reason it is not a one-line
change:

- **`security/base.html` is a drifted copy-paste fork of `base.html`,** not a
  child of it. It carries Bootstrap 4.1.3 from stackpath where the site
  otherwise loads 4.6.1 from cdnjs, and no popper — so the login, register and
  password-reset pages already render against a different framework version
  than the rest of the site. Editing one base will not reach them.
- **`templates/security/base.saved.html` is a leftover** beside it, and wants
  deleting or explaining.


---

## Raised 2026-08-23, by the first rebuild rehearsal

*None of these were findable by reading. Each came from running the procedure on
a real host; the run is kept at [`rehearsal-2026-08-23.md`](rehearsal-2026-08-23.md).*

### 14. `backup.sh`'s working-tree guard fails open

**Repo:** podpack — **the one to fix first.**

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

*Fix.* Create the parent before testing it, or resolve the path without
requiring it to exist.

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

### 16. Recreating the database discards `db-init`'s grants permanently

**Repo:** podpack

*Evidence.* `db-init/01-create-app-user.sh` runs only while the postgres data
directory is still empty. The restore procedure recreates the database, which
destroys the `SCHEMA app AUTHORIZATION <app role>` and the `CONNECT` grant it
made, and it will not run again.

*Why it matters.* It works today because the dump restores its own ownership and
PostgreSQL grants `CONNECT` to `PUBLIC` on a new database. Both are load-bearing
accidents that nothing records.

*Fix.* Documented for now at [`rebuild.md`](rebuild.md) 4.2. A real fix re-applies
the grants after a restore, or restores into the existing schema instead.

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


### 19. `restore.sh` replaces `.env`, so a restore onto a different host fails its own check

**Repo:** podpack — inferred 2026-08-23 by reading, **confirmed and made worse
by rehearsal 2 on 2026-08-24.**

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

*Fix.* Either keep the per-host values out of what is restored, or take
`--port`, or re-read `.env` for `WEB_HOST_PORT` before the health check.
Documented meanwhile at [`rebuild.md`](rebuild.md) Part 3 and `operations.md` §6.


### 20. `backup.sh`'s cross-deployment guard is inert on most sites

**Repo:** podpack — found 2026-08-23 by reading the script after rehearsal 1.

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

*Fix.* Derive the mount path from the same place `compose.yaml` gets it, or read
it from the container rather than reconstructing it. Fixing item 18 first would
make this straightforward.

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

**Repo:** podpack — observed 2026-08-24, rehearsal 2.

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
