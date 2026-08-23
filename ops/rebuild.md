# Rebuild: bare host to serving site

**Meant to be followed, not read.** The reasoning lives in
[`operations.md`](../operations.md) and this links there rather than repeating
it — one place per fact, or they drift, which is how §6 came to say this site
lacks a script it has had since 0.7.1.

**Every command below is literal.** Nothing has a placeholder in it: the values
that change between one rebuild and the next are gathered into the
configuration block, and every step after that refers to them by name. Fill the
block in once, paste it into your shell, and the rest is copy-and-run.

Where a command's output disagrees with what is written, record it and **carry
on**. Do not fix as you go: fixing as you go means only the steps before the
first problem are ever exercised, which is how a procedure passes its own
rehearsal.

- **`☐`** — as written; tick and move on.
- **`✎`** — write what differed.

---

## Configuration

Fill in, then paste the whole block into the shell you will work in. Anything
you cannot know yet is marked with the step that tells you.

```bash
export SITE_REPO=git@github.com:holdenweb/holdenweb-com.git
export SITE_DIR=holdenweb.com
export MODE=RESTORE
export WEB_PORT=
export SITE_HOST=
export BACKUP=
export ADMIN_EMAIL=
```

| Variable | Meaning | Known at |
| --- | --- | --- |
| `SITE_REPO` | Where the site's git repository lives | now |
| `SITE_DIR` | Directory to clone into. **Not a second checkout of a site already deployed on this host** — see 2.1 | now |
| `MODE` | `RESTORE` or `FRESH` — see below | now |
| `WEB_PORT` | The port the control panel allocated | **1.1** |
| `SITE_HOST` | The hostname proxied to that port | **1.2** |
| `BACKUP` | The backup directory to restore from | **3.1** |
| `ADMIN_EMAIL` | Administrator's address. `FRESH` only | **6.1** |

Check it took, before you rely on it:

```bash
: "${SITE_REPO:?}" "${SITE_DIR:?}" "${MODE:?}" && echo "configuration loaded"
```

### `MODE` — the one decision

| | **RESTORE** | **FRESH** |
| --- | --- | --- |
| | This site's data comes back | An empty site on a new host |
| Typical cause | The host died; you are putting it back | A new deployment, or a staging copy |
| Accounts | Everyone can still sign in | Nobody has an account yet |

**Only three steps differ — 3.2, 4.2 and 6.1 — and each says so where it
arrives.** Everything else is identical, which is why this is one document and
not two.

> The one defect that cost real time in rehearsal 1 was a step that did *not*
> branch when it should have. If a step below looks like it assumes the other
> path, that is a bug in this document; record it.

### Timing

Each part opens with a `date` command. Run it — the timestamps land in your
terminal transcript, so timing costs no attention, and the total is the single
number a 3am document most needs. There is a table to fill in at the end.

---

## Part 0 — before anything is destroyed

*Rehearsal only. In a real emergency the host is already gone; start at Part 1.*

```bash
date -u +%H:%M:%S
```

**0.1 — Take the backup you will restore from.**

`backup.sh` refuses to write inside the working tree, because the result holds a
verbatim copy of every secret. That guard resolves the destination's parent, so
create it first — if the parent does not exist the check cannot run:

```bash
mkdir -p ~/backups
```

```bash
./scripts/backup.sh
```

```bash
./scripts/verify-backup.sh
```

*Expect:* a directory under `~/backups/<site>/`, mode 0700, holding
`manifest.txt`, `plan.json`, `database.pgc`, `app-data.tar.gz`,
`config.tar.gz`, `rowcounts.txt`, `env` — no leading dot — and `secrets.env`.
`verify-backup.sh` ends `VERIFIED:` and names the git commit and alembic
revision.

`☐` `✎` ______________________________________________

**0.2 — Record the host as it is**, so the rebuild can be compared to it.

```bash
python3 scripts/configure-host.py --check
```

```bash
podman compose ps
```

*Expect:* `--check` writes nothing, and reports which values are still the
example's.

`☐` `✎` ______________________________________________

---

## Part 1 — the control panel  *(human; nothing in git knows any of it)*

```bash
date -u +%H:%M:%S
```

**1.1** In the Opalstack panel, create or confirm the application and note the
port it allocates. **1.2** Confirm the hostname proxied to that port. These are
the only two inputs this document cannot derive, so put them in the
configuration now:

```bash
export WEB_PORT=
export SITE_HOST=
```

```bash
: "${WEB_PORT:?}" "${SITE_HOST:?}" && echo "$SITE_HOST -> 127.0.0.1:$WEB_PORT"
```

`☐` `✎` ______________________________________________

---

## Part 2 — clone, and configure the host

```bash
date -u +%H:%M:%S
```

**2.1**

```bash
git clone "$SITE_REPO" "$SITE_DIR"
```

```bash
cd "$SITE_DIR"
```

