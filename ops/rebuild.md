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

`☐` `✎` Here's what actually happened:
```
[[sholden@opal17 holdenweb-com]$ podman compose exec web printenv PODPACK_PROXY_HOPS
grep -n PROXY .env
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

Error: executing /home/sholden/bin/docker-compose exec web printenv PODPACK_PROXY_HOPS: exit status 1
[sholden@opal17 holdenweb-com]$
```
So it looks like .env is missing a line. I'm not timing this as it's being fitted in among other work.  y the way, if you could let me know how to silence the "external compose provider" message I'd love it.

**0.2 — Take production's backup.** This is the restore source.

```bash
# on the PRODUCTION host
./scripts/backup.sh
./scripts/verify-backup.sh
```

*Expect:* a directory under `~/backups/holdenweb-com/`, mode 0700, containing
`manifest.txt`, `plan.json`, `database.pgc`, `app-data.tar.gz`, `config.tar.gz`,
`rowcounts.txt`, `env` — note, no leading dot — and `secrets.env`.
`verify-backup.sh` exits 0.

> Both scripts are marked ⚠️ in `operations.md` — never run on this host. This
> is the first time. Treat a clean run as a finding too.

`☐` `✎` The backup appeared to run well:

```
[sholden@opal17 holdenweb-com]$ ./scripts/backup.sh
./scripts/backup.sh: line 54: cd: /home/sholden/backups: No such file or directory
backup: /home/sholden/backups/holdenweb-com/20260822T214120Z
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

  dumping postgres ...
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

    database.pgc  10813 bytes
  app-data.tar.gz  1036570 bytes
  secrets.env, env, config.tar.gz
  rowcounts.txt    4 tables

backup complete: /home/sholden/backups/holdenweb-com/20260822T214120Z
1.1M	/home/sholden/backups/holdenweb-com/20260822T214120Z
```
Here are the relevant directory listings.
```
Last login: Sat Aug 22 21:05:32 2026 from 90.200.204.190
[sholden@opal17 ~]$ ls -ld /home/sholden/backups/holdenweb-com/20260822T214120Z
drwx------. 2 sholden sholden 158 Aug 22 21:41 /home/sholden/backups/holdenweb-com/20260822T214120Z
[sholden@opal17 ~]$ ls -al /home/sholden/backups/holdenweb-com/20260822T214120Z
total 1056
drwx------. 2 sholden sholden     158 Aug 22 21:41 .
drwx------. 3 sholden sholden      30 Aug 22 21:41 ..
-rw-------. 1 sholden sholden 1036570 Aug 22 21:41 app-data.tar.gz
-rw-------. 1 sholden sholden    2956 Aug 22 21:41 config.tar.gz
-rw-------. 1 sholden sholden   10813 Aug 22 21:41 database.pgc
-rw-------. 1 sholden sholden    4972 Aug 22 21:41 env
-rw-------. 1 sholden sholden     923 Aug 22 21:41 manifest.txt
-rw-------. 1 sholden sholden    1060 Aug 22 21:41 plan.json
-rw-------. 1 sholden sholden      62 Aug 22 21:41 rowcounts.txt
-rw-------. 1 sholden sholden    3128 Aug 22 21:41 secrets.env
```

**0.3 — Record the host as it is**, so the rebuild can be compared to it.

```bash
python3 scripts/configure-host.py --check
podman compose ps
curl -s localhost:<WEB_HOST_PORT>/healthz
```

*Expect:* `--check` writes nothing and reports which values are still the
example's, and whether this host can run containers.

`☐` `✎` The system appears to be in a viable state:
```
[sholden@opal17 holdenweb-com]$ python3 scripts/configure-host.py --check
checking .env and secrets.env in /home/sholden/apps/third-alma/holdenweb-com

  unchanged from the example, which is usually fine: COMPOSE_FILE, GUNICORN_WORKERS, HOST_DATA_DIR, HOST_LOG_DIR, POSTGRES_BIND_ADDR, POSTGRES_HOST_PORT, SITE_NAME, WEB_BIND_ADDR
  no credential is still at its example value

nothing to report.
```
---

