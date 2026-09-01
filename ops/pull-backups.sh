#!/usr/bin/env bash
# Pull the host's backups to the laptop, so a backup does not live only on the
# machine it protects. operations.md section 4 is the argument. This is the
# off-machine copy, and it is only ever as current as the last time the laptop
# ran it -- so schedule it, and let it be noisy on failure.
#
# Suggested laptop schedule (after the host's 03:17 backup and 04:23 verify):
#   30 5 * * * /Users/sholden/sites/holdenweb.com/ops/pull-backups.sh >> ~/backups/pull.log 2>&1
#
# Source is the host's BACKUP_ROOT (~/backups/$SITE_NAME on the host); the
# destination mirrors it here. --delete so a backup rotated away on the host is
# rotated away here too, rather than the copy growing without limit.
#
# The tree contains secrets.env in clear (ADR-0035). The destination is created
# 0700 and rsync -a preserves the source's modes; keep it on a disk you would
# lose in the same sentence as this laptop, or encrypt it.
#
# Defaults target staging; production is one variable:
#   SITE_NAME=hw-holdenweb-com ./ops/pull-backups.sh
set -euo pipefail

SITE_NAME="${SITE_NAME:-os-holdenweb-com}"
HOST="${BACKUP_HOST:-opal17}"
SRC="${BACKUP_SRC:-backups/$SITE_NAME/}"              # relative to the host login home
DEST="${BACKUP_DEST:-$HOME/backups/$SITE_NAME-remote/}"

mkdir -p "$DEST"
chmod 700 "$DEST"
rsync -a --delete "$HOST:$SRC" "$DEST"
echo "$(date -u +%FT%TZ): pulled $HOST:$SRC -> $DEST"