*Expect:* `config/`, `src/` and `alembic/` present — those are in git, and git
is their backup. No `.env`, no `secrets.env`, no `hostdata/`.

> **Do not run compose from any other checkout of this site while you work.**
> Two directories are separate compose projects, but a build in one tags the
> other's image name, so the second `up.sh` can quietly serve the first's code.

`☐` `✎` ______________________________________________

**2.2**

```bash
python3 scripts/configure-host.py --port "$WEB_PORT"
```

*Expect:* `wrote .env and secrets.env (0600)`, then the port, the database and
role, whether SELinux is enforcing, and that secrets were generated with none
printed. It **refuses to overwrite** either file, so a second run is safe.

*Watch for:* the SELinux line. `not enforcing` leaves `VOLUME_RW`/`VOLUME_RO`
empty and is correct on a permissive host; `detected` sets them to `:Z`/`,z`.
Both are right answers — the wrong answer is the file not saying. A host can be
*labelled but permissive*, which is what Opalstack is today: if it is ever
switched to enforcing, this decision changes and the mounts break.

`☐` `✎` ______________________________________________

---

## Part 3 — the content and the database

```bash
date -u +%H:%M:%S
```

**3.1 — Name the backup**, once, and let every later step refer to it:

```bash
export BACKUP=
```

```bash
ls -l "${BACKUP:?}/database.pgc" "$BACKUP/app-data.tar.gz" "$BACKUP/secrets.env"
```

*Expect:* three files. This is also why the variable exists — written literally,
`< <backup>/database.pgc` is a bash syntax error, because `< <` is process
substitution.

`☐` `✎` ______________________________________________

### 3.2 — **BRANCHES**

**`MODE=RESTORE` — put the backup's secrets back.** This is what makes it a
restore rather than a new site:

```bash
install -m 600 "$BACKUP/secrets.env" ./secrets.env
```

**`MODE=FRESH` — skip it.** Keep the `secrets.env` that 2.2 generated.

> **What the choice decides.** `SECURITY_PASSWORD_SALT` is HMAC'd with every
> password before it is hashed, so a fresh salt invalidates every stored
> password; `SECRET_KEY` invalidates sessions and outstanding reset links. On
> `RESTORE` everyone can still sign in. On `FRESH` nobody can, and that is
> correct rather than broken.

`☐` `✎` ______________________________________________

**3.3 — Restore the app data**, before starting anything.

```bash
./scripts/prepare-host-dirs.sh
```

```bash
tar -xzf "$BACKUP/app-data.tar.gz" -C ./hostdata
```

```bash
du -sh hostdata/apps/*
```

*Expect:* `pages` holding roughly 1.0 MB — the site's content, in
subdirectories. `qrcode` and `pp_pdf` empty, correctly: both are stateless.

> `/_status` will report `"stored_files": []` for `pages` regardless, because
> that field lists top-level files only and cannot see a directory. Check the
> disk, as above, when you want to know whether content came back.

`☐` `✎` ______________________________________________

---

## Part 4 — bring it up

```bash
date -u +%H:%M:%S
```

**4.1**

```bash
./scripts/up.sh
```

*Expect:* `postgres` healthy, `migrate` exited cleanly, `web` started.

> **`db-init` runs exactly once** — only while the postgres data directory is
> still empty. It is what creates `SCHEMA app AUTHORIZATION <app role>` and
> grants `CONNECT`. That matters in the next step.

`☐` `✎` ______________________________________________

### 4.2 — **BRANCHES**

Drop and recreate first; the dump carries its own schema.

```bash
podman compose exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

> This throws away everything `db-init` did, and `db-init` will not run again.
> It works because the dump restores its own ownership and PostgreSQL grants
> `CONNECT` to `PUBLIC` on a new database. Both are load-bearing and neither is
> obvious.

**`MODE=RESTORE` — no `--no-owner`.** The roles came back with `secrets.env`, so
the dump's ownership is correct:

```bash
podman compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error' < "$BACKUP/database.pgc"
```

**`MODE=FRESH` — `--no-owner`.** The dump names a role this host does not have:

```bash
podman compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < "$BACKUP/database.pgc"
```

> **Getting this backwards breaks the site three steps later.** `--no-owner` on
> the `RESTORE` path makes the *admin* own schema `app`, while the application
> connects as the app role with `search_path = app`. It surfaces as `migrate`
> failing with what reads like a broken migration. Observed, rehearsal 1.

```bash
podman compose restart web
```

`☐` `✎` ______________________________________________

**4.3 — Row counts, against the backup's own record.**

```bash
cat "$BACKUP/rowcounts.txt"
```

`☐` `✎` ______________________________________________

---

## Part 5 — the settings nothing will tell you about

```bash
date -u +%H:%M:%S
```

Both are absent from a freshly configured host, and neither has a symptom you
would see by looking at the site.

**5.1 — The proxy.**

```bash
echo 'PODPACK_PROXY_HOPS=1' >> .env
```

```bash
podman compose up -d --force-recreate web
```

```bash
podman compose exec web printenv PODPACK_PROXY_HOPS
```

*Expect:* `1`. Empty means the line went into a different `.env`, or carries an
`export ` prefix — compose's `env_file` is not a shell and would read the name
as `export PODPACK_PROXY_HOPS`.

> **This site can never be told this by podpack.** The variable's entire
> documentation lives in `env.example`, and this site's copy is a *seeded*
> substrate file — `podpack substrate upgrade` reports every file `ok` and
> delivers nothing. Without the line, every URL built with `_external=True`
> comes out `http://`, and the first thing to carry one is a password-reset
> mail.