## Part 1 — the control panel  *(human, and nothing in git knows it)*

**1.1** In Opalstack, create the application (or confirm the existing one) and
**write down the port it allocates**: 15055

**1.2** Confirm the domain binding — which hostname is proxied to that port:
os.holdenweb.com

*These two numbers are the only inputs the rest of the document cannot derive.*

`☐` `✎` Super. Fingers crossed.

---

## Part 2 — clone, and configure the host

**2.1**

```bash
git clone git@github.com:holdenweb/holdenweb-com.git holdenweb.com
cd holdenweb.com
```

[sholden@opal17 os]$ git clone git@github.com:holdenweb/holdenweb-com.git holdenweb.com
Cloning into 'holdenweb.com'...
load pubkey "/home/sholden/.ssh/id_rsa": Invalid key length
Enter passphrase for key '/home/sholden/.ssh/id_rsa':
Enter passphrase for key '/home/sholden/.ssh/id_rsa_personal_2016':
remote: Enumerating objects: 1222, done.
remote: Counting objects: 100% (1222/1222), done.
remote: Compressing objects: 100% (557/557), done.
remote: Total 1222 (delta 551), reused 1203 (delta 532), pack-reused 0 (from 0)
Receiving objects: 100% (1222/1222), 5.31 MiB | 7.47 MiB/s, done.
Resolving deltas: 100% (551/551), done.
[sholden@opal17 os]$ ls -al holdenweb.com/
total 248
drwxr-xr-x. 13 sholden sholden   4096 Aug 23 08:15 .
drwxr-xr-x+  3 sholden sholden     35 Aug 23 08:14 ..
drwxr-xr-x.  3 sholden sholden     92 Aug 23 08:15 alembic
-rw-r--r--.  1 sholden sholden   5100 Aug 23 08:15 alembic.ini
-rw-r--r--.  1 sholden sholden   3718 Aug 23 08:15 compose.mongodb.yaml
-rw-r--r--.  1 sholden sholden   5792 Aug 23 08:15 compose.postgres.yaml
-rw-r--r--.  1 sholden sholden   7600 Aug 23 08:15 compose.yaml
drwxr-xr-x.  2 sholden sholden    128 Aug 23 08:15 config
drwxr-xr-x.  2 sholden sholden     36 Aug 23 08:15 container
-rw-r--r--.  1 sholden sholden   4150 Aug 23 08:15 Containerfile
drwxr-xr-x.  2 sholden sholden     43 Aug 23 08:15 db-init
-rw-r--r--.  1 sholden sholden   3838 Aug 23 08:15 dev.env.example
-rw-r--r--.  1 sholden sholden   2815 Aug 23 08:15 .dockerignore
-rw-r--r--.  1 sholden sholden   4972 Aug 23 08:15 .env.example
drwxr-xr-x.  7 sholden sholden    191 Aug 23 08:15 .git
drwxr-xr-x.  3 sholden sholden     31 Aug 23 08:15 .github
-rw-r--r--.  1 sholden sholden   2956 Aug 23 08:15 .gitignore
-rw-r--r--.  1 sholden sholden     92 Aug 23 08:15 .justfile
drwxr-xr-x.  2 sholden sholden     43 Aug 23 08:15 mongodb-init
-rw-r--r--.  1 sholden sholden  25789 Aug 23 08:15 operations.md
drwxr-xr-x.  2 sholden sholden     32 Aug 23 08:15 ops
-rw-r--r--.  1 sholden sholden   8131 Aug 23 08:15 PROJECT-BRIEF.md
-rw-r--r--.  1 sholden sholden   2899 Aug 23 08:15 pyproject.toml
-rw-r--r--.  1 sholden sholden   4982 Aug 23 08:15 README.md
drwxr-xr-x.  2 sholden sholden    177 Aug 23 08:15 scripts
-rw-r--r--.  1 sholden sholden   3000 Aug 23 08:15 secrets.env.example
drwxr-xr-x.  3 sholden sholden     31 Aug 23 08:15 src
-rw-r--r--.  1 sholden sholden   5794 Aug 23 08:15 substrate.json
drwxr-xr-x.  3 sholden sholden    144 Aug 23 08:15 tests
-rw-r--r--.  1 sholden sholden 122884 Aug 23 08:15 uv.lock

