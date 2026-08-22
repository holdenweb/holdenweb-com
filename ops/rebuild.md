# Rebuild: bare host to serving site

**Print this and mark it up.** It is meant to be *followed*, not read — the
reference is [`operations.md`](../operations.md), and this links there rather
than repeating it.

Every step gives the command and **what you should see**. Where they disagree,
that is a finding: write what happened in the margin and **carry on**. Do not
fix as you go — fixing as you go means only the steps before the first problem
ever get exercised, which is how a procedure passes its own rehearsal.

Note the time when you start each part. A runbook that is correct but slow
fails differently at 3am, and only a clock catches it.

- **`☐` as written** — tick and move on.
- **`✎`** — write what differed.

---

## Part 0 — before anything is destroyed

Only for the rehearsal. In a real emergency the host is already gone and you
start at Part 1.

**0.1 — Why did `PODPACK_PROXY_HOPS` never reach the container?** Settle it
before the evidence is wiped.

```bash
podman compose exec web printenv PODPACK_PROXY_HOPS
grep -n PROXY .env
```

*Expect:* the first prints `1`; if it prints nothing, the second shows why —
an `export ` prefix (compose's `env_file` is not a shell and reads the name as
`export PODPACK_PROXY_HOPS`), a stray quote, or the line absent because it went
into a different `.env`.

`☐` `✎` ______________________________________________

**0.2 — Take production's backup.** This is the restore source.

```bash
# on the PRODUCTION host
./scripts/backup.sh
./scripts/verify-backup.sh
```

*Expect:* a directory under `~/backups/holdenweb-com/`, mode 0700, containing
`manifest.txt`, `database.pgc`, `app-data.tar.gz`, `rowcounts.txt`, `.env` and
`secrets.env`. `verify-backup.sh` exits 0.

> Both scripts are marked ⚠️ in `operations.md` — never run on this host. This
> is the first time. Treat a clean run as a finding too.

`☐` `✎` ______________________________________________

**0.3 — Record the host as it is**, so the rebuild can be compared to it.

```bash
python3 scripts/configure-host.py --check
podman compose ps
curl -s localhost:<WEB_HOST_PORT>/healthz
```

*Expect:* `--check` writes nothing and reports which values are still the
example's, and whether this host can run containers.

`☐` `✎` ______________________________________________

---

## Part 1 — the control panel  *(human, and nothing in git knows it)*

**1.1** In Opalstack, create the application (or confirm the existing one) and
**write down the port it allocates**: ____________

**1.2** Confirm the domain binding — which hostname is proxied to that port:
____________

*These two numbers are the only inputs the rest of the document cannot derive.*

`☐` `✎` ______________________________________________

---

## Part 2 — clone, and configure the host

**2.1**

```bash
git clone git@github.com:holdenweb/holdenweb-com.git holdenweb.com
cd holdenweb.com
```

*Expect:* `config/`, `src/` and `alembic/` present — those are in git, and git
is their backup. No `.env`, no `secrets.env`, no `hostdata/`.

`☐` `✎` ______________________________________________

**2.2**

```bash
python3 scripts/configure-host.py --port <the port from 1.1>
```

*Expect:* `wrote .env and secrets.env (0600) for 'holdenweb.com'`, then four
lines reporting the port, the database and role, whether SELinux is enforcing,
and that secrets were generated and none printed. It **refuses to overwrite**
either file, so a second run is safe and says so.

*Watch for:* the SELinux line. `not enforcing` means `VOLUME_RW`/`VOLUME_RO`
stay empty and that is correct; `detected` means they are set to `:Z`/`,z`. Both
are right answers — the wrong answer is the file not saying.

`☐` `✎` ______________________________________________

---

## Part 3 — restore the content and the database

**3.1 — Get the backup onto this host.** From 0.2, or the latest under
`~/backups/holdenweb-com/`.

`☐` `✎` ______________________________________________

**3.2 — The secrets decision.** Two different procedures; know which you are in.

| | Do this | Consequence |
| --- | --- | --- |
| **Real restore** | `install -m 600 <backup>/secrets.env ./secrets.env` | Site keeps its identity. Everyone can still log in. |
| **This rehearsal** | *Skip it* — keep the generated `secrets.env` | **Nobody can log in to the rebuilt site.** |

> **Why, and it is not a bug.** `SECURITY_PASSWORD_SALT` is HMAC'd with every
> password before it is hashed, so a fresh salt invalidates every stored
> password in the restored `user` table. `SECRET_KEY` invalidates sessions and
> any outstanding reset links. This is exactly why the real procedure restores
> `secrets.env` verbatim — the rehearsal deliberately does not, so that
> production's `SECRET_KEY` never lands on a second host.
>
> **So §6 step 2 is NOT tested by this rehearsal.** Record that as a known gap
> rather than letting a clean run imply otherwise.

`☐` `✎` ______________________________________________

