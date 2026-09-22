#!/bin/bash
# Refresh one of the `pages` app's content trees from a staged directory.
#
# The problem this exists for is ownership. On Linux, prepare-host-dirs.sh
# hands `hostdata/apps` to the containers' unprivileged uids with
# `podman unshare chown`, and those uids are *subuids* out here -- so the tree
# belongs to something like 1158576 and your own shell cannot write to it:
#
#     $ ls -ld hostdata/apps/pages/html-pages
#     drwxr-xr-x. 3 1158576 1158576 ...
#     $ mkdir python-classes
#     mkdir: cannot create directory 'python-classes': Permission denied
#
# `podman unshare` re-enters that mapping, where the same directory is owned by
# 10001 and you are root. Note that it is `podman unshare` and not util-linux's
# `unshare`, which looks identical, runs without complaint, and does nothing:
# it does not know about podman's subuid mapping, so the files stay unwritable
# and the failure looks like the one you were trying to fix.
#
# macOS needs none of this -- the chown is gated on `uname -s`, so the files
# belong to you already -- and running `podman unshare` there would operate
# inside the podman machine's VM rather than on these files. Hence the same
# `inside_namespace` helper scripts/restore.sh uses, for the same reason.
#
# Usage:
#     ops/refresh-content.sh <staged-directory> [--mirror]
#
# Default is a MERGE: files are added and overwritten, and anything already
# here that the source does not have is left alone. `--mirror` removes the
# destination first, so a file deleted at the source disappears here too.
#
# The merge default is deliberate. scripts/restore.sh learned this the hard
# way: an unpack that only ever adds leaves files deleted on purpose sitting
# beside the new ones, producing a state that never existed anywhere. That is
# recoverable; deleting a visitor's content because a staging directory was
# incomplete is not. Ask for --mirror when you mean it.
#
# No restart is needed. podpack_pages resolves a page by reading the file on
# every request (`content.find_page`), with no index and no cache, so content
# is live the moment it lands.
set -euo pipefail

# CDPATH is exported in this project's shell (.zshrc). With it set, bash echoes
# the directory on a CDPATH-matched `cd`, so the `$(cd ... && pwd)` below would
# capture the path twice and `cd "$here"` would then fail on the doubled value.
# Nothing here wants CDPATH's search behaviour; clear it once.
unset CDPATH

# --- configuration -------------------------------------------------------
APP="${APP:-pages}"
TREE="${TREE:-html-pages}"
APP_UID="${APP_UID:-10001}"          # the Containerfile's unprivileged uid
# -------------------------------------------------------------------------

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

source_dir="${1:-}"
mode="${2:-merge}"

if [[ -z "$source_dir" || ! -d "$source_dir" ]]; then
    echo "usage: ops/refresh-content.sh <staged-directory> [--mirror]" >&2
    [[ -n "$source_dir" ]] && echo "no such directory: ${source_dir}" >&2
    exit 1
fi
[[ "$mode" == "merge" || "$mode" == "--mirror" ]] || {
    echo "second argument, if given, must be --mirror" >&2; exit 1; }

if [[ ! -f .env ]]; then
    echo "no .env here -- run this from a deployed site" >&2
    exit 1
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

# Resolved by python rather than `cd ... && pwd`, which fails open on a path
# that does not exist yet -- the defect backup.sh carried for a week.
resolve() { python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }
target="$(resolve "${HOST_DATA_DIR:?}/apps/${APP:?}/${TREE:?}")"
staged="$(resolve "$source_dir")"

case "${staged}/" in
    "${target}/"*|"$(resolve "${HOST_DATA_DIR}")/"*)
        echo "the staged directory is inside the content tree; stage it elsewhere" >&2
        exit 1 ;;
esac

inside_namespace() {
    if [[ "$(uname -s)" == "Linux" ]]; then podman unshare "$@"; else "$@"; fi
}

echo "app:     ${APP}/${TREE}"
plural() { [[ "$1" == 1 ]] && echo "1 file" || echo "$1 files"; }
echo "from:    ${staged}  ($(plural "$(find "$staged" -type f | wc -l | tr -d ' ')"))"
echo "into:    ${target}  ($(plural "$(inside_namespace find "$target" -type f 2>/dev/null | wc -l | tr -d ' ')"))"
echo "mode:    ${mode/--/}"

if [[ "$mode" == "--mirror" ]]; then
    # The prompt is gated, the removal is not. `push-content.sh` drives this
    # over ssh with no pty, so an ungated `read` gets EOF and aborts a mirror
    # that was already confirmed locally -- and from cron it aborts outright.
    #
    # Gating the whole branch instead is the obvious edit and is wrong: it would
    # skip the `rm -rf` too, so --mirror would quietly behave as a merge, leaving
    # files the source no longer has beside the new ones. That is the state
    # restore.sh's header warns about, and it would look like success.
    if [ -t 0 ]; then
        read -r -p "Mirror REMOVES anything not in the source. Type 'mirror' to go on: " reply
        [[ "$reply" == "mirror" ]] || { echo "aborted"; exit 1; }
    fi
    inside_namespace rm -rf "${target:?}"
fi

inside_namespace mkdir -p "$target"
# Copied inside the namespace, from a staging directory you own: the copy runs
# as root *in that namespace*, so it can write where your shell cannot.
#
# `-R` and not `-a`. `-a` implies `--preserve=all`, which includes xattrs and
# the SELinux context, and opal17 refuses to set those on the destination:
#
#     cp: preserving permissions for '.../python-classes/.': Invalid argument
#
# The copy itself had already succeeded when that fired, but `set -e` then
# aborted before the chown below -- so the files were there and owned by the
# wrong uid, which is the state this script exists to avoid.
#
# Nothing is lost by not preserving. Modes and ownership are set deterministically
# two lines down, which is what you want for content generated on another host:
# whatever umask produced it there has no business deciding what a web server
# can read here. Timestamps are not preserved either; the app does not use them.
inside_namespace cp -R "${staged}/." "${target}/"

# Deterministic, and before the chown: directories 0755, files 0644.
inside_namespace chmod -R "u=rwX,go=rX" "$target"

# Ownership last, and to the app's uid rather than the namespace's root: the
# container runs as 10001, and a tree left owned by namespace-root reads back
# out here as yours, which is the state this script exists to get out of.
if [[ "$(uname -s)" == "Linux" ]]; then
    podman unshare chown -R "${APP_UID}:${APP_UID}" "$target"
fi

echo
echo "now holds $(plural "$(inside_namespace find "$target" -type f | wc -l | tr -d ' ')")"
echo "No restart needed: pages reads each file as it serves it. Check one:"
echo "    curl -sI http://127.0.0.1:${WEB_HOST_PORT}/pages/<name> | head -1"