*Expect:* `config/`, `src/` and `alembic/` present — those are in git, and git
is their backup. No `.env`, no `secrets.env`, no `hostdata/`.

`☐` `✎` Note that this directory can live anywhere. I chose to put it in the app's home directory, but as you observe these are the only things than need to be asserted. As expected.

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

`☐` `✎` That seemed to go all right:
```
[sholden@opal17 holdenweb.com]$ python3 scripts/configure-host.py --port 15055
wrote .env and secrets.env (0600) for 'holdenweb.com'
  port          15055 on 127.0.0.1
  database      holdenweb_com, application role holdenweb_com_app
  SELinux       not enforcing
  secrets       generated; none printed here, and none of them lab values

  still the example's value, and needs changing:
    MAIL_PASSWORD (secrets.env)

  unchanged from the example, which is usually fine: POSTGRES_BIND_ADDR, POSTGRES_HOST_PORT

next: ./scripts/prepare-host-dirs.sh && ./scripts/up.sh
```
I thought we needed to enfore SELinux, but clearly I'm wrong.

---

## Part 3 — restore the content and the database

**3.1 — Get the backup onto this host.** From 0.2, or the latest under
`~/backups/holdenweb-com/`.

`☐` `✎` Backup is available at /home/sholden/backups/holdenweb-com/20260822T214120Z

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

`☐` `✎` I chose the real restore, as the database still exists. Maybe we need to consider partial restore procedures? But I'm quite happy to overwrite the existing database to test procedure.

**3.3 — Restore the app data**, before starting anything.

```bash
./scripts/prepare-host-dirs.sh
tar -xzf <backup>/app-data.tar.gz -C ./hostdata
```

*Expect:* `hostdata/apps/pages/` holding roughly 1.0 MB — the site's content.
`qrcode/` and `pp_pdf/` are empty, correctly: both declare themselves stateless.

`☐` `✎` Seemed unremarkable.
```
[sholden@opal17 holdenweb.com]$ install -m 600 /home/sholden/backups/holdenweb-com/20260822T214120Z/secrets.env secrets.env
[sholden@opal17 holdenweb.com]$ ./scripts/prepare-host-dirs.sh
ready: ./hostdata/apps
ready: ./hostlogs/apps
ready: ./hostdata/postgres
ready: ./hostlogs/postgres
ownership set for the containers' unprivileged uids
[sholden@opal17 holdenweb.com]$ tar -xzf  /home/sholden/backups/holdenweb-com/20260822T214120Z/app-data.tar.gz  -C ./hostdata
```

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

