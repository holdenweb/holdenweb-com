# Containerised Flask + MongoDB lab

A podman suite running a Flask app and a MongoDB Community Edition server,
arranged so that **no state and no host-specific setting lives inside a
container**. The point is to exercise production-shaped code locally: the same
compose file, images and config files can be promoted to a real host by editing
`.env` alone.

## Quick start

```bash
cd podman && ./scripts/prepare-host-dirs.sh && podman compose up -d --build
```

Then:

```bash
curl -s localhost:8457/ | python3 -m json.tool
```

The index route reports where each piece of its state actually came from — the
config file it read, whether the upload mount is writable, the database it is
connected to, and what it can currently see. That is the whole point of the
demo app: if a mount is wrong, this route says so.

Shut down with `podman compose down`. Host storage survives; see
[Starting over](#starting-over).

## Ports

| Service | Host port | Why not the obvious one |
| --- | --- | --- |
| Flask | `127.0.0.1:8457` | 8456 is the real site's local port, and a `holdenwebcom-web-1` container may already hold it |
| MongoDB | `127.0.0.1:27018` | 27017 is very likely a natively installed `mongod` |

Both are offset by one from the real thing, deliberately: a lab that silently
binds the production port is a lab that will one day be mistaken for
production. Both bind to loopback only, so neither is reachable from the
network. Change them in `.env` if they still clash.

## Where everything lives

| What | Host location | Container location |
| --- | --- | --- |
| MongoDB data | `$HOST_DATA_DIR/mongo/data` | `/data/db` |
| MongoDB internal config | `$HOST_DATA_DIR/mongo/configdb` | `/data/configdb` |
| Uploaded files | `$HOST_DATA_DIR/uploads` | `/var/lib/holdenweb/uploads` |
| MongoDB log | `$HOST_LOG_DIR/mongo/mongod.log` | `/var/log/mongodb` |
| App log | `$HOST_LOG_DIR/web/app.log` | `/var/log/holdenweb` |
| mongod settings | `config/mongod.conf` | `/etc/mongo/mongod.conf` (read-only) |
| App settings | `config/app.toml` | `/etc/holdenweb/app.toml` (read-only) |
| Secrets and wiring | `.env` | environment variables |

`HOST_DATA_DIR` and `HOST_LOG_DIR` default to `./hostdata` and `./hostlogs`
(both gitignored) so the lab is self-contained. On a real host they become
absolute — `/srv/holdenweb/data`, `/var/log/holdenweb` — and nothing else needs
to change.

The split between the last two rows is the one worth internalising:
**non-secret settings that vary per host go in `config/`; secrets go in the
environment.** Config files are version-controllable and reviewable; `.env` is
not committed.

## Changing things

Two loops, depending on what you touched:

```bash
podman compose restart web        # after editing config/app.toml
podman compose restart mongo      # after editing config/mongod.conf
```

```bash
podman compose up -d              # after editing .env (recreates containers)
podman compose up -d --build      # after editing app/ or the Containerfile
```

Editing a mounted config file needs no rebuild and no image change, which is
exactly the behaviour you want on a real host.

## Reading the logs

`mongod` is configured to log to a **file on the host**, matching how it would
be run in production — so `podman logs` shows almost nothing for it:

```bash
tail -f hostlogs/mongo/mongod.log
```

The Flask app logs to both stdout and the host, so either works:

```bash
podman compose logs -f web
tail -f hostlogs/web/app.log
```

## Talking to the database directly

```bash
podman run --rm -it --network host docker.io/library/mongo:8.0 \
    mongosh "mongodb://holdenweb_app:holdenweb-app-password@127.0.0.1:27018/holdenweb"
```

Those are the *application* credentials, which have `readWrite` on one database
and nothing else. The root credentials in `.env` are used exactly once, by the
bootstrap below, and are never given to the app.

## First-run bootstrap

[`mongo-init/01-create-app-user.sh`](mongo-init/01-create-app-user.sh) creates
the least-privileged application user and an index. The MongoDB image runs that
directory **only while the data directory is empty** — and since the data
directory is on the host, that means "the first time you bring the lab up on
this machine", not "every time the container is recreated".

## Starting over

```bash
podman compose down
rm -rf hostdata hostlogs
./scripts/prepare-host-dirs.sh
podman compose up -d
```

Deleting `hostdata/mongo/data` is what re-arms the bootstrap script.

## How the services fit together

`init-storage` → `mongo` (waits for healthy) → `web`.

`init-storage` is a throwaway root container that hands the bind-mounted host
directories to the unprivileged uids the servers actually run as (999 for
`mongod`, 10001 for the app). Without it `mongod` cannot open its logfile on a
host directory it does not own, and crash-loops. It is not a privilege
escalation: under rootless podman that "root" is your own user inside a
namespace, and on macOS the ownership change is namespace-local — the host
keeps its own ownership.

Both servers have healthchecks, so `podman compose up -d` does not return until
Mongo is genuinely accepting authenticated queries.

## Running on Linux

Two differences on a real Linux host:

- **SELinux (RHEL, Fedora, CentOS Stream).** Append `,Z` to the read-write bind
  mounts and `,z` to the read-only shared ones in
  [compose.yaml](compose.yaml) — e.g.
  `${HOST_DATA_DIR}/mongo/data:/data/db:Z`. Without a label, SELinux denies the
  container access. The mount points are commented in the file.
- **Ownership.** `init-storage` handles it, but if you prefer to pre-create the
  directories yourself, `prepare-host-dirs.sh` does the equivalent
  `podman unshare chown` on Linux.

## Compose front-ends

Verified with both:

- `podman compose` — delegates to Docker Compose v2 if installed, which has the
  most complete support for `depends_on` conditions. Recommended.
- `podman-compose` — also works. It names containers with underscores
  (`holdenweb-lab_web_1`) rather than hyphens, so don't mix the two front-ends
  against the same project without taking the stack down first.

## What the demo app is, and is not

[`app/app.py`](app/app.py) is a purpose-built app that exists to prove the
plumbing: it reads host config, writes to Mongo, writes to the host uploads
directory, and reports on all three. It is **not** the real holdenweb
application, which uses Postgres via SQLAlchemy and alembic and has no Mongo
counterpart.

To point this lab at the real application instead, build the `web` service from
the repository root using the pattern in the top-level
[Dockerfile](../Dockerfile) (uv + uwsgi) and give it the environment the real
app expects.

### Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Where each piece of state lives, and whether it is reachable |
| `GET` | `/healthz` | 200 only if Mongo answers a ping; 503 otherwise |
| `GET` | `/notes` | List stored notes, newest first |
| `POST` | `/notes` | `{"text": "..."}` → stores a note in Mongo |
| `POST` | `/uploads/<name>` | Request body → a file in the host uploads directory |

## Proving persistence

The claim worth testing, since it is the whole reason the suite exists:

```bash
curl -sX POST -H 'Content-Type: application/json' -d '{"text":"survives"}' localhost:8457/notes
curl -sX POST --data-binary 'hello' localhost:8457/uploads/probe.txt
podman compose down          # both containers destroyed
podman compose up -d
curl -s localhost:8457/notes # the note is still there
cat hostdata/uploads/probe.txt
```
