# The 3am Almanac — a podpack message knowledge base

> **Generated from [`messages.json`](messages.json) by [`build-messages.py`](build-messages.py). Edit the JSON, not this file.**

Every message this system is likely to put in front of you — 119 of them — with where it comes from, how serious it is, and what to do. At 3am: search this file for the fixed part of the message you're staring at (`<angle-brackets>` mark the variable bits). The browsable, filterable version is [`messages.html`](messages.html).

**Severity** — 🔴 critical (42) an outage, or data/secrets at risk · 🟠 needs action (36) a step failed or a decision is needed · 🟡 warning (21) worth a look · 🔵 info (20) normal, listed so you can confirm it's benign.

**Where** — *laptop* (your machine, dev & deploy) · *host* (the Opalstack deploy host) · *either*.


## Your laptop

### 🔴 poll-bad-body
`<time>: health check FAILED for <url> -- 200 but body lacks "status":"ok" (the proxy answered; the app or database did not)`

- **Critical** · **where:** laptop · **from:** `ops/poll-health.sh`
- **Means:** nginx answered 200 (likely its own error page) but the app's health JSON is absent: web is down/unhealthy behind a working proxy, or the database is down.
- **Do:** Check web + postgres on the host; hit /healthz directly for the reason. Cross-ref healthz-503.

### 🔴 poll-no-200
`<time>: health check FAILED for <url> -- no 200 (DNS, TLS, the proxy, or the container is down)`

- **Critical** · **where:** laptop · **from:** `ops/poll-health.sh`
- **Means:** The site did not return 200 from outside: DNS, TLS, the nginx proxy, or the web container is down. The site is unreachable.
- **Do:** Check the host: `ssh <host> 'cd ~/apps/<app>/site && podman compose ps'`; check DNS/proxy; then ./ops/deploy.sh or restart web.

### 🟠 deploy-bad-remote-url
`remote '<target>' is not an scp-style host:path URL: <url>`

- **Needs action** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** The remote exists but is not host:path form, so deploy can't derive the rebuild command.
- **Do:** Re-point it: `git remote set-url <target> opal17:apps/<app>/site`.

### 🟠 deploy-dirty
`uncommitted changes to tracked files; commit first, or pass --allow-dirty.`

- **Needs action** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** Tracked files have uncommitted changes; only commits are pushed, so they would not deploy. Untracked files (a stray README.pdf) do not count.
- **Do:** Commit them, or pass --allow-dirty to deploy anyway (up.sh then stamps -dirty).

### 🟠 deploy-no-remote
`no git remote named '<target>'. Add it (see ops/DEPLOY.md): git remote add <target> opal17:apps/<app>/site`

- **Needs action** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** The target's git remote is not configured on this laptop.
- **Do:** Add it per ops/DEPLOY.md: `git remote add <target> opal17:apps/<app>/site`.

### 🟠 deploy-usage
`usage: deploy.sh [--dry-run] [--allow-dirty] <staging|production>`

- **Needs action** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** No target (or an unknown flag) was given.
- **Do:** Re-run with `staging` or `production`.

### 🟠 dev-cannot-reach-db
`cannot reach the local database named in dev.env. If PostgreSQL is running, it probably has no role or database for this site yet: createuser --pwprompt <user> / createdb --owner <user> <name>`

- **Needs action** · **where:** laptop · **from:** `scripts/dev.sh`
- **Means:** podpack will not create the local database itself (the server is yours). The exact commands to create the role and DB are printed. Exit 2.
- **Do:** Run the printed `createuser --pwprompt <user>` and `createdb --owner <user> <name>`, then re-run dev.sh.

### 🟠 pull-rsync-error
`rsync: change_dir "..." failed: No such file or directory / rsync error: ...`

- **Needs action** · **where:** laptop · **from:** `ops/pull-backups.sh`
- **Means:** The pull failed. Commonly the source ~/backups/<SITE_NAME>/ does not exist yet (no backup has run on the host), or ssh to the host failed.
- **Do:** Confirm backups have run on the host (is backup.cron installed?) and that `ssh <host>` works.

### 🟡 deploy-no-health-url
`==> no health URL configured for <target>; verify it by hand.`

- **Warning** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** The target (e.g. production before its domain exists) has no health URL, so it deployed but did not self-verify.
- **Do:** Check the site by hand; set the target's URL in deploy.sh's health_url().

### 🟡 deploy-not-on-origin
`note: HEAD (<sha>) is not on origin/main -- deploying unpublished code.`

- **Warning** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** You are deploying a commit that is not on GitHub. Fine for staging; worth noticing for production.
- **Do:** `git push origin main` to publish, or proceed if this is deliberate.

### 🟡 dev-created-env
`created dev.env from dev.env.example -- review it before going further`

- **Warning** · **where:** laptop · **from:** `scripts/dev.sh`
- **Means:** A missing dev.env was seeded from the example.
- **Do:** Edit dev.env (notably SQLALCHEMY_DATABASE_URI and ports) before continuing.

### 🟡 dev-mongo-note
`note: this site declares mongodb, which a local run does not start. Install one natively and add MONGODB_URI to dev.env, or expect the apps that use it to report themselves unhealthy.`

- **Warning** · **where:** laptop · **from:** `scripts/dev.sh`
- **Means:** .env declares mongodb, but a native dev.sh run does not start it; apps needing Mongo will be unhealthy.
- **Do:** Install MongoDB natively and add MONGODB_URI to dev.env, or accept those apps being unhealthy in local dev.

### 🔵 deploy-progress
`==> deploying <sha> to <target> (<host>:<path>) / ==> verifying <url> / ==> <target> is healthy at <sha>`

- **Info** · **where:** laptop · **from:** `ops/deploy.sh`
- **Means:** Normal progress. The last line is success: pushed, rebuilt, and /healthz returned ok.
- **Do:** Nothing.

### 🔵 dev-server-banner
`development server -- one process, no gunicorn, no proxy, debug reloader on. the containerised stack is ./scripts/up.sh, and is what production resembles.`

- **Info** · **where:** laptop · **from:** `scripts/dev.sh`
- **Means:** About to exec flask run --debug: the single-process dev server, not production shape.
- **Do:** Nothing. Use ./scripts/up.sh when you need production-like behaviour.

### 🔵 pull-success
`<time>: pulled <host>:<src> -> <dest>`

- **Info** · **where:** laptop · **from:** `ops/pull-backups.sh`
- **Means:** The off-machine backup copy synced successfully.
- **Do:** Nothing.


## Host scripts

### 🔴 backup-dump-empty
`the <service> dump is empty -- refusing to keep a backup that cannot restore`

- **Critical** · **where:** host · **from:** `backup.sh`
- **Means:** A store's dump produced a zero-byte file. A backup that can't restore is worse than none, so the whole destination is deleted.
- **Do:** Check that store's health and credentials (`podman compose logs <service>`); confirm the dump command works. Re-run once it dumps non-empty.