`☐` `✎` Again, apparently unexceptional.
```
[sholden@opal17 holdenweb.com]$ ./scripts/up.sh
building from 18007cc
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

Sending build context to Docker daemon  530.6kB
[1/2] STEP 1/10: FROM docker.io/library/python:3.12-slim AS builder
[1/2] STEP 2/10: ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     UV_COMPILE_BYTECODE=1     UV_LINK_MODE=copy
--> Using cache 185147cdcf890c66206f22e9121cb7c6d41bb1782fa039011f9eb7c66e4abd9f
--> 185147cdcf89
[1/2] STEP 3/10: COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv
--> Using cache 6e55e04a9cb0cfa4b3d1fc89f5c64cd06e1b872762614cf553f98009bc00c4e3
--> 6e55e04a9cb0
[1/2] STEP 4/10: RUN apt-get update  && apt-get install --yes --no-install-recommends git  && rm -rf /var/lib/apt/lists/*
--> Using cache 3a1c72176e799a21064672d1ef450b208de91941b5abafb1d4db451ec8a616c8
--> 3a1c72176e79
[1/2] STEP 5/10: WORKDIR /app
--> Using cache 6250469ff80e3dd2e4aebe9b6103441544cab4b08f52228bd7b8cb52fbf17d9c
--> 6250469ff80e
[1/2] STEP 6/10: COPY pyproject.toml uv.lock ./
--> Using cache f04f8e23a55329e577cd2fa640387430b3a09746202815f6dd0407220e21cad5
--> f04f8e23a553
[1/2] STEP 7/10: RUN uv sync --frozen --no-install-project --no-dev
--> Using cache 490ae9b322e598d8d83dbd2414ed432985de134aa11617c4b2d5367a9024bdbb
--> 490ae9b322e5
[1/2] STEP 8/10: COPY src/ ./src/
--> Using cache 4accd8b3351fa127f0070dc75f5233b22fb50f071caeb669a95b799df090e76b
--> 4accd8b3351f
[1/2] STEP 9/10: COPY README.md ./
--> Using cache 58982e1f97b93f8e3e2886745a4a70c56f912d93b2a0269907c3b6a5eb1bf1f6
--> 58982e1f97b9
[1/2] STEP 10/10: RUN uv sync --frozen --no-dev
--> Using cache 30169948c34616cf1bdefd8aa7ea497256e8c64d66f0b8220746d17161352fdd
--> 30169948c346
[2/2] STEP 1/17: FROM docker.io/library/python:3.12-slim
[2/2] STEP 2/17: ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1
--> Using cache a1c6ddac5bc2aab917635be9d93bcbf9b72c331d31e69e4da559b06c5af44dd7
--> a1c6ddac5bc2
[2/2] STEP 3/17: WORKDIR /app
--> Using cache 0068c523b773379760c76672c13fbdc09861916196278770c911de3b0660b078
--> 0068c523b773
[2/2] STEP 4/17: COPY --from=builder /app/.venv ./.venv
--> Using cache 12b84d08ed08e5a85b22094a074acc233e612e7f6c1082d7d75cb8265d7bd6f1
--> 12b84d08ed08
[2/2] STEP 5/17: COPY src/ ./src/
--> Using cache 08acd61a4029c59af0bf37664015893a0bafb22a7a57b0e96f9f89068c2fd9c6
--> 08acd61a4029
[2/2] STEP 6/17: COPY alembic.ini ./
--> Using cache 1838c62f95cd5ddf3c7cb67ed9896e1ffaa7c817aa805e96605956c7aaabd168
--> 1838c62f95cd
[2/2] STEP 7/17: COPY alembic/ ./alembic/
--> Using cache d4f9274b385fb9b4ca51c07a4c0bfd9ad3590a1119e94cfc1c47d7d0bc04b2e4
--> d4f9274b385f
[2/2] STEP 8/17: COPY container/healthcheck.py ./healthcheck.py
--> Using cache 024caeef10cfd67e2d4b87d072a1eb963b9f5bab2432d79017234c18468e1d65
--> 024caeef10cf
[2/2] STEP 9/17: ENV PATH="/app/.venv/bin:${PATH}"
--> Using cache 575e4033ada866c654001544d17daee0115aff1a6cac7a4d9192cbb3e58d13a5
--> 575e4033ada8
[2/2] STEP 10/17: ARG GIT_SHA=unknown
--> Using cache 3cd9e639d1ec8b28500b07c45db6f8967c607fabbf13c83b9df1b2a93a17e9c3
--> 3cd9e639d1ec
[2/2] STEP 11/17: ENV PODPACK_BUILD_COMMIT=${GIT_SHA}
--> Using cache a5541b34c1084a8deb1d92aec4803ff4c7da6dcf30d46aa1ee1a719be4858e4c
--> a5541b34c108
[2/2] STEP 12/17: RUN groupadd --gid 10001 app  && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app
--> Using cache 8a29ac43cd297205d34c5339c3ec2836e8fddb4e62f3473446128e658e0d1e51
--> 8a29ac43cd29
[2/2] STEP 13/17: ENV HOME=/home/app
--> Using cache 2529e844340158ed304f7d6ef315b95cf8edcee6cb2a367b2a7826c067c8c184
--> 2529e8443401
[2/2] STEP 14/17: USER 10001:10001
--> Using cache d705a5459001692ee554b8308f1db9bbb59297e7d5fa66776b9ac9892d65704a
--> d705a5459001
[2/2] STEP 15/17: EXPOSE 8000
--> Using cache cf435b2df4fe31ed7837c6eed302a5fe17218685729e686b49d14d5b7ff467ac
--> cf435b2df4fe
[2/2] STEP 16/17: CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --access-logfile - 'holdenweb:create_app()'"]
--> Using cache d565492c328162c1137c744855d533fd755a7d87a04c135098e1de5482f04d1c
--> d565492c3281
[2/2] STEP 17/17: LABEL "com.docker.compose.image.builder"="classic"
--> Using cache ac0793a69359f08f345bf083914d8e77daa018ea510d805b219c9f27217388ae
[2/2] COMMIT localhost/holdenweb.com-web:latest
--> ac0793a69359
Successfully tagged localhost/holdenweb.com-web:latest
Successfully tagged localhost/holdenweb-com-web:latest
ac0793a69359f08f345bf083914d8e77daa018ea510d805b219c9f27217388ae
Successfully built ac0793a69359
Successfully tagged localhost/holdenweb.com-web:latest
Sending build context to Docker daemon  530.6kB
[1/2] STEP 1/10: FROM docker.io/library/python:3.12-slim AS builder
[1/2] STEP 2/10: ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     UV_COMPILE_BYTECODE=1     UV_LINK_MODE=copy
--> Using cache 185147cdcf890c66206f22e9121cb7c6d41bb1782fa039011f9eb7c66e4abd9f
--> 185147cdcf89
[1/2] STEP 3/10: COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv
--> Using cache 6e55e04a9cb0cfa4b3d1fc89f5c64cd06e1b872762614cf553f98009bc00c4e3
--> 6e55e04a9cb0
[1/2] STEP 4/10: RUN apt-get update  && apt-get install --yes --no-install-recommends git  && rm -rf /var/lib/apt/lists/*
--> Using cache 3a1c72176e799a21064672d1ef450b208de91941b5abafb1d4db451ec8a616c8
--> 3a1c72176e79
[1/2] STEP 5/10: WORKDIR /app
--> Using cache 6250469ff80e3dd2e4aebe9b6103441544cab4b08f52228bd7b8cb52fbf17d9c
--> 6250469ff80e
[1/2] STEP 6/10: COPY pyproject.toml uv.lock ./
--> Using cache f04f8e23a55329e577cd2fa640387430b3a09746202815f6dd0407220e21cad5
--> f04f8e23a553
[1/2] STEP 7/10: RUN uv sync --frozen --no-install-project --no-dev
--> Using cache 490ae9b322e598d8d83dbd2414ed432985de134aa11617c4b2d5367a9024bdbb
--> 490ae9b322e5
[1/2] STEP 8/10: COPY src/ ./src/
--> Using cache 4accd8b3351fa127f0070dc75f5233b22fb50f071caeb669a95b799df090e76b
--> 4accd8b3351f
[1/2] STEP 9/10: COPY README.md ./
--> Using cache 58982e1f97b93f8e3e2886745a4a70c56f912d93b2a0269907c3b6a5eb1bf1f6
--> 58982e1f97b9
[1/2] STEP 10/10: RUN uv sync --frozen --no-dev
--> Using cache 30169948c34616cf1bdefd8aa7ea497256e8c64d66f0b8220746d17161352fdd
--> 30169948c346
[2/2] STEP 1/17: FROM docker.io/library/python:3.12-slim
[2/2] STEP 2/17: ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1
--> Using cache a1c6ddac5bc2aab917635be9d93bcbf9b72c331d31e69e4da559b06c5af44dd7
--> a1c6ddac5bc2
[2/2] STEP 3/17: WORKDIR /app
--> Using cache 0068c523b773379760c76672c13fbdc09861916196278770c911de3b0660b078
--> 0068c523b773
[2/2] STEP 4/17: COPY --from=builder /app/.venv ./.venv
--> Using cache 12b84d08ed08e5a85b22094a074acc233e612e7f6c1082d7d75cb8265d7bd6f1
--> 12b84d08ed08
[2/2] STEP 5/17: COPY src/ ./src/
--> Using cache 08acd61a4029c59af0bf37664015893a0bafb22a7a57b0e96f9f89068c2fd9c6
--> 08acd61a4029
[2/2] STEP 6/17: COPY alembic.ini ./
--> Using cache 1838c62f95cd5ddf3c7cb67ed9896e1ffaa7c817aa805e96605956c7aaabd168
--> 1838c62f95cd
[2/2] STEP 7/17: COPY alembic/ ./alembic/
--> Using cache d4f9274b385fb9b4ca51c07a4c0bfd9ad3590a1119e94cfc1c47d7d0bc04b2e4
--> d4f9274b385f
[2/2] STEP 8/17: COPY container/healthcheck.py ./healthcheck.py
--> Using cache 024caeef10cfd67e2d4b87d072a1eb963b9f5bab2432d79017234c18468e1d65
--> 024caeef10cf
[2/2] STEP 9/17: ENV PATH="/app/.venv/bin:${PATH}"
--> Using cache 575e4033ada866c654001544d17daee0115aff1a6cac7a4d9192cbb3e58d13a5
--> 575e4033ada8
[2/2] STEP 10/17: ARG GIT_SHA=unknown
--> Using cache 3cd9e639d1ec8b28500b07c45db6f8967c607fabbf13c83b9df1b2a93a17e9c3
--> 3cd9e639d1ec
[2/2] STEP 11/17: ENV PODPACK_BUILD_COMMIT=${GIT_SHA}
--> Using cache a5541b34c1084a8deb1d92aec4803ff4c7da6dcf30d46aa1ee1a719be4858e4c
--> a5541b34c108
[2/2] STEP 12/17: RUN groupadd --gid 10001 app  && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app
--> Using cache 8a29ac43cd297205d34c5339c3ec2836e8fddb4e62f3473446128e658e0d1e51
--> 8a29ac43cd29
[2/2] STEP 13/17: ENV HOME=/home/app
--> Using cache 2529e844340158ed304f7d6ef315b95cf8edcee6cb2a367b2a7826c067c8c184
--> 2529e8443401
[2/2] STEP 14/17: USER 10001:10001
--> Using cache d705a5459001692ee554b8308f1db9bbb59297e7d5fa66776b9ac9892d65704a
--> d705a5459001
[2/2] STEP 15/17: EXPOSE 8000
--> Using cache cf435b2df4fe31ed7837c6eed302a5fe17218685729e686b49d14d5b7ff467ac
--> cf435b2df4fe
[2/2] STEP 16/17: CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --access-logfile - 'holdenweb:create_app()'"]
--> Using cache d565492c328162c1137c744855d533fd755a7d87a04c135098e1de5482f04d1c
--> d565492c3281
[2/2] STEP 17/17: LABEL "com.docker.compose.image.builder"="classic"
--> Using cache ac0793a69359f08f345bf083914d8e77daa018ea510d805b219c9f27217388ae
[2/2] COMMIT localhost/holdenweb.com-web:latest
--> ac0793a69359
Successfully tagged localhost/holdenweb.com-web:latest
Successfully tagged localhost/holdenweb-com-web:latest
ac0793a69359f08f345bf083914d8e77daa018ea510d805b219c9f27217388ae
Successfully built ac0793a69359
Successfully tagged localhost/holdenweb.com-web:latest
[+] up 7/7
 ✔ Image localhost/holdenweb.com-web:latest Built                                                 12.2s
 ✔ Network holdenwebcom_default             Created                                                0.0s
 ✔ Container holdenwebcom-init-postgres-1   Exited                                                 0.8s
 ✔ Container holdenwebcom-init-storage-1    Exited                                                 7.7s
 ✔ Container holdenwebcom-postgres-1        Healthy                                                7.7s
 ✔ Container holdenwebcom-migrate-1         Exited                                                 8.7s
 ✔ Container holdenwebcom-web-1             Started                                                8.9s
 ```


