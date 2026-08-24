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
| `BACKUP` | The backup directory to restore from. `RESTORE` only | **0.1**, or given |
| `ADMIN_EMAIL` | Administrator's address. `FRESH` only | **5.1** |

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

**The modes diverge in Part 3 and nowhere else that matters.** `RESTORE` is a
single command — `scripts/restore.sh` — because the substrate already ships the
whole procedure. `FRESH` has no dump, so it configures a host and starts it.
After Part 3 they rejoin, with one small branch at 5.1 over whether an
administrator already exists.

> Rehearsal 1's expensive defect was a step that did *not* branch when it
> should have — and the reason it existed at all was that this document was
> hand-rolling what `restore.sh` already did, in a worse order. If a step below
> looks like it assumes the other path, that is a bug here; record it.

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

**The site has to be up for this.** `backup.sh` asks the running `web` service
what to archive, and refuses without it — which is worth knowing before you need
it, because in the emergency where the site is down you *cannot take a backup*.
The last good one is whatever you already have. `verify-backup.sh` needs the
stack up too: it reads each dump with the store's own tooling, inside the store's
own container.

`backup.sh` also refuses to write inside the working tree, because the result
holds a verbatim copy of every secret. That guard resolves the destination's
parent, so create it first — if the parent does not exist the check cannot run:

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
example's plus whether this host can run containers — the Compose v2 provider,
the podman socket, and lingering. It needs `.env` and `secrets.env` to exist
already; on a bare clone it says `not configured yet` and stops.

> A backup that fails part way leaves nothing behind: `backup.sh` removes the
> destination if the plan names no store, if a dump comes out empty, or if a
> store named in the plan produced no file. So a directory that exists is a
> directory that got to the end.

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

## Part 2 — clone

```bash
date -u +%H:%M:%S
```

```bash
git clone "$SITE_REPO" "$SITE_DIR"
```

```bash
cd "$SITE_DIR"
```

*Expect:* `config/`, `src/` and `alembic/` present — those are in git, and git
is their backup. No `.env`, no `secrets.env`, no `hostdata/`.

> **Know which checkout you are in.** Two checkouts of one site coexist
> perfectly well provided two things differ: `SITE_NAME` *after compose
> normalises it* — dots are stripped, dashes kept, so `holdenweb.com` becomes
> `holdenwebcom` while `holdenweb-com` stays as it is — and `WEB_HOST_PORT`,
> which is the only genuine bind clash. Images do not collide: measured. What
> does go wrong is a person forgetting which directory they are in, which is
> most of what went wrong in rehearsal 1.

`☐` `✎` ______________________________________________

---

## Part 3 — **BRANCHES**: bring the site into existence

```bash
date -u +%H:%M:%S
```

This is where the two modes stop resembling each other. Follow one heading and
skip the other entirely.

### `MODE=RESTORE` — one command

Check the backup is the one you mean, and complete — `restore.sh` refuses on a
missing file, but reading the names first is cheaper than reading its refusal:

```bash
ls -l "${BACKUP:?}"
```

```bash
./scripts/restore.sh "$BACKUP"
```

That is the whole of it, and it is worth knowing what it is doing rather than
treating it as magic, because it stops twice to ask you things:

1. **Is this the right backup and the right target?** It prints what it is
   restoring from and into, and waits for you to type `restore`.
2. **Does the code match the data?** It compares the backup's commit against
   this checkout and says which way you are rolling — a newer checkout means
   alembic rolls the data forward, which is fine; an older one may not know
   about tables in the dump.

Then, in an order chosen to avoid the two traps that a hand-run restore falls
into: it puts `secrets.env` and `.env` back, keeping yours as
`.superseded-<stamp>`; unpacks the app data **before** the first `compose up`,
because `init-storage` hands the mounts to the containers' uids and does not
run twice; **removes each restored app's directory first**, because `tar` only
ever adds and a merge is a state that never existed; brings **each store up
alone**, so its bootstrap creates the role the dump's objects belong to; then
the rest of the stack, which makes `migrate` a free consistency check.

Finally it verifies out loud — every table's row count against
`rowcounts.txt`, and `/healthz` — and **exits non-zero** if either fails.