### 🔴 backup-refuse-inside-site
`refusing to write a backup inside the site directory: ... it would contain secrets.env in clear. Set BACKUP_ROOT.`

- **Critical** · **where:** host · **from:** `backup.sh`
- **Means:** The destination resolves to inside the checkout. A backup holds every secret verbatim; a directory of credentials inside the repo is one careless `git add` from being published. Nothing was written.
- **Do:** Set BACKUP_ROOT outside the working tree, e.g. ~/backups/<site>.

### 🔴 backup-refuse-mount-mismatch
`REFUSING: the running web container does not mount this directory's app data. ... Another deployment is using this compose project name.`

- **Critical** · **where:** host · **from:** `backup.sh`
- **Means:** Two checkouts share the same compose project name, so compose's `web` belongs to a different deployment. Backing up now would dump one deployment's DB beside another's app data.
- **Do:** Stop the other deployment or give this one a distinct SITE_NAME. The printed lists show expected vs actual mount; reconcile before backing up.

### 🔴 backup-refuse-no-web-container
`REFUSING: compose will not say which container is this project's web, so nothing here can prove the containers belong to this directory.`

- **Critical** · **where:** host · **from:** `backup.sh`
- **Means:** `podman compose ps -q web` returned nothing, so the script cannot prove the running containers belong to this checkout. Fails closed on purpose.
- **Do:** Check the stack is this deployment's (`podman compose ps`), that SITE_NAME/project name is right, and that compose is v2. Bring up the correct stack, then re-run.

### 🔴 backup-store-missing-dump
`a store named in the plan produced no dump: <file>`

- **Critical** · **where:** host · **from:** `backup.sh`
- **Means:** A store named in the plan produced no dump file at all (the cross-check that counts plan stores against written files). Destination deleted.
- **Do:** Re-run; if it recurs, inspect the store. Treat any surviving backup taken before this fix as suspect.

### 🔴 cfg-refuse-overwrite
`refusing to overwrite: <files> ... These carry a live site's identity -- the salt every stored password is keyed on, and the role the database was created with. Regenerating them does not reconfigure the site, it loses it. Use --force only on a site with no data yet.`

- **Critical** · **where:** host · **from:** `configure-host.py`
- **Means:** .env/secrets.env already exist. Overwriting would regenerate SECURITY_PASSWORD_SALT (every stored password becomes unverifiable) and the DB role/name -- i.e. lose the site. Nothing was changed.
- **Do:** Do NOT --force on a site with data. To inspect, use --check. Only --force on a site with no data yet.

### 🔴 prepare-not-a-lab
`PODPACK_ENVIRONMENT=<env>, so this is not a lab, and ... resolves to <path>, which is inside the checkout ... Point it somewhere the checkout does not own ... Set PODPACK_ENVIRONMENT to 'local' if this really is a lab.`

- **Critical** · **where:** host · **from:** `prepare-host-dirs.sh`
- **Means:** On a non-lab deployment, HOST_DATA_DIR/HOST_LOG_DIR resolve inside the git checkout -- where a `git clean -fdx`, fresh clone, or rebuild would wipe live data. Anything but `local` (typos included) triggers it. Exit 1.
- **Do:** Point data/log dirs outside the checkout (../data, ../logs beside site/). Only set PODPACK_ENVIRONMENT=local if this is genuinely a throwaway lab.

### 🔴 restore-count-mismatch
`<schema>.<table>   MISMATCH: expected <a>, found <b>`

- **Critical** · **where:** host · **from:** `restore.sh`
- **Means:** A table's live row count does not match the backup: the data is not fully restored (an empty dump restores cleanly and looks perfect -- this is what catches it). Restore exits non-zero.
- **Do:** Do not treat the site as restored. Investigate the store restore (logs, dump integrity); re-restore from a verified backup.

### 🔴 restore-counts-not-matched
`row counts do not match the backup -- the data is NOT fully restored`

- **Critical** · **where:** host · **from:** `restore.sh`
- **Means:** Final gate: at least one table mismatched. The site may be up but the data is incomplete.
- **Do:** Do not go live on it. Re-restore from a verified backup; investigate why the dump was short.

### 🔴 restore-not-healthy
`the site is not healthy -- see 'podman compose logs web'`

- **Critical** · **where:** host · **from:** `restore.sh`
- **Means:** /healthz never returned 200 -- the restored site is effectively down. Common causes: migrate failed, DB auth (URI vs role drift), bad .env.
- **Do:** `podman compose logs web` (and migrate). Fix and re-run.

### 🔴 verify-app-data-empty
`FAILED: <n> app(s) keep data, and the archive holds nothing`

- **Critical** · **where:** host · **from:** `verify-backup.sh`
- **Means:** The plan says apps keep data, but the app-data archive is empty -- data that should exist wasn't captured.
- **Do:** Distrust the backup; investigate the backup run's app-data step. Re-take.

### 🔴 verify-dump-corrupt
`FAILED: <service>'s dump could not be read right through / the archive is truncated or corrupt: <file>`

- **Critical** · **where:** host · **from:** `verify-backup.sh`
- **Means:** The store's own tool could not read the dump end to end -- truncated or corrupt. Exactly the failure verify exists to catch early.
- **Do:** This backup cannot restore that store. Take and verify a fresh backup now; keep the last known-good one.

### 🔴 verify-no-table-data
`FAILED: the database dump contains no table data at all`

- **Critical** · **where:** host · **from:** `verify-backup.sh`
- **Means:** The Postgres dump is a valid archive holding zero TABLE DATA -- what a dump of the wrong or empty database looks like. The silent-empty-backup disaster.
- **Do:** Do not trust it. Confirm the site actually had data; check the backup (right container? right DB?). Re-take.

### 🟠 backup-no-env
`no .env -- nothing to back up; this is not a deployed site`

- **Needs action** · **where:** host · **from:** `backup.sh`
- **Means:** There is no .env in the tree, so this is not a deployed site.
- **Do:** You are probably in the wrong directory. cd to the real deployment (~/apps/<app>/site).

### 🟠 backup-plan-no-store
`the plan names no backing store, so this would archive no data at all / (are the PODPACK_SERVICE_* markers set? see compose.yaml)`

- **Needs action** · **where:** host · **from:** `backup.sh`
- **Means:** The plan lists zero backing stores, so the backup would contain no data. Usually the PODPACK_SERVICE_* env markers are unset. The half-made destination is removed.
- **Do:** Set the PODPACK_SERVICE_* markers in compose.yaml / overlays, then re-run.

### 🟠 backup-web-not-running
`the web service is not running, so nothing can say what to back up / bring the site up, or restore from an existing backup instead`

- **Needs action** · **where:** host · **from:** `backup.sh`
- **Means:** The web container is not running, so `podpack backup plan` can't be asked what to archive.
- **Do:** ./scripts/up.sh to bring the stack up, then re-run; or restore from an existing backup.