**4.2 — Load the data over that schema.** The dump carries the same schema, so
drop and recreate first.

**Set this first, so the placeholder cannot collide with the shell:**

```bash
BACKUP=/home/sholden/backups/holdenweb-com/<the timestamp>
```

> Writing `< <backup>/database.pgc` literally is a bash syntax error — `< <` is
> process substitution. Use the variable.

```bash
podman compose exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

Now **the branch from 3.2, and getting it wrong breaks the site in a way that
looks like a migration bug**:

| If at 3.2 you… | Restore with |
| --- | --- |
| **restored `secrets.env`** (real restore) | `pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error` |
| **kept the generated one** (rehearsal) | `pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error` |

```bash
podman compose exec -T postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error' < "$BACKUP/database.pgc"
podman compose restart web
```

> **Why `--no-owner` is wrong on the real-restore path.** `db-init` creates
> `SCHEMA app AUTHORIZATION <app role>`, and every table lives in it.
> `--no-owner` makes the restoring role — the *admin* — own that schema instead,
> while the application still connects as the app role with `search_path = app`.
> The site then fails at `migrate` with a permission error that reads like a
> broken migration. Observed, 23 August 2026.

*Expect:* silence from `pg_restore`. Any error, and `--exit-on-error` stops it.

`☐` `✎` Seems to have gone OK.
```
[sholden@opal17 holdenweb.com]$ podman compose exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

