#!/bin/bash
# Take a complete, restorable backup of this site.
#
# Three things have to come back for a restore to be a restore, and they live
# in three different places, which is the whole reason this script exists:
#
#   1. the database          -- in the container's PostgreSQL
#   2. the app data          -- $HOST_DATA_DIR/apps, the *live* copy of the
#                               content; an app ships its data but seeds it
#                               once, so the packaged copy is not this one
#   3. the site's identity   -- secrets.env, which must come back verbatim or
#                               every stored password becomes unverifiable
#
# Config and code are not here: they are in git, which is a better backup than
# this one. `.env` is copied anyway, because it is the fastest way to see how
# the host that took the backup was wired.
#
# The dump is verified before this script claims success. An unreadable backup
# discovered during a restore is worse than no backup, because it was believed.
#
# Runs from anywhere; writes to $BACKUP_ROOT (default ~/backups/<SITE_NAME>),
# deliberately OUTSIDE the repository. The archive contains secrets.env, and a
# directory of credentials inside a working tree is one careless `git add`
# away from being published.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

# shellcheck disable=SC1091
set -a; . ./.env; set +a

keep="${BACKUP_KEEP:-14}"
root="${BACKUP_ROOT:-${HOME}/backups/${SITE_NAME}}"
stamp="$(date -u +%Y-%m-%dT%H%M%SZ)"
dest="${root}/${stamp}"

# Fail before writing anything rather than leave a directory holding a
# zero-byte dump that looks like a backup in a listing.
if ! podman compose ps --status running --services 2>/dev/null | grep -qx postgres; then
    echo "backup: the postgres service is not running -- nothing to dump" >&2
    exit 1
fi

mkdir -p "$dest"
chmod 700 "$root" "$dest"
echo "backup: ${dest}"

# The container's own environment supplies the credentials, so they never
# appear in this script's process arguments, where `ps` would show them.
# Ownership is preserved (no --no-owner): a restore lands in a stack whose
# db-init has already created the same role from the same secrets.env.
podman compose exec -T postgres \
    sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
    > "${dest}/database.pgc"

# Verification, not decoration. pg_restore --list parses the whole archive, so
# it fails on a truncated or corrupt one; and an archive can be perfectly valid
# while containing no rows at all, which is what a dump of the wrong database
# looks like.
podman compose exec -T postgres pg_restore --list < "${dest}/database.pgc" \
    > "${dest}/database.toc" 2>/dev/null
tables="$(grep -c 'TABLE DATA' "${dest}/database.toc" || true)"
if [[ "$tables" -eq 0 ]]; then
    echo "backup: the dump contains no table data -- refusing to keep it" >&2
    rm -rf "$dest"
    exit 1
fi
echo "  database.pgc   $(wc -c < "${dest}/database.pgc" | tr -d ' ') bytes, ${tables} tables"

# App data, from the host side: it is a bind mount, so no container is needed
# and none has to be running.
tar -czf "${dest}/app-data.tar.gz" -C "${HOST_DATA_DIR}" apps
echo "  app-data.tar.gz $(wc -c < "${dest}/app-data.tar.gz" | tr -d ' ') bytes"

# 0600 from the moment it exists, not after a chmod on the next line.
install -m 600 secrets.env "${dest}/secrets.env"
install -m 600 .env "${dest}/env"
echo "  secrets.env, env"

# What produced this, in case the answer matters years from now.
{
    echo "site        ${SITE_NAME}"
    echo "taken       ${stamp}"
    echo "host        $(hostname)"
    echo "commit      $(git rev-parse HEAD 2>/dev/null || echo unknown)"
    echo "image       $(podman compose images web --format json 2>/dev/null | head -c 400 || true)"
} > "${dest}/manifest.txt"

# Prune oldest-first, and only ever inside $root. `ls -1 | sort` orders these
# names correctly because the stamp is ISO-8601 and fixed-width.
#
# A while-read loop rather than `mapfile`: macOS ships bash 3.2, where mapfile
# does not exist and the script would die on its last line having already
# taken a perfectly good backup.
total="$(ls -1 "$root" 2>/dev/null | wc -l | tr -d ' ')"
if (( total > keep )); then
    ls -1 "$root" | sort | head -n $(( total - keep )) | while read -r old; do
        rm -rf "${root:?}/${old}"
        echo "  pruned ${old}"
    done
fi

echo "backup: complete, $(ls -1 "$root" | wc -l | tr -d ' ') kept (limit ${keep})"
