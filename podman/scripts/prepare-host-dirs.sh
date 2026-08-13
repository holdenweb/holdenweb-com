#!/bin/bash
# Create the host directories the suite bind-mounts, and copy .env into place
# on first run. Safe to re-run.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "created .env from .env.example -- review it before going further"
fi

# shellcheck disable=SC1091
set -a; . ./.env; set +a

for dir in \
    "${HOST_DATA_DIR}/mongo/data" \
    "${HOST_DATA_DIR}/mongo/configdb" \
    "${HOST_DATA_DIR}/uploads" \
    "${HOST_LOG_DIR}/mongo" \
    "${HOST_LOG_DIR}/web"
do
    mkdir -p "$dir"
    echo "ready: $dir"
done

# The containers run unprivileged, as uid 999 (mongod, fixed by the upstream
# image) and uid 10001 (the app, fixed by our Containerfile). Under rootless
# podman those uids land inside your user namespace rather than on real host
# uids, so the directories only need to be writable by the mapped user -- which
# `podman unshare chown` arranges. On Linux this is required; on macOS the
# virtiofs mount already presents everything as writable, and the command is a
# harmless no-op if it fails.
if [[ "$(uname -s)" == "Linux" ]]; then
    podman unshare chown -R 999:999 "${HOST_DATA_DIR}/mongo" "${HOST_LOG_DIR}/mongo"
    podman unshare chown -R 10001:10001 "${HOST_DATA_DIR}/uploads" "${HOST_LOG_DIR}/web"
    echo "ownership set for the containers' unprivileged uids"
fi