*Note:* the count is the number of values in `X-Forwarded-Proto`, not the
number of proxies. One nginx that overwrites the header is `1` however many
boxes sit behind it.

`☐` `✎` ______________________________________________

**5.2 — The mail password.** On `RESTORE` it came back with `secrets.env`; on
`FRESH` it is still the example value and 2.2 said so. Either way, prove it:

```bash
podman compose exec web flask --app holdenweb mail check
```

*Expect:* the server, the username, the *shape* of the password — never its
value — then a real SMTP connection, exit 0.

`☐` `✎` ______________________________________________

---

## Part 6 — verify

```bash
date -u +%H:%M:%S
```

### 6.1 — **BRANCHES**

**`MODE=RESTORE` — nothing to do.** Your accounts came back with `secrets.env`;
sign in as yourself.

**`MODE=FRESH` — make an administrator**, or `/_status` answers nobody:

```bash
export ADMIN_EMAIL=
```

```bash
podman compose exec web flask --app holdenweb users create "${ADMIN_EMAIL:?}" --active
```

```bash
podman compose exec web flask --app holdenweb roles create admin
```

```bash
podman compose exec web flask --app holdenweb roles add "$ADMIN_EMAIL" admin
```

> The first **stops and asks for a password**. The address must be able to
> receive mail: flask-security checks deliverability, so `you@example.com` is
> refused — that domain publishes no MX record.

`☐` `✎` ______________________________________________

**6.2 — `/_status`**, signed in as an administrator. Unauthenticated it answers
404, correctly, so this is a browser step — but the health endpoint is not, and
answers now:

```bash
curl -s "http://127.0.0.1:$WEB_PORT/healthz"
```

*Expect:* `{"database":"ok","status":"ok"}` here, and in the browser
`proxy.hops_trusted: 1`, `proxy.scheme: "https"`, `build_commit` matching what
you deployed, and the database and role you configured.

`☐` `✎` ______________________________________________

**6.3 — The integration suite**, which is the real check
([`operations.md` §3](../operations.md)). Never the front page: the QR code app
answered 200 for weeks while contributing no navigation at all.

```bash
uv run pytest tests/integration --base-url "https://$SITE_HOST"
```

*Expect:* 15 passed, and a header naming what it tested. **Run it against the
host you just built** — a suite pointed at the old deployment passes and proves
nothing, which is how rehearsal 1 left the restore path unverified.

`☐` `✎` ______________________________________________

**6.4 — The one that matters.** Request a password reset, and read the mail.

*Expect:* a link beginning **`https://`**. An `http://` link means 5.1 did not
take, and `/_status` says which half — header not sent, or hops not trusted.

`☐` `✎` ______________________________________________

**6.5 — Prove the backup regime on *this* host.**

```bash
./scripts/backup.sh && ./scripts/verify-backup.sh
```

`☐` `✎` ______________________________________________

```bash
date -u +%H:%M:%S
```

---

## Timing

| Part | Started | |
| --- | --- | --- |
| 0 — before the wipe | ________ | *rehearsal only* |
| 1 — control panel | ________ | |
| 2 — clone and configure | ________ | |
| 3 — content and database | ________ | |
| 4 — bring it up | ________ | |
| 5 — the hidden settings | ________ | |
| 6 — verify | ________ | |
| **finished** | ________ | |

**Parts 1–6 elapsed: ________** — the number to quote when somebody asks how
long the site is down for.

---

## What this does not cover

- **DNS.** No TTL drop, no cutover. [`operations.md` §7](../operations.md)
  phase 2 is a different procedure and is still unrun.
- **Continuity.** This is a rebuild, not a move; the site is down throughout.
- **Noticing.** Nothing polls `/healthz`, so every step above assumes somebody
  already knows. That is upstream of this whole document.

*Rehearsal 1's marked-up run is kept at
[`rehearsal-2026-08-23.md`](rehearsal-2026-08-23.md). A browser version of this
page, with a copy button on every command, comes from
`python3 ops/render-rebuild.py > scratch/rebuild.html` — generated, so it cannot
drift from this file.*