> **On a host whose port differs from the old one, expect it to fail at the
> last step, and expect that.** `.env` comes back from the backup carrying the
> *old* `WEB_HOST_PORT`, so the health check polls a port nothing is listening
> on. The data is restored correctly; only the last check is wrong. Fix it:
>
> ```bash
> sed -i "s/^WEB_HOST_PORT=.*/WEB_HOST_PORT=$WEB_PORT/" .env
> ```
>
> ```bash
> ./scripts/up.sh
> ```
>
> Check the other per-host values in `.env` while you are there —
> `WEB_BIND_ADDR`, and `VOLUME_RW`/`VOLUME_RO` if this host's SELinux differs
> from the old one's. `python3 scripts/configure-host.py --check` reports them
> without writing anything.

**Do not run `configure-host.py --port` on this path.** It would generate a
`.env` and `secrets.env` that `restore.sh` then replaces with the backup's, and
fresh secrets are the one thing a restore must not have.

`☐` `✎` ______________________________________________

### `MODE=FRESH` — no dump, so no `restore.sh`

```bash
python3 scripts/configure-host.py --port "$WEB_PORT"
```

*Expect:* `wrote .env and secrets.env (0600)`, then the port, the database and
role, whether SELinux is enforcing, and that secrets were generated with none
printed. It **refuses to overwrite** either file, so a second run is safe.

*Watch for:* the SELinux line. `not enforcing` leaves `VOLUME_RW`/`VOLUME_RO`
empty and is right on a permissive host; `detected` sets them to `:Z`/`,z`. A
host can be *labelled but permissive*, which is what Opalstack is today — if it
is ever switched to enforcing, this decision changes and the mounts break.

It also names any value still at the example's, which on this path will include
`MAIL_PASSWORD`. Set it now, in `secrets.env`: sixteen letters, spaces removed,
and **no `$`**, which compose expands there as well as in `.env`.

```bash
./scripts/prepare-host-dirs.sh
```

```bash
./scripts/up.sh
```

*Expect:* `postgres` healthy, `migrate` exited cleanly, `web` started.

`☐` `✎` ______________________________________________

---

## Part 4 — the setting nothing will tell you about

```bash
date -u +%H:%M:%S
```

Absent however the site got here, and with no symptom you would see by looking
at it.

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

**And prove the mail credential**, which came back with `secrets.env` on
`RESTORE` and was set by hand on `FRESH`:

```bash
podman compose exec web flask --app holdenweb mail check
```

*Expect:* the server, the username, the *shape* of the password — never its
value — then a real SMTP connection, exit 0.

`☐` `✎` ______________________________________________

---

## Part 5 — verify

```bash
date -u +%H:%M:%S
```

### 5.1 — **BRANCHES**

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

**5.2 — `/_status`**, signed in as an administrator. Unauthenticated it answers
404, correctly, so this is a browser step — but the health endpoint is not, and
answers now:

```bash
curl -s "http://127.0.0.1:$WEB_PORT/healthz"
```

*Expect:* `{"database":"ok","status":"ok"}` here, and in the browser
`proxy.hops_trusted: 1`, `proxy.scheme: "https"`, `build_commit` matching what
you deployed, and the database and role you configured.

`☐` `✎` ______________________________________________

**5.3 — The integration suite**, which is the real check
([`operations.md` §3](../operations.md)). Never the front page: the QR code app
answered 200 for weeks while contributing no navigation at all.

```bash
uv run pytest tests/integration --base-url "https://$SITE_HOST"
```

*Expect:* 15 passed, and a header naming what it tested. **Run it against the
host you just built** — a suite pointed at the old deployment passes and proves
nothing, which is how rehearsal 1 left the restore path unverified.

`☐` `✎` ______________________________________________

**5.4 — The one that matters.** Request a password reset, and read the mail.

*Expect:* a link beginning **`https://`**. An `http://` link means 5.1 did not
take, and `/_status` says which half — header not sent, or hops not trusted.

`☐` `✎` ______________________________________________

**5.5 — Prove the backup regime on *this* host.**

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
| 2 — clone | ________ | |
| 3 — restore, or configure | ________ | |
| 4 — the proxy setting | ________ | |
| 5 — verify | ________ | |
| **finished** | ________ | |

**Parts 1–5 elapsed: ________** — the number to quote when somebody asks how
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