### 🟠 cfg-linger-off
`lingering is off, so the containers and the podman socket stop when you log out. loginctl enable-linger <uid>`

- **Needs action** · **where:** host · **from:** `configure-host.py`
- **Means:** Without linger, rootless containers and the podman socket die at logout (Opalstack needs this).
- **Do:** `loginctl enable-linger <uid>`.

### 🟠 cfg-not-v2
`the compose provider is not Compose v2 -- podman-compose silently ignores depends_on conditions, which is what sequences migrate before web. Install the v2 binary and set PODMAN_COMPOSE_PROVIDER.`

- **Needs action** · **where:** host · **from:** `configure-host.py`
- **Means:** The wrong compose provider is active. podman-compose ignores the depends_on gates that order init-storage -> postgres -> migrate -> web -- every ordering guarantee breaks.
- **Do:** Install the Compose v2 binary and set PODMAN_COMPOSE_PROVIDER. Never run the stack under podman-compose.

### 🟠 cfg-socket-missing
`<sock> is missing -- Compose v2 talks to podman through it. systemctl --user enable --now podman.socket`

- **Needs action** · **where:** host · **from:** `configure-host.py`
- **Means:** The rootless podman API socket isn't running; Compose v2 needs it.
- **Do:** `systemctl --user enable --now podman.socket`.

### 🟠 restore-incomplete-backup
`backup is incomplete: <backup>/<file> is missing or empty`

- **Needs action** · **where:** host · **from:** `restore.sh`
- **Means:** A required member (manifest.txt, plan.json, app-data.tar.gz, env, secrets.env) is missing or empty; this backup can't be restored.
- **Do:** Use a different, complete backup; run verify-backup.sh on candidates first.

### 🟠 restore-prompt
`This will REPLACE the data and secrets above. Type 'restore' to go on:`

- **Needs action** · **where:** host · **from:** `restore.sh`
- **Means:** Interactive confirmation gate (skipped only with --yes). Anything other than the literal word `restore` aborts.
- **Do:** Type `restore` to proceed; anything else aborts safely.

### 🟠 restore-store-unhealthy
`<service> did not become healthy; see 'podman compose logs <service>'`

- **Needs action** · **where:** host · **from:** `restore.sh`
- **Means:** A store never reached healthy within ~120s; restore stops. App data and .env/secrets.env are in place but no data has been loaded.
- **Do:** `podman compose logs <service>` for why (mount ownership, PGDATA mode, healthcheck args). Fix and re-run.

### 🟠 verify-required-missing
`FAILED: <file> is missing or empty`

- **Needs action** · **where:** host · **from:** `verify-backup.sh`
- **Means:** A required backup member is absent or zero-length -- the backup is structurally incomplete.
- **Do:** Distrust this backup. Take a fresh one; if this was the latest, investigate the backup run.

### 🟠 verify-store-not-running
`FAILED: <service> is not running, so its dump cannot be read / bring the stack up; verification needs the store's own tooling`

- **Needs action** · **where:** host · **from:** `verify-backup.sh`
- **Means:** Verification reads each dump with the store's own tool inside its container; that store isn't up. A limitation of the check, not necessarily a bad backup.
- **Do:** ./scripts/up.sh, then re-run verification.

### 🟡 cfg-still-example-credential
`still the example's value, and needs changing: <VAR> (<file>)`

- **Warning** · **where:** either · **from:** `configure-host.py`
- **Means:** A credential-shaped variable still equals the example -- a lab value that won't authenticate, and for a live site a published credential. Often a site's own key the script doesn't generate (e.g. MAIL_PASSWORD).
- **Do:** Edit those variables in .env/secrets.env to real values before the site serves.

### 🟡 manifest-alembic-unknown
`alembic revision: UNKNOWN`

- **Warning** · **where:** host · **from:** `backup.sh (manifest.txt)`
- **Means:** The schema revision this data belongs to is unrecorded -- the one fact a restore most needs. Postgres was likely unhealthy at backup time.
- **Do:** Prefer a fresh backup where the revision is recorded; a backup with UNKNOWN here is harder to restore safely.

### 🟡 manifest-running-build-unknown
`running build: UNKNOWN (the web container did not report a build stamp)`

- **Warning** · **where:** host · **from:** `backup.sh (manifest.txt)`
- **Means:** The running web container carried no build stamp, so the manifest can't say which code produced the data.
- **Do:** Rebuild with ./scripts/up.sh (it stamps the commit) so future backups can name the serving build. The data is still valid.

### 🟡 prepare-created-env
`created <.env|secrets.env> from <file>.example -- review it before going further`

- **Warning** · **where:** host · **from:** `prepare-host-dirs.sh`
- **Means:** A missing .env or secrets.env was seeded from its example. Example secrets.env holds LAB credentials; a fresh secrets.env is only right for a site with no data yet.
- **Do:** For a real deployment, run configure-host.py (which generates real secrets) rather than shipping example values. Review the file first.

### 🟡 restore-cleanup-notice
`this restore set these aside for you to read: ... delete them once you are satisfied -- secrets.env.superseded-* is a copy of every secret this site has, and none of these is ignored`

- **Warning** · **where:** host · **from:** `restore.sh`
- **Means:** .superseded-* and .env.from-backup were left in the tree. On older sites they are NOT gitignored, and one is a clear copy of every secret -- a `git add` from publication.
- **Do:** Read them if useful, then delete them. Confirm they aren't staged or committed.

### 🟡 restore-env-key-differs
`<KEY>: keeping <mine>, backup had <theirs>`

- **Warning** · **where:** host · **from:** `restore.sh`
- **Means:** A per-host key (SITE_NAME, WEB_HOST_PORT, HOST_DATA_DIR ...) differs between this host and the backup; this host's value is kept. Every one of these has been wrong on a real restore at least once.
- **Do:** Confirm keeping this host's value is right (usually yes on the same host; check carefully on a replacement).

### 🟡 restore-installed-backup-env
`no .env here, so the backup's was installed. These describe the host it came from, and want checking before this site answers anywhere else:`

- **Warning** · **where:** host · **from:** `restore.sh`
- **Means:** A fresh clone had no .env, so the backup's was installed wholesale -- and it describes the OLD host (ports, paths, bind address, SITE_NAME).
- **Do:** Edit .env for this host before exposing the site: especially WEB_BIND_ADDR, WEB_HOST_PORT, HOST_DATA_DIR, SITE_NAME.

### 🟡 restore-warn-commit-mismatch
`WARNING: this checkout is not the commit the backup was taken from. (The checkout is NEWER ... this is fine. OR ... OLDER or unrelated ... Prefer: git checkout <commit>)`

- **Warning** · **where:** host · **from:** `restore.sh`
- **Means:** Code and data are from different commits. NEWER is fine (alembic rolls forward). OLDER/unrelated is the concern: the backup's schema may describe tables this code doesn't know. Deliberately a warning, not an auto-checkout.
- **Do:** If NEWER, proceed. If OLDER/unrelated, `git checkout <backup-commit>` first unless you intend to roll forward.

