#!/bin/bash
# Prove a backup can be restored, by restoring it.
#
# A backup regime is a claim about the future, and the only evidence for it is
# a restore that has actually happened. This script produces that evidence on
# demand and cheaply: it restores the dump into a *scratch database* beside the
# live one, counts what came back, and drops the scratch database again. The
# site is untouched throughout and never stops serving.
#
#   ops/restore-rehearsal.sh              # the most recent backup
#   ops/restore-rehearsal.sh <directory>  # a named one
#
# Where to run it: preferably on the laptop, against the lab stack, using a
# backup copied down from the host. That rehearses the restore *and* the
# transfer, which is the half of a restore that fails at three in the morning.
# Running it on the production host is supported and safe -- a separate
# database, dropped afterwards -- but it proves less.
#
# Exits non-zero on any failure, so a scheduled run is worth scheduling.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

# shellcheck disable=SC1091
set -a; . ./.env; set +a

root="${BACKUP_ROOT:-${HOME}/backups/${SITE_NAME}}"
if [[ $# -ge 1 ]]; then
    backup="$1"
else
    backup="${root}/$(ls -1 "$root" 2>/dev/null | sort | tail -1)"
fi

[[ -f "${backup}/database.pgc" ]] || { echo "no database.pgc in ${backup}" >&2; exit 1; }
echo "rehearsing: ${backup}"

# $$ rather than a timestamp: two rehearsals in the same second would collide,
# and the failure would look like a corrupt backup rather than a name clash.
scratch="rehearsal_$$"

cleanup() {
    podman compose exec -T postgres \
        sh -c "dropdb -U \"\$POSTGRES_USER\" --if-exists ${scratch}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

podman compose exec -T postgres sh -c "createdb -U \"\$POSTGRES_USER\" ${scratch}" 2>/dev/null

# --exit-on-error is the point of the exercise. Without it pg_restore reports
# every failure and still exits 0, so a rehearsal would pass on an archive that
# restored nothing.
if ! podman compose exec -T postgres \
        sh -c "pg_restore -U \"\$POSTGRES_USER\" -d ${scratch} --exit-on-error" \
        < "${backup}/database.pgc" 2>&1 | grep -v 'external compose provider'; then
    echo "REHEARSAL FAILED: pg_restore reported an error" >&2
    exit 1
fi

# What actually came back. Counted from the restored database's own catalogue
# rather than from a list written here, so a table added to the site in future
# appears without this script being edited.
echo "restored:"
podman compose exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d ${scratch} -At -F' ' -c \"
    select schemaname||'.'||relname, n_live_tup
    from pg_stat_user_tables order by relname\"" 2>/dev/null \
  | sed 's/^/  /'

rows="$(podman compose exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d ${scratch} -At -c \"
    select coalesce(sum(n_live_tup), 0) from pg_stat_user_tables\"" 2>/dev/null | tr -d ' \r')"
if [[ "${rows:-0}" -eq 0 ]]; then
    echo "REHEARSAL FAILED: the restored database is empty" >&2
    exit 1
fi

# The other half of the backup. A tar that cannot be listed cannot be
# extracted, and the content is the part git does not hold.
files="$(tar -tzf "${backup}/app-data.tar.gz" | wc -l | tr -d ' ')"
[[ "$files" -gt 0 ]] || { echo "REHEARSAL FAILED: app-data.tar.gz is unreadable or empty" >&2; exit 1; }

# secrets.env is the third leg, and the one whose absence is discovered latest
# -- a restore without it produces a site that starts, serves, and cannot
# verify a single stored password. Presence and non-emptiness only: the
# contents are never read, printed or compared.
#
# Whether those values are still the shipped lab examples is a *configuration*
# question, not a backup one, and podpack already answers it properly:
# `python3 scripts/configure-host.py --check`. Asking it here as well would be
# a second, worse copy of a facility that exists.
[[ -s "${backup}/secrets.env" ]] || { echo "REHEARSAL FAILED: no secrets.env in the backup" >&2; exit 1; }

echo "rehearsal PASSED: ${rows} rows, ${files} data files, secrets present"
