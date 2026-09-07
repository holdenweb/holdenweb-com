#!/usr/bin/env bash
# Push a content tree from here to a target's running site, in one step.
#
# The content apps -- pages, pybooks, blog -- read their content from the host's
# data directory, and ops/refresh-content.sh mirrors a staged directory into one
# of those trees. That runs *on the host*, against container-owned files (hence
# its `podman unshare`), so refreshing a remote deployment otherwise means
# copying the source up by hand and then ssh-ing in to run it. This is that pair
# as one command, run from wherever the content is built.
#
# The content sibling of ops/deploy.sh, and it borrows deploy.sh's idea of a
# target: the same git remote, whose scp-style URL (opal17:apps/os/site) names
# both the host and the site path, so neither is written down twice.
#
#     ops/push-content.sh staging ~/Projects/Python/orpy/python-classes \
#         --app pybooks --tree html-pages --mirror
#     ops/push-content.sh staging ~/Projects/Python/sitescraper/build \
#         --app blog --tree export --mirror
#
# --app / --tree name the destination exactly as they do for refresh-content.sh:
# the tree at hostdata/apps/<app>/<tree>. --mirror passes straight through and
# means the same there -- remove whatever the source does not have -- and is off
# by default in both places, because an incomplete source with --mirror deletes a
# visitor's content; ask for it when you mean it. --dry-run prints the plan and
# changes nothing.
set -euo pipefail

usage() {
  echo "usage: ${0##*/} [--dry-run] <staging|production> <local-dir> --app APP --tree TREE [--mirror]" >&2
  exit 2
}

dry=0; mirror=0; target=""; src=""; app=""; tree=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) dry=1 ;;
    --mirror)  mirror=1 ;;
    --app)     app="${2:?--app needs a value}"; shift ;;
    --tree)    tree="${2:?--tree needs a value}"; shift ;;
    --*)       echo "unknown option: $1" >&2; usage ;;
    *)         if   [ -z "$target" ]; then target="$1"
               elif [ -z "$src" ];    then src="$1"
               else echo "unexpected argument: $1" >&2; usage; fi ;;
  esac
  shift
done
[ -n "$target" ] && [ -n "$src" ] && [ -n "$app" ] && [ -n "$tree" ] || usage
case "$target" in
  staging|production) ;;
  *) echo "target must be 'staging' or 'production', not '$target'" >&2; usage ;;
esac
[ -d "$src" ] || { echo "no such source directory: $src" >&2; exit 1; }

# The target names the host and the site path, exactly as ops/deploy.sh reads
# them -- one source of truth, no second copy to drift.
url="$(git remote get-url "$target" 2>/dev/null)" || {
  echo "no git remote named '$target' (see ops/DEPLOY.md):" >&2
  echo "  git remote add $target opal17:apps/<app>/site" >&2
  exit 1
}
case "$url" in
  *:*) sshhost="${url%%:*}"; path="${url#*:}" ;;
  *)   echo "remote '$target' is not an scp-style host:path URL: $url" >&2; exit 1 ;;
esac

mirror_arg=""; [ "$mirror" -eq 1 ] && mirror_arg="--mirror"

if [ "$dry" -eq 1 ]; then
  echo "+ rsync -a --delete '$src/' '$sshhost:<scratch>/'"
  echo "+ ssh $sshhost \"cd ~/$path && APP=$app TREE=$tree ./ops/refresh-content.sh <scratch> $mirror_arg\""
  echo "+ ssh $sshhost 'rm -rf <scratch>'   # always, on the way out"
  exit 0
fi

echo "==> pushing $src -> $target ($sshhost:$path), tree $app/$tree${mirror_arg:+ (mirror)}"

# A fresh scratch directory on the host, removed whatever happens next. The
# content is public, so /tmp is fine; the copy is transient because
# refresh-content.sh is what installs it, under the container's ownership.
scratch="$(ssh "$sshhost" 'mktemp -d "${TMPDIR:-/tmp}/push-content.XXXXXXXX"')"
cleanup() { ssh "$sshhost" "rm -rf -- $scratch" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# --delete so the scratch is exactly the source: a stale file left here would
# otherwise be mirrored into the live tree. The trailing slash copies contents.
rsync -a --delete "$src/" "$sshhost:$scratch/"

# refresh-content.sh cd's to the site root itself; the scratch path is absolute,
# so that cd leaves it alone. It owns the container-subuid dance.
ssh "$sshhost" "cd ~/$path && APP=$app TREE=$tree ./ops/refresh-content.sh $scratch $mirror_arg"

echo "==> done; $app/$tree on $target refreshed from $src"