### 🟡 verify-all-empty
`NOTE: every table is empty. Right for a site that has no data yet; alarming for one that had some yesterday. Only you know which.`

- **Warning** · **where:** host · **from:** `verify-backup.sh`
- **Means:** Every recorded table has zero rows. Legitimate for a brand-new site; a red flag for an established one. Not a failure.
- **Do:** If this site had data yesterday, treat as a possible bad backup and investigate; otherwise fine.

### 🟡 verify-fewer-rows
`NOTE: this backup holds less than <previous> did. ... Deletions look exactly like this. So does a backup of a site that was seeded rather than restored.`

- **Warning** · **where:** host · **from:** `verify-backup.sh`
- **Means:** Fewer rows (or tables) than the previous backup. Could be legitimate deletions -- or the signature of a site that was seeded (aborted restore then brought up) whose backup silently becomes the latest.
- **Do:** Establish which before this becomes the copy you reach for. If you didn't delete that data, prefer an earlier verified backup and investigate.

### 🔵 backup-complete
`backup complete: <dest>`

- **Info** · **where:** host · **from:** `backup.sh`
- **Means:** Success. The whole backup is owner-only (chmod -R go-rwx).
- **Do:** Nothing. Optionally verify it now with verify-backup.sh.

### 🔵 cfg-wrote
`wrote .env and secrets.env (0600) for '<site>' (then port / database / SELinux / secrets generated; none printed)`

- **Info** · **where:** host · **from:** `configure-host.py`
- **Means:** Success -- fresh config written 0600. Secrets were generated with a URL-safe alphabet and never printed.
- **Do:** Nothing. `SELinux detected -- mounts will be relabelled` means :Z/,z flags were set (getting that wrong yields a healthy-looking Postgres whose db-init never ran).

### 🔵 manifest-app-skipped-stateless
`<app> declared SKIPPED, declared stateless`

- **Info** · **where:** host · **from:** `backup.sh (manifest.txt)`
- **Means:** That app said it stores nothing, so no data was archived for it -- expected, not an omission.
- **Do:** Nothing, unless an app you know holds data shows SKIPPED -- then its site_app data declaration is wrong.

### 🔵 restore-complete
`restore complete, and checked.`

- **Info** · **where:** host · **from:** `restore.sh`
- **Means:** Success -- health 200 and every row count matched.
- **Do:** Nothing. Then handle the cleanup notice if shown.

### 🔵 up-building-from
`building from <sha>  (or <sha>-dirty, or unknown)`

