#!/bin/bash
# Rebuild this site on this host from a backup, end to end.
#
# The mechanical core is scripts/restore.sh, which the substrate ships and
# which does the hard part -- ordering the unpack, the stores and the stack so
# that ownership and the application role come out right. This wraps it with
# the three things it cannot do for itself: clearing whatever is already here,
# reconciling the per-host values it overwrites, and checking the result
# against the address the world actually uses.
#
# Run it from the directory that will *contain* the checkout, not from inside
# one. The script itself may live in any checkout -- it works on the directory
# you are standing in, not the one it was read from:
#
#     cd ~/apps/os
#     export WEB_PORT=15055 SITE_HOST=os.holdenweb.com
#     export BACKUP=~/backups/holdenweb-com/20260823T170934Z
#     export SITE_DIR=holdenweb-com
#     /path/to/any/checkout/ops/rebuild.sh --check     # preflight, changes nothing
#     /path/to/any/checkout/ops/rebuild.sh
#
# Name SITE_DIR after the compose project the site will end up driving, which
# is whatever SITE_NAME the backup carries -- `holdenweb-com` for this site.
# Directory and project then agree, and `podman compose` from that directory
# does what it looks like it does. They diverged once and cost an hour.
#
# `--check` validates every precondition and changes nothing, which is worth
# doing first at any hour and essential at three in the morning.
#
# It restores. It does not create a site from nothing -- for that the backup is
# irrelevant and `configure-host.py` is the entry point; see ops/rebuild.md.
set -euo pipefail

SITE_REPO="${SITE_REPO:-git@github.com:holdenweb/holdenweb-com.git}"
SITE_DIR="${SITE_DIR:-holdenweb-staging}"
PROXY_HOPS="${PROXY_HOPS:-1}"

check_only=no
[[ "${1:-}" == "--check" ]] && check_only=yes