[sholden@opal17 holdenweb.com]$ podman compose exec -T postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < <backup>/database.pgc
-bash: syntax error near unexpected token `<'
[sholden@opal17 holdenweb.com]$ podman compose exec -T postgres sh -c   'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < /home/sholden/backups/holdenweb-com/20260822T214120Z/database.pgc
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

[sholden@opal17 holdenweb.com]$ podman compose restart web
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

[+] restart 0/1
 ⠴ Container holdenwebcom-web-1 Restarting                                                         0.4s
 ```


**4.3 — Check the row counts against the backup's own record.**

```bash
cat <backup>/rowcounts.txt
```

`☐` `✎` OK
```
[sholden@opal17 holdenweb.com]$ cat /home/sholden/backups/holdenweb-com/20260822T214120Z/rowcounts.txt
app|alembic_version|1
app|role|1
app|roles_users|1
app|user|2
```

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

`☐` `✎` Well, migrate failed :-(.
```
[sholden@opal17 holdenweb.com]$ podman compose up -d --force-recreate web
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

[+] up 5/5
 ✔ Container holdenwebcom-postgres-1      Healthy                                                  3.0s
 ✘ Container holdenwebcom-migrate-1       Error service "migrate" didn't complete successfu...     3.8s
 ✔ Container holdenwebcom-web-1           Recreated                                                0.7s
 ✔ Container holdenwebcom-init-postgres-1 Exited                                                   0.7s
 ✔ Container holdenwebcom-init-storage-1  Exited                                                   2.0s
service "migrate" didn't complete successfully: exit 1
Error: executing /home/sholden/bin/docker-compose up -d --force-recreate web: exit status 1
```

Attempts to access the site receive a 502 response from Opalstack's nginx proxy, so I can't tell you what status says that way.

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

`☐` `✎` In fact the real password was already in place. Again when trying to bring the web service up the migrate service failed.
```
[sholden@opal17 holdenweb.com]$ podman compose up -d web
>>>> Executing external compose provider "/home/sholden/bin/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

[+] up 4/4
 ✔ Container holdenwebcom-postgres-1      Healthy                                                  1.9s
 ✔ Container holdenwebcom-init-postgres-1 Exited                                                   0.7s
 ✔ Container holdenwebcom-init-storage-1  Exited                                                   1.9s
 ✘ Container holdenwebcom-migrate-1       Error service "migrate" didn't complete successfull...   1.7s
service "migrate" didn't complete successfully: exit 1
Error: executing /home/sholden/bin/docker-compose up -d web: exit status 1
```
 I can't run mailcheck because that service is down.
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