**3.3 — Restore the app data**, before starting anything.

```bash
./scripts/prepare-host-dirs.sh
tar -xzf <backup>/app-data.tar.gz -C ./hostdata
```

*Expect:* `hostdata/apps/pages/` holding roughly 1.0 MB — the site's content.
`qrcode/` and `pp_pdf/` are empty, correctly: both declare themselves stateless.

`☐` `✎` ______________________________________________

---

## Part 4 — bring it up

**4.1**

```bash
./scripts/up.sh
```

*Expect:*

```
holdenweb-com-postgres-1   Up ... (healthy)
holdenweb-com-web-1        Up ... (healthy)
```

`db-init` creates the role and database from `secrets.env`; `migrate` builds the
schema from the alembic history. If `migrate` fails while postgres reports
healthy, that is the SELinux row in `operations.md` §14.

`☐` `✎` ______________________________________________

**4.2 — Load the data over that schema.** The dump carries the same schema, so
drop and recreate first.

```bash
podman compose exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
podman compose exec -T postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < <backup>/database.pgc
podman compose restart web
```

> **`--no-owner` is needed here and not in a real restore.** The dump names
> production's role; this host generated its own. In a real restore the role
> came back with `secrets.env` and the objects land owned correctly without it.

*Expect:* silence from `pg_restore`. Any error, and `--exit-on-error` stops it.

`☐` `✎` ______________________________________________

**4.3 — Check the row counts against the backup's own record.**

```bash
cat <backup>/rowcounts.txt
```

`☐` `✎` ______________________________________________

---

## Part 5 — the two settings nothing will tell you about

Both are missing on a freshly configured host, and neither has a symptom you
would notice by looking at the site.

**5.1 — The proxy.** In `.env`:

```bash
PODPACK_PROXY_HOPS=1
```

then `podman compose up -d --force-recreate web`.

> This site's `.env.example` is a **seeded** substrate file, so it will never
> document this variable however far podpack advances — `podpack substrate
> upgrade` reports every file `ok` and delivers nothing. That is why the line is
> written here instead.

*Expect afterwards:* `/_status` reports `"hops_trusted": 1` and
`"scheme": "https"`.

`☐` `✎` ______________________________________________

**5.2 — The mail password.** `configure-host.py` reports which values are still
the example's, and `MAIL_PASSWORD` will be one of them. Set the real Gmail App
Password in `secrets.env` — sixteen letters, spaces removed, **no `$`**, which
compose expands in `secrets.env` as well as `.env`. Then:

```bash
podman compose up -d web
podman compose exec web flask --app holdenweb mail check
```

*Expect:* the server, the username, the *shape* of the password — never its
value — then a real SMTP connection, exit 0.

`☐` `✎` ______________________________________________

---

## Part 6 — verify

**6.1 — An administrator.** Restored accounts cannot sign in (3.2), so make one.

```bash
podman compose exec web flask --app holdenweb users create <your real address> --active
podman compose exec web flask --app holdenweb roles create admin
podman compose exec web flask --app holdenweb roles add <your real address> admin
```

*It will stop and ask for a password.* The address must be one that could
receive mail — flask-security checks deliverability.

`☐` `✎` ______________________________________________

**6.2 — `/_status`**, signed in as that administrator. Reports the installed
apps, where each keeps its state, the database and role actually connected, the
commit the image came from, and `proxy`.

`☐` `✎` ______________________________________________

**6.3 — The integration suite**, which is the real check (`operations.md` §3).
Never the front page: the QR code app answered 200 for weeks while contributing
no navigation at all.

```bash
uv run pytest tests/integration --base-url https://<the hostname from 1.2>
```

*Expect:* 15 tests, and a header naming what it tested.

`☐` `✎` ______________________________________________

**6.4 — The thing that started all this.** Request a password reset for the
account from 6.1, and read the mail.

*Expect:* a link beginning **`https://`**. An `http://` link means 5.1 did not
take, and `/_status` will say which half — header not sent, or hops not trusted.

`☐` `✎` ______________________________________________

**6.5 — Prove the backup regime on this host**, because a regime rehearsed
elsewhere has not been rehearsed here.

```bash
./scripts/backup.sh && ./scripts/verify-backup.sh
```

`☐` `✎` ______________________________________________

---

## What this rehearsal does not test

Say so out loud, so a clean run is not read as more than it is.

- **§6 step 2** — restoring `secrets.env` verbatim. Deliberately skipped (3.2).
- **`--no-owner` is not what a real restore uses** (4.2).
- **DNS.** No TTL drop, no cutover. `operations.md` §7 phase 2 stays untested.
- **Continuity.** This is a rebuild, not a move; the site is down throughout.
- **Noticing.** Nothing polls `/healthz`, so every step above assumes somebody
  already knows the site is down. That is backlog #8 and it is upstream of this
  whole document.