# How long a rebuild takes is the one figure a 3am document most needs and the
# one nothing has ever recorded: the checklist stamps each part with `date` and
# this script, which replaced it, quietly dropped that. Three rehearsals have
# now produced no number at all.
started="$(date -u +%s)"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
note() { printf '   %s\n' "$*"; }
die()  { printf '\nFAILED: %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Preconditions. Every one of these has cost a rehearsal.
# ---------------------------------------------------------------------------
say "checking preconditions"

: "${WEB_PORT:?set it to the port the control panel allocated}"
: "${SITE_HOST:?set it to the PUBLIC hostname, not the name of this machine}"
: "${BACKUP:?set it to the backup directory to restore from}"

# The machine's own name resolves, answers, and 404s everything, which reads as
# a broken site rather than a wrong variable. Rehearsal 2 lost thirteen tests
# to it.
[[ "$SITE_HOST" == "$(hostname -s)" || "$SITE_HOST" == "$(hostname)" ]] && \
    die "SITE_HOST is this machine's own name. It wants the public hostname."

[[ -d "$BACKUP" ]] || die "no such backup directory: $BACKUP"
for required in manifest.txt plan.json app-data.tar.gz env secrets.env; do
    [[ -s "$BACKUP/$required" ]] || die "backup is incomplete: $required missing or empty"
done
note "backup: $BACKUP"
note "        $(grep -m1 '^taken:' "$BACKUP/manifest.txt")"
note "        $(grep -m1 '^alembic revision:' "$BACKUP/manifest.txt")"

# A backup taken from a *seeded* site looks almost identical to a real one --
# same size to within a few bytes, one row different, and verify-backup.sh
# calls both VERIFIED. Saying the row count out loud is the cheapest defence
# there is until podpack records which it was.
#
# Backlog #22 is fixed in podpack 0.9.0b4: verify-backup.sh now compares
# each table against the previous backup in the same root and says when a
# count has fallen. This stays because it fires earlier -- before the restore,
# on the backup you are about to trust -- and because it asks a question only
# a person can answer.
if [[ -s "$BACKUP/rowcounts.txt" ]]; then
    rows="$(awk -F'|' '{s += $3} END {print s + 0}' "$BACKUP/rowcounts.txt")"
    tables="$(wc -l < "$BACKUP/rowcounts.txt" | tr -d ' ')"
    note "        ${rows} rows across ${tables} tables -- is that the site you remember?"
fi

[[ -w . ]] || die "cannot write to $(pwd)"
[[ "$(basename "$(pwd)")" == "$SITE_DIR" ]] && \
    die "run this from the directory that will contain $SITE_DIR, not from inside it"

# restore.sh installs the backup's .env -- and with it SITE_NAME, the compose
# project name -- whenever the checkout has none of its own. That is exactly this
# script's case, because it clones fresh a few lines below. So every compose
# command afterwards still acts on the *backup's* project, which is another
# deployment's if one is running.
#
# Backlog #19 is fixed in podpack 0.9.0b4, and this guard is NOT obsolete.
# The fix makes restore.sh keep an .env that already exists; a fresh clone has
# none, so the rebuild path is the one case where the old behaviour still
# applies. Do not remove this on the strength of the item being struck.
running="$(podman ps --format '{{.Names}}' 2>/dev/null || true)"
# Naming the stop command matters: from this directory there is no compose file,
# so `podman compose down` cannot work and the reader is left hunting. Observed.
[[ -z "$running" ]] || die "containers are running, and a restore adopts the backup's compose project:
$(printf '  %s\n' $running)
  Stop them by name -- from here there is no compose file, so compose cannot:
      podman stop $(echo $running | tr '\n' ' ')"

note "target:  $(pwd)/$SITE_DIR"
note "public:  https://$SITE_HOST -> 127.0.0.1:$WEB_PORT"

if [[ "$check_only" == yes ]]; then
    say "preconditions pass; nothing was changed"
    exit 0
fi

# ---------------------------------------------------------------------------
# 1. Clear the ground.
#
# `podman unshare` because prepare-host-dirs.sh gave hostdata and hostlogs to
# the containers' uids, which are subuids out here. Without it `rm -rf` fails
# on every file; run from the wrong directory it succeeds having removed
# nothing, and the failure then appears one command later and blames something
# else. Both seen in rehearsal 3.
# ---------------------------------------------------------------------------
if [[ -e "$SITE_DIR" ]]; then
    say "removing the previous $SITE_DIR"
    podman unshare rm -rf "$SITE_DIR"
    [[ -e "$SITE_DIR" ]] && die "could not remove $SITE_DIR"
fi

say "cloning"
git clone --quiet "$SITE_REPO" "$SITE_DIR"
cd "$SITE_DIR"
note "at $(git rev-parse --short HEAD)"

# The fix that makes a restore work on Linux arrived in podpack 0.9.0b3 and
# reaches a site through `podpack substrate upgrade`. A checkout without it
# fails on every file *after* replacing .env and secrets.env, so it is worth
# one grep rather than one wasted rebuild.
grep -q inside_namespace scripts/restore.sh || die \
    "this checkout's scripts/restore.sh predates the namespace fix (podpack 0.9.0b3).
  Push the substrate upgrade, or the unpack will fail on every file."

# ---------------------------------------------------------------------------
# 2. The restore itself, which prompts twice and is the point of all this.
# ---------------------------------------------------------------------------
say "restoring"
log="$(mktemp)"
rc=0
./scripts/restore.sh "$BACKUP" 2>&1 | tee "$log" || rc="${PIPESTATUS[0]}"

# It ends by curling ${WEB_HOST_PORT} from the .env it just restored, which is
# the *old* host's port. Usually that simply works -- the site really is on that
# port at that moment, because the restored .env is what brought it up -- and
# the reconciliation below then moves it. Measured on 2026-08-24: `site healthz:
# 200 (http://127.0.0.1:3427/)`, the old port, passing.
#
# It fails only where that port is unavailable or something else holds it, and
# then the data is correctly in place and only the check is wrong. That single
# case is forgiven; anything else is not, and the distinction is worth drawing
# rather than swallowing.
#
# Backlog #19's fix does not remove this either, for the reason given at the
# nothing-running guard above: it keeps an existing .env, and a fresh clone has
# none. Restoring into a checkout that already has its own .env now polls this
# host's port and passes, so this branch simply stops firing there.
if [[ "$rc" -ne 0 ]]; then
    if grep -q 'the site is not healthy' "$log" && ! grep -q 'MISMATCH' "$log"; then
        note "restore.sh reported the site unhealthy on the *old* port; expected here."
    else
        rm -f "$log"
        die "restore.sh failed for a reason this script will not paper over. Read its output above."
    fi
fi
rm -f "$log"

# ---------------------------------------------------------------------------
# 3. Reconcile the values that belong to this host rather than to the backup.
# ---------------------------------------------------------------------------
say "reconciling .env for this host"
was_port="$(grep -m1 '^WEB_HOST_PORT=' .env | cut -d= -f2-)"
sed -i.bak "s/^WEB_HOST_PORT=.*/WEB_HOST_PORT=${WEB_PORT}/" .env && rm -f .env.bak
note "WEB_HOST_PORT ${was_port:-unset} -> ${WEB_PORT}"

# Never delivered by an upgrade: its documentation lives in env.example, which
# is a seeded file podpack never touches again. Without it every _external URL
# comes out http://, first visible in a password-reset mail.
if grep -q '^PODPACK_PROXY_HOPS=' .env; then
    sed -i.bak "s/^PODPACK_PROXY_HOPS=.*/PODPACK_PROXY_HOPS=${PROXY_HOPS}/" .env && rm -f .env.bak
else
    printf 'PODPACK_PROXY_HOPS=%s\n' "$PROXY_HOPS" >> .env
fi
note "PODPACK_PROXY_HOPS=${PROXY_HOPS}"

# ---------------------------------------------------------------------------
# 4. Up, on this host's port.
# ---------------------------------------------------------------------------
say "starting"
./scripts/up.sh

say "checking"
code=000
for _ in $(seq 30); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${WEB_PORT}/healthz" || true)"
    [[ "$code" == "200" ]] && break
    sleep 2
done
[[ "$code" == "200" ]] || die "healthz on 127.0.0.1:${WEB_PORT} answered ${code}, not 200"
note "healthz 200 on 127.0.0.1:${WEB_PORT}"

hops="$(podman compose exec -T web printenv PODPACK_PROXY_HOPS 2>/dev/null | tr -d '\r' || true)"
[[ "$hops" == "$PROXY_HOPS" ]] || die "the container reports PODPACK_PROXY_HOPS='${hops}', not ${PROXY_HOPS}"
note "container reads PODPACK_PROXY_HOPS=${hops}"

public="$(curl -s -o /dev/null -w '%{http_code}' "https://${SITE_HOST}/healthz" || true)"
note "https://${SITE_HOST}/healthz -> ${public}"
[[ "$public" == "200" ]] || die "the public address does not reach this site. The proxy mapping is wrong, or DNS has not caught up."

elapsed=$(( $(date -u +%s) - started ))
say "rebuilt in $((elapsed / 60))m $((elapsed % 60))s, and answering on https://${SITE_HOST}"

# Which compose project this checkout now drives, asked of podman rather than
# derived. restore.sh brings SITE_NAME back from the backup, so a directory
# called `-staging` routinely owns a project named for production -- and
# compose normalises the name besides, stripping dots and keeping dashes. Two
# transformations between the directory you are standing in and the containers
# you get, neither of them visible. Rehearsal 4 lost time to exactly this:
# `podman compose exec web` answered "service web is not running" about a
# container that was, because it was run one directory away.
project="$(grep -m1 '^SITE_NAME=' .env | cut -d= -f2-)"
web_container="$(podman ps --format '{{.Names}}' | grep -- '-web-1$' | head -1)"
# Only if podman has renamed the container in some way this script does not
# know about; the health check above has already proved one is serving.
web_container="${web_container:-${project}-web-1}"

cat <<EOF

   This checkout drives compose project '${project}', and podman is calling its
   web container '${web_container}'. Run compose commands from here:

        cd $(pwd)

   From anywhere else compose reads a different .env, resolves a different
   project, and reports "service web is not running" about containers that are.
   To sidestep that entirely, name the container:

        podman exec ${web_container} flask --app holdenweb roles add <email> admin

   Three things this script cannot check, and one of them is the point:

     1. Sign in as yourself. Accounts came back with secrets.env, so your
        existing credentials work -- if they do not, the restore took the
        wrong secrets.env.
     2. Request a password reset and read the mail. The link must begin
        https://. That is the fault this whole exercise started with.
     3. From your laptop, against this host:
            uv run pytest tests/integration --base-url https://${SITE_HOST}

   Then prove the regime here, and mind where it writes:
        ./scripts/backup.sh && ./scripts/verify-backup.sh
EOF