- **Info** · **where:** host · **from:** `up.sh`
- **Means:** Rebuilding and stamping this commit into the image. `-dirty` = built from an uncommitted tree (normal while working); `unknown` = a repo with no commits (a brand-new site's first build).
- **Do:** Nothing normally. On production, -dirty or unknown means the running image has no clean commit behind it -- commit and re-run for a reproducible build.

### 🔵 verify-verified
`VERIFIED: <backup> (then taken / from host / source directory / git commit / alembic revision / services)`

- **Info** · **where:** host · **from:** `verify-backup.sh`
- **Means:** Success -- every leg read clean. A scheduled run exits 0.
- **Do:** Nothing. This is the pass line.


## The app — boot & runtime

### 🔴 cfg-cannot-start-secrets
`this site cannot start: not set: <names>; still holding a placeholder: <names> -- the file was installed and never edited. Secrets come from the environment, which compose fills from secrets.env; a local run gets them from dev.env via scripts/dev.sh.`

- **Critical** · **where:** either · **from:** `config.py`
- **Means:** One or more required secrets are empty/unset, or still a placeholder (CHANGEME, an unresolved @@TOKEN@@). Reports ALL offenders at once, each annotated with who needs it. Crashes web (and migrate for the DB URI) at boot.
- **Do:** Fill the named vars in secrets.env (container) or dev.env (local). Empty (SECRET_KEY=) counts as missing. Never commit values.

### 🔴 cfg-config-not-mounted
`host configuration not mounted at <path> -- check the ./config bind mount in compose.yaml`

- **Critical** · **where:** either · **from:** `config.py`
- **Means:** The TOML host config (default /etc/podpack/app.toml) isn't a file at that path -- usually a wrong or missing ./config bind mount. web crash-loops.
- **Do:** Fix the ./config/app.toml:/etc/podpack/app.toml:ro mount in compose.yaml; confirm the file exists.

### 🔴 cfg-require-env
`required environment variable <NAME> is not set`

- **Critical** · **where:** either · **from:** `config.py`
- **Means:** A single required env var (SECRET_KEY, SQLALCHEMY_DATABASE_URI, SECURITY_PASSWORD_SALT) was absent -- the one-name-at-a-time backstop behind the richer check above.
- **Do:** Set the named variable in secrets.env (container) or dev.env (local).

### 🔴 healthz-db-down
`{"database":"<sqlalchemy error>","status":"unhealthy"}  -- HTTP 503`

- **Critical** · **where:** either · **from:** `core.py`
- **Means:** SELECT 1 against the database raised; the site is up but has no working DB. The container healthcheck sees 503 -> the whole stack is marked unhealthy.
- **Do:** Check PostgreSQL (postgres service health, SQLALCHEMY_DATABASE_URI, the grant/search_path). The error text is SQLAlchemy's own.

### 🔴 mig-missing-schema
`This connection's search_path is '<sp>', and no schema in it exists. Every CREATE TABLE below would fail ... To repair it, connect as the superuser and run: CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION <the application role>; ... Restoring with scripts/restore.sh instead avoids this entirely.`

- **Critical** · **where:** host · **from:** `alembic/env.py`
- **Means:** The role's search_path names a schema (app) that no longer exists -- the classic aftermath of dropdb/createdb by hand: db-init runs only while the data dir is empty, so a recreated DB comes back with only public. Runs in migrate -> web never starts.
- **Do:** Run the printed CREATE SCHEMA ... AUTHORIZATION <app role> as superuser (role = POSTGRES_APP_USER in secrets.env) -- or restore via scripts/restore.sh, which brings each store up alone so its bootstrap runs first.

### 🔴 mig-no-database-uri
`SQLALCHEMY_DATABASE_URI is not set. Migrations read it from the environment, as the site does -- compose supplies it from secrets.env, and a local run gets it from dev.env via scripts/dev.sh.`

- **Critical** · **where:** either · **from:** `alembic/env.py`
- **Means:** Alembic env found no DB URI. env.py deliberately does NOT load_dotenv() -- a bare `alembic upgrade head` will not silently reach a stray .env (that was a measured near-miss on the live DB). Runs in migrate -> web never starts.
- **Do:** Run migrations through scripts/dev.sh (sources dev.env) or compose (supplies secrets.env); don't rely on a stray .env.

### 🔴 proxy-hops-not-a-number
`PODPACK_PROXY_HOPS is '<raw>', which is not a whole number. It counts the proxies between the internet and this site: 1 where a single nginx forwards to it, unset where nothing does.`

- **Critical** · **where:** either · **from:** `proxy.py`
- **Means:** PODPACK_PROXY_HOPS is set to a non-integer (or negative). Refused rather than defaulted, because a deployment that meant to proxy but serves unproxied reproduces the cleartext reset-link bug this module fixes.
- **Do:** Set PODPACK_PROXY_HOPS to a whole number (1 behind a single nginx), or unset it entirely.

### 🔴 reg-clashing-table
`installing '<module>' failed: it declares the table '<t>' (already needed by <apps> / already on db.metadata). Table names are shared across every installed app ... so prefix __tablename__ with the app's own name.`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** Two installed apps define the same __tablename__. SQLAlchemy's own error names the table but neither app; this names who's involved.
- **Do:** Prefix the offending __tablename__ with the app's own name so table names don't collide.

### 🔴 reg-duplicate-blueprint-name
`two installed apps share the blueprint name '<name>'; it has to be unique because it decides the template namespace, the data and log directories, and the config section`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** Two apps in apps resolve to the same blueprint name; that name is the app's whole identity, so it must be unique.
- **Do:** Rename one app's blueprint, or drop the duplicate from apps.

### 🔴 reg-missing-table-dependency
`this site is missing a table that nothing installed defines: <table>, needed by <apps>. Either add the app that defines it to [site] apps, or stop installing the app that needs it.`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** An installed app declares needs_tables for a table no installed app defines. The site would serve every page and fail on the first query that touches it.
- **Do:** Add the app that defines the table to [site] apps, or remove the app that needs it.

### 🔴 reg-mount-for-uninstalled-app
`[site.mounts] mounts <names>, which no installed app answers to. Installed apps: <installed>. Note the key is the app's name -- that is, its blueprint's name -- which is not always the import name listed in apps.`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** [site.mounts] names an app that isn't installed -- a typo, or an app dropped from apps while its mount stayed.
- **Do:** Fix the [site.mounts] key to the app's blueprint name (not necessarily the import name in apps), or delete the stale mount.

### 🔴 reg-nav-endpoint-missing
`<name> contributes the nav entry '<label>' naming the endpoint '<endpoint>', which no view provides; nav entries name endpoints rather than paths so that they follow the app wherever the site mounts it`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** An app's Section names an endpoint no view provides. Caught at boot because otherwise url_for raises BuildError while rendering the chrome -- on every page.
- **Do:** Fix the endpoint string in the app's nav=(Section(...),) to a real blueprint.view name.

### 🔴 reg-no-site-app
`<module> is listed as an installed app but exposes no module-level `site_app`; see podpack.registry for the contract`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** A name in [site] apps imports fine but has no module-level site_app. Also fires in the migrate container, so it surfaces there rather than one service later in web.
- **Do:** Give the app package a module-level `site_app = SiteApp(...)`, or remove it from apps.

### 🔴 reg-site-app-wrong-type
`<module>.site_app is a <TypeName>, not a SiteApp. A podpack app wraps its blueprint rather than exporting it: site_app = SiteApp(blueprint=..., url_prefix=...)`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** site_app exists but is the wrong type -- classically `site_app = blueprint`, the natural move from plain Flask.
- **Do:** Wrap the blueprint: `site_app = SiteApp(blueprint=..., ...)`.

### 🔴 reg-url-prefix-in-app-config
`[apps.<name>] sets url_prefix, which podpack no longer reads. Mount points belong to the site, so move it to: [site.mounts] <name> = "..."`

- **Critical** · **where:** either · **from:** `registry.py`
- **Means:** The old spelling -- mount point under the app's own [apps.<name>] table. Refused rather than silently ignored.
- **Do:** Move url_prefix out of [apps.<name>] into [site.mounts] <name> = "...".

### 🔴 urls-bad-base-url
`[site] base_url is '<value>', which has no scheme and host. It is the site's canonical public address, so it needs to look like 'https://example.com'.`

- **Critical** · **where:** either · **from:** `urls.py`
- **Means:** [site] base_url is set but scheme-less/host-less, which urljoin would silently mangle. Caught at boot rather than in the first mail that carries a link.
- **Do:** Set base_url to a full https://host form, or remove it (it's optional -- only needed for request-less link building).

### 🟠 healthz-app-unhealthy
`{"apps":{"<app>":{"status":"unhealthy","detail":"...","fatal":true}},"status":"unhealthy"}  -- 503 only when fatal`

- **Needs action** · **where:** either · **from:** `core.py`
- **Means:** An installed app's healthz() returned unhealthy or raised. Operators (admin) see ms/detail/fatal; non-operators see only status. Only fatal=true apps take the site to 503.
- **Do:** Read detail (as operator, or in /_status) to see which app and why. A non-fatal unhealthy app means one feature is degraded, not the site.

### 🟠 hw-mail-send-failed
`could not send the '<template>' email to <recipient>: <ExcType>: <exc>`

- **Needs action** · **where:** either · **from:** `holdenweb mail_util.py`
- **Means:** flask-security tried to send mail (password reset is the one that matters) and the backend raised -- dead/expired SMTP credential, network, TLS. Without this it becomes a 500 with a traceback on the reset form.
- **Do:** Diagnose the mail credential with `flask --app holdenweb mail check`. <template> tells you which mail; <ExcType> the failure family.

### 🟠 hw-mail-visitor-flash
`That email could not be sent just now -- a problem at our end, not with your account. Please try again shortly.`

- **Needs action** · **where:** either · **from:** `holdenweb mail_util.py`
- **Means:** Shown to a visitor whose mail failed, so they don't wait forever after flask-security's cheerful 'instructions have been sent'. It means real mail delivery is down.
- **Do:** Fix SMTP (see hw-mail-send-failed and mail check). Reset mail is only reached for addresses that have an account.

### 🟠 hw-mailcheck-fail
`SMTP auth FAILED: <ExcType>  (then <exc>; exit 1)`

- **Needs action** · **where:** either · **from:** `holdenweb commands.py`
- **Means:** `flask --app holdenweb mail check` -- the mail server rejected the connection/credential. Non-zero exit so a deploy step can gate on it. The definitive mail diagnosis, faster than a reset round-trip.
- **Do:** Read <ExcType>/<exc>; fix credential or account (535 = auth). Password shape is checked too: a Google App Password is 16 lowercase letters, no spaces.

### 🟠 mig-foreign-autogenerate
`refusing to autogenerate against <dialect>: this site deploys on postgresql, and a revision written here can be one PostgreSQL rejects. Point SQLALCHEMY_DATABASE_URI at a PostgreSQL first -- dev.env names your local one. Applying migrations (alembic upgrade head) is not restricted.`

- **Needs action** · **where:** laptop · **from:** `migrations.py`
- **Means:** You ran `alembic revision --autogenerate` against SQLite (or other), which produces revisions PostgreSQL rejects. Refused (not warned) because the bad file outlives the session and gets applied to prod unwatched.
- **Do:** Point SQLALCHEMY_DATABASE_URI at your local PostgreSQL (dev.env names it) before autogenerating. Applying migrations is never blocked.

### 🟡 boot-no-admin-role
`no 'admin' role exists, so /_status will answer 404 to everyone -- including you. Create it and grant it: flask --app <name> roles create admin / roles add <email> admin`

- **Warning** · **where:** either · **from:** `__init__.py`
- **Means:** The site booted, but no admin role exists, so /_status (and holdenweb's /config) 404 for everyone including the operator. Normal on a brand-new site; a lockout if you expected admin access.
- **Do:** Run the two `flask ... roles` commands it prints (and `flask users create` first if you have no user).

### 🟡 paths-file-logging-disabled
`file logging disabled for <module>: <exc>`

- **Warning** · **where:** either · **from:** `paths.py`
- **Means:** Couldn't open <log_root>/<app>/<app>.log (permissions/mount). The app still runs and still logs to stdout; only its own file handler is missing.
- **Do:** Check the log-root bind-mount ownership/writability (cross-ref /_status log_dir_writable).

### 🟡 reg-backup-claim-contradicted
`app '<name>' says it stores nothing, but <data_dir> holds <files>. A backup will skip it on the app's word: either the declaration is wrong, or those files are not wanted.`

- **Warning** · **where:** either · **from:** `registry.py`
- **Means:** An app declared Backup(data=False) but its data directory is not empty. The only SiteApp declaration that warns instead of refusing to boot. Also on /_status.
- **Do:** Fix the app's backs_up declaration, or remove the stray files. Left alone, backups silently skip that directory.

### 🟡 reg-unprefixed-table-warning
`app '<name>' declares the table '<t>', which its own name does not prefix. ... a second app claiming '<t>' will stop a site booting. Name it in the app's needs_tables if it is deliberate.`

- **Warning** · **where:** either · **from:** `registry.py`
- **Means:** An app defines a table whose name isn't prefixed by the app name -- a latent collision that boot-fails whichever site later installs a second app claiming that name.
- **Do:** Prefix the table name, or (if deliberately shared) list it in the app's needs_tables to silence the warning.

### 🔵 boot-admin-check-skipped
`could not check for the 'admin' role: <exc>`

- **Info** · **where:** either · **from:** `__init__.py`
- **Means:** Benign. The auth tables don't exist yet (fresh DB, or a test DB), so the admin-role diagnostic couldn't run. Ordinary on first boot before migrate has run.
- **Do:** Nothing. If tables should exist, check the migrate service ran.

### 🔵 healthz-ok
`{"status":"ok","database":"ok"}  -- HTTP 200`

- **Info** · **where:** either · **from:** `core.py`
- **Means:** Liveness + readiness passed: SELECT 1 succeeded and no fatal app-health failure. The container healthcheck reads only the status code.
- **Do:** Nothing. This is the healthy state.

### 🔵 hw-config-404
`/config -> HTTP 404 (to any non-admin)`

- **Info** · **where:** either · **from:** `holdenweb views.py`
- **Means:** /config serialises the Flask config's keys and shape but REDACTS secret values -- SECRET_KEY, the DB URI, MAIL_PASSWORD and the like come back as `<redacted, N chars>` (commit 5dd5c28); it 404s (not 403) to anyone who isn't admin, like /_status. The guard fails closed, and the body no longer carries secret values.
- **Do:** If an operator gets 404 here, it's the missing-admin-role story again (boot-no-admin-role). If a NON-admin ever gets 200, that's a guard failure to investigate at once -- but the redaction means the body does not by itself leak secret values, so rotate only what a check shows was actually exposed.

### 🔵 status-404-to-non-admin
`/_status -> HTTP 404 (to any non-operator)`

- **Info** · **where:** either · **from:** `core.py`
- **Means:** /_status deliberately answers 404, not 403, to anyone who isn't an operator -- including when the admin role doesn't exist yet, or the guard failed closed. A refusal and a nonexistent route look identical on purpose.
- **Do:** If you are locked out, you likely have no admin role/grant (see boot-no-admin-role). Otherwise this is the intended response.

### 🔵 status-fields
`/_status -> 200 JSON: database, database_user, database_schema, site, config_source, build_commit, data_root, log_root, proxy{}, unclaimed{}, apps{}`

- **Info** · **where:** either · **from:** `core.py`
- **Means:** The operator's ground truth for where state lives. build_commit answers 'is the container running this commit?' (a -dirty suffix = built from an uncommitted tree). apps.<n>.data_dir_writable=false is a mount-ownership problem.
- **Do:** Read it when a mount, grant, config edit, or 'which commit is live?' is in question. Operator only.

### 🔵 status-unclaimed-nonempty
`/_status unclaimed.data / unclaimed.logs / unclaimed.tables non-empty`

- **Info** · **where:** either · **from:** `core.py`
- **Means:** Files, dirs, or tables that no currently-installed app answers for -- normally the residue of an app REMOVED from apps (its data is kept, never auto-deleted). Not an error.
- **Do:** Confirm it's expected leftover state. Reported, never tidied -- deletion is your call.


## Substrate CLI

### 🔴 state-hand-edited
`<path> is missing <fields>. It is written by `podpack substrate` and not meant to be edited by hand; restore it from version control.  (also: cannot read substrate.json: <exc>)`

- **Critical** · **where:** either · **from:** `substrate/__init__.py`
- **Means:** substrate.json was hand-edited, truncated, or corrupt. Exit 2 distinguishes corruption from ordinary pending work (exit 1).
- **Do:** `git checkout substrate.json`.

### 🔴 state-schema-newer
`<path> was written with substrate schema <N>, and this podpack understands <M>. Upgrade podpack, or restore the substrate.json that matches the pinned version.`

- **Critical** · **where:** either · **from:** `substrate/__init__.py`
- **Means:** substrate.json came from a NEWER podpack (a pin was rolled back). Refuses rather than misread it.
- **Do:** Upgrade podpack, or restore the matching substrate.json from git.

### 🟠 cli-conflicts-summary
`<N> conflict(s): the .new files hold podpack's version; resolve each with --take-upstream PATH or --keep PATH`

- **Needs action** · **where:** either · **from:** `podpack cli`
- **Means:** Upgrade finished with unresolved conflicts; the recorded podpack_version did NOT advance (stays visibly pending).
- **Do:** Resolve each .new with --take-upstream or --keep, then re-run upgrade.

### 🟠 cli-no-state
`no substrate.json here -- run `podpack substrate init` first  (or: substrate.json already exists here -- ... upgrade is the command that moves it forward)`

- **Needs action** · **where:** either · **from:** `podpack cli`
- **Means:** This directory was never initialised (or you ran init on an already-initialised site).
- **Do:** `podpack substrate init` for a new site; `podpack substrate upgrade` to move an existing one forward.

### 🟠 st-conflict
`<file>  conflict   (upgrade: podpack's version goes to <file>.new -- resolve with --take-upstream or --keep)`

- **Needs action** · **where:** either · **from:** `podpack substrate`
- **Means:** You edited a managed file AND upstream changed it differently; the three-way merge can't be automatic. podpack writes its version beside yours as <file>.new and does NOT advance the recorded version.
- **Do:** Diff the .new, then `podpack substrate upgrade --take-upstream <file>` (your copy saved as .orig) or `--keep <file>`.

### 🟠 st-new-vars-pending
`<file>  new variables pending: <VAR1>, <VAR2>   (or, during upgrade: appended new variables)`

- **Needs action** · **where:** either · **from:** `podpack substrate`
- **Means:** A newer podpack defines env vars your .env.example/.env has never been offered; upgrade appends them under a '# --- added by podpack substrate upgrade ---' banner (values may arrive as CHANGEME).
- **Do:** `podpack substrate upgrade` to append them, then set any CHANGEME values.

### 🟠 st-secrets-add-by-hand
`secrets.env  add by hand: <VAR1>, <VAR2>   (or: needs new secrets)`

- **Needs action** · **where:** either · **from:** `podpack substrate`
- **Means:** secrets.env is missing secrets a newer podpack expects. podpack will NEVER write this file (a default here would be a weak credential on its way to prod).
- **Do:** Add the named secrets to secrets.env yourself; secrets.env.example shows their shape.

### 🟡 st-locally-edited
`<file>  locally edited`

- **Warning** · **where:** either · **from:** `podpack substrate status`
- **Means:** You edited a managed file and upstream has not changed it; podpack keeps your edit. (This is what a site's own copy of a substrate file you changed on purpose shows -- e.g. an unreleased postgresql.conf tweak.)
- **Do:** Nothing needed. `podpack substrate diff <file>` shows the drift.

### 🟡 st-not-managed
`<file>  not managed here (outside the site / not a regular file / a dangling symlink)`

- **Warning** · **where:** either · **from:** `podpack substrate status`
- **Means:** The path (or a parent) is a symlink resolving outside the site, or the target is a directory/device/dangling symlink where a file was expected. podpack refuses to follow it.
- **Do:** Check for a stray symlink or odd entry on that path if you expected podpack to manage it.

### 🔵 st-status-words
`<file>  ok | update available | update available (already applied) | seeded at <v> | seeded at <v>, since edited | removed by site`

- **Info** · **where:** either · **from:** `podpack substrate status`
- **Means:** Benign per-file bookkeeping from `podpack substrate status`. 'update available (already applied)' = disk already equals the new version, only the recorded baseline lags. 'seeded ... since edited' = you edited a seed/config file, which podpack never rewrites wholesale.
- **Do:** Mostly nothing. `podpack substrate upgrade` settles any 'update available' by re-baselining.


## Containers & database

### 🔴 build-git-not-found
`Git executable not found  (uv, during uv sync in the build)`

- **Critical** · **where:** either · **from:** `Containerfile / uv`
- **Means:** An app locked to a git source needs git at build time. (Fixed in the Containerfile; only bites a customised base image.)
- **Do:** Ensure the builder stage still installs git.

### 🔴 gated-dependency-failed
`dependency failed to start: container <project>-<svc>-1 exited (<code>)  /  service "web" ... depends on ... which did not complete successfully (or ... is unhealthy)`

- **Critical** · **where:** either · **from:** `podman compose`
- **Means:** A gate service (init-storage, init-postgres, migrate) failed, or postgres never went healthy, so web was never started. web is a symptom, not the cause.
- **Do:** Read the NAMED service's own logs: `podman compose logs <service>`. Fix the root cause (perms, DB, migration), then ./scripts/up.sh.

### 🔴 pg-auth-failed
`FATAL: password authentication failed for user "<user>"`

- **Critical** · **where:** either · **from:** `postgres / pg_hba.conf`
- **Means:** TCP clients must SCRAM-authenticate; the supplied password is wrong or the role's stored hash predates a password change.
- **Do:** Verify the password in secrets.env matches the role. If you changed it, the role's stored hash must be updated (or re-arm the cluster).

### 🔴 pg-config-file-missing
`could not open configuration file "/etc/postgresql/postgresql.conf": No such file or directory  (or pg_hba.conf / pg_ident.conf)`

- **Critical** · **where:** either · **from:** `postgres`
- **Means:** One of the three config files isn't mounted. postgresql.conf names hba_file/ident_file explicitly, so all three must be mounted together.
- **Do:** Check the three ./config/pg_*.conf:/etc/postgresql/...:ro mounts.

### 🔴 pg-db-missing
`FATAL: database "<db>" does not exist  /  FATAL: role "<user>" does not exist`

- **Critical** · **where:** either · **from:** `postgres`
- **Means:** Connecting to a DB/role the bootstrap never created -- wrong POSTGRES_DB/POSTGRES_APP_USER vs the URI, or the empty-dir bootstrap was skipped.
- **Do:** Check POSTGRES_DB/POSTGRES_APP_USER vs the URI's dbname/user in secrets.env; re-arm if the cluster predates the setting.

### 🔴 pg-wrong-permissions
`FATAL: data directory "/var/lib/postgresql/data/pgdata" has invalid permissions -- Permissions should be u=rwx (0700)`

- **Critical** · **where:** either · **from:** `postgres`
- **Means:** PGDATA isn't mode 0700 -- usually because someone pre-created the pgdata sub-directory, or the mount point's 0777 (macOS virtiofs) leaked in.
- **Do:** Never pre-create .../data/pgdata -- let initdb make it. Delete the bad dir and let the stack recreate it.

### 🟠 compose-sentinel
`required variable "COMPOSE_FILE" is missing a value: compose.yaml alone is not a complete podpack stack. Every backing service is an overlay named in COMPOSE_FILE -- set it in .env, e.g. COMPOSE_FILE=compose.yaml:compose.postgres.yaml`

- **Needs action** · **where:** either · **from:** `compose.yaml`
- **Means:** COMPOSE_FILE is unset, so compose reads only compose.yaml -- an incomplete stack with no database. Caught at interpolation, before web fails to resolve a hostname.
- **Do:** Set COMPOSE_FILE=compose.yaml:compose.postgres.yaml in .env.

### 🟠 pg-init-skipped
`(bootstrap lines absent; later) role "<app_user>" does not exist`

- **Needs action** · **where:** either · **from:** `postgres`
- **Means:** /docker-entrypoint-initdb.d only runs on an empty data dir. A leftover host data dir means the role was never created.
- **Do:** To re-arm, stop the stack and delete $HOST_DATA_DIR/postgres (on Linux: `podman unshare rm -rf ...`), then ./scripts/up.sh.

### 🟠 pg-reload-as-root
`pg_ctl: cannot be run as root`

- **Needs action** · **where:** either · **from:** `postgres`
- **Means:** `pg_ctl reload` refuses to run as root.
- **Do:** `podman compose exec -u postgres postgres pg_ctl reload`.

### 🟡 healthcheck-unhealthy
`container STATUS shows health: unhealthy (probe: python /app/healthcheck.py -> /healthz, exit 0 only on HTTP 200)`

- **Warning** · **where:** either · **from:** `container/healthcheck.py`
- **Means:** /healthz didn't return 200 within the window (interval 10s, retries 6, start_period 10s). Sticks unhealthy -> the stack won't serve.
- **Do:** `podman compose logs web`; hit /healthz for the JSON reason (healthz-503 = DB down, the usual cause).

### 🔵 migrate-running
`INFO [alembic.runtime.migration] Running upgrade <rev> -> <rev>, <msg>`

- **Info** · **where:** either · **from:** `migrate service`
- **Means:** The one-shot migrate service is bringing the schema to head before web starts. Normal.
- **Do:** Nothing.

### 🔵 pg-connection-noise
`connection received / connection authorized: user=<u> database=<d> / checkpoint starting / disconnection`

- **Info** · **where:** either · **from:** `postgres`
- **Means:** Expected operational logging (log_connections/log_disconnections/log_checkpoints are on). Logs now rotate as postgresql-<Day>.log, a week of history at most.
- **Do:** Nothing.

### 🔵 pg-init-role
`creating application role '<POSTGRES_APP_USER>' in database '<POSTGRES_DB>' ... CREATE ROLE ... CREATE SCHEMA ... application role created`

- **Info** · **where:** either · **from:** `postgres db-init`
- **Means:** First-run bootstrap creating the least-privilege app role + app schema. Runs ONLY while the data dir is empty (first time on this machine).
- **Do:** Nothing. If it did NOT run on a fresh host, the data dir wasn't empty (see pg-init-skipped).

### 🔵 pg-ready
`database system is ready to accept connections`

- **Info** · **where:** either · **from:** `postgres`
- **Means:** Server up and listening -- the line the healthcheck waits for.
- **Do:** Nothing.


## External tools — git, uv, podman, nginx

### 🔴 nginx-502
`an HTML page whose body says "502 Bad Gateway" with a Server: nginx header (nginx's own error page, not a podpack response). 504 = upstream too slow.`

- **Critical** · **where:** host · **from:** `nginx (Opalstack proxy)`
- **Means:** The site container isn't accepting connections on WEB_HOST_PORT -- down, unhealthy, wrong port, or never started (linger/gate failure). A status-code-only monitor can be fooled; the 502 body is nginx-generated, which is why poll-health.sh checks the body.
- **Do:** `podman compose ps` / `logs web`; confirm the container is healthy and bound to the allocated port.

### 🔴 podman-compose-vs-plugin
`(no error) services that should wait start in the same second -- the tell-tale of running under `podman-compose` (hyphen) instead of `podman compose` (space)`

- **Critical** · **where:** either · **from:** `podman-compose`
- **Means:** podman-compose (the Python tool) silently IGNORES depends_on conditions -- every ordering gate rests on them. init-storage stops preceding servers (perms break), web stops waiting for migrate, nothing waits for Postgres. A broken front end, not an alternative.
- **Do:** Use `podman compose` (space). `configure-host.py --check` verifies the provider is Compose v2.

### 🔴 uv-installation-plan-path
`error: Failed to determine installation plan ... Distribution not found at: file:///path/to/podpack`

- **Critical** · **where:** either · **from:** `uv`
- **Means:** A [tool.uv.sources] path = ... source can't be resolved inside the container build -- the build context has no such path. (This is why the site pins podpack from PyPI and the apps from git, never a local path.)
- **Do:** Switch the dependency to a git = "https://..." (or published) source, then `uv lock`.

### 🟠 git-denycurrentbranch
`remote: error: refusing to update checked out branch: refs/heads/<branch> ... updating the current branch in a non-bare repository is denied ... ! [remote rejected] <branch> -> <branch> (branch is currently checked out)`

- **Needs action** · **where:** host · **from:** `git`
- **Means:** You pushed to the branch checked out on the server's working checkout, and receive.denyCurrentBranch is at its default. Git won't move the branch out from under a live worktree.
- **Do:** On the host: `git config receive.denyCurrentBranch updateInstead` in ~/apps/<app>/site, then push again. (ops/DEPLOY.md sets this up.)

### 🟠 git-non-fast-forward
`! [rejected] <branch> -> <branch> (fetch first / non-fast-forward) ... the remote contains work that you do not have locally.`

- **Needs action** · **where:** either · **from:** `git`
- **Means:** The remote has commits you don't -- common when a deploy host committed a config edit.
- **Do:** `git pull --rebase` then push. Never force-push a shared deploy remote without care.

### 🟠 git-updateinstead-dirty
`! [remote rejected] <branch> -> <branch> (Working directory has unstaged changes)  /  (Untracked working tree files would be overwritten by merge)`

- **Needs action** · **where:** host · **from:** `git`
- **Means:** updateInstead refuses when the server worktree is dirty or a push would overwrite untracked files -- it won't clobber edits made on the host. Config edits made in-place on the deploy checkout are the usual culprit.
- **Do:** On the server, commit/stash/discard the local changes (or move the untracked files), then push again.

### 🟠 podman-no-such-service
`no such service: <name>   (notably `no such service: .` from a command pasted with a trailing period)`

- **Needs action** · **where:** either · **from:** `podman compose`
- **Means:** A service name doesn't exist in the merged compose files -- a typo, wrong COMPOSE_FILE, or punctuation pasted with an inline command.
- **Do:** Check the name / COMPOSE_FILE. Put runnable commands on their own line so no trailing '.' is pasted.

### 🟠 uv-git-fetch-failed
`error: Failed to download and build `<pkg> @ git+https://...` ... Git operation failed (repository not found / could not read Username)`

- **Needs action** · **where:** either · **from:** `uv / git`
- **Means:** A git dependency's repo is private, unpublished, or mistyped.
- **Do:** Publish/point at the correct repo, or ensure credentials; then `uv lock`.

### 🟠 uv-lockfile-frozen
`error: The lockfile at `uv.lock` needs to be updated but `--frozen` was provided. To update the lockfile, run `uv lock`.  (also the --locked / --check variants)`

- **Needs action** · **where:** either · **from:** `uv`
- **Means:** pyproject.toml or [tool.uv.sources] changed but uv.lock wasn't regenerated; the frozen build refuses to drift. Editing a pin alone isn't enough.
- **Do:** `uv lock` and commit uv.lock, then rebuild/deploy.

