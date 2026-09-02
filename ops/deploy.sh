#!/usr/bin/env bash
# Deliver a committed revision to a target and rebuild it there. Development is
# on the laptop; this is the one command that moves a revision outward --
# staging first, production only after it has been seen working on staging.
#
# Why push-and-rebuild rather than rsync: the target is a real git checkout at
# the pushed commit, so scripts/up.sh stamps GIT_SHA into the image and
# /_status can answer "is the container running this commit?" (ADR-0017). An
# rsync'd tree has no HEAD and stamps `unknown`, losing exactly that.
#
# A target is a git remote whose scp-style URL (opal17:apps/os/site) is the
# single source of truth for where it lives: the rebuild command is derived
# from it, so there is no second copy of the host or path to drift. Set each
# target up once per host -- see ops/DEPLOY.md.
set -euo pipefail

# target -> URL polled after the rebuild to confirm it came up. Production is
# blank until its Opalstack app and domain exist; fill it in then.
health_url() {
  case "$1" in
    staging)    echo "https://os.holdenweb.com/healthz" ;;
    production) echo "" ;;
    *)          echo "" ;;
  esac
}

usage() { echo "usage: ${0##*/} [--dry-run] [--allow-dirty] <staging|production>" >&2; exit 2; }

dry=0; allow_dirty=0; target=""
for a in "$@"; do
  case "$a" in
    --dry-run)     dry=1 ;;
    --allow-dirty) allow_dirty=1 ;;
    staging|production) target="$a" ;;
    *) usage ;;
  esac
done
[ -n "$target" ] || usage

url="$(git remote get-url "$target" 2>/dev/null)" || {
  echo "no git remote named '$target'. Add it (see ops/DEPLOY.md):" >&2
  echo "  git remote add $target opal17:apps/<app>/site" >&2
  exit 1
}
case "$url" in
  *:*) sshhost="${url%%:*}"; path="${url#*:}" ;;
  *)   echo "remote '$target' is not an scp-style host:path URL: $url" >&2; exit 1 ;;
esac

# Deploy committed code. --untracked-files=no so a stray untracked file (a local
# README.pdf, a scratch note) does not count: it is never pushed. What must not
# ship silently is an uncommitted change to a *tracked* file, since only commits
# are pushed. up.sh's -dirty stamp is the accident safety net; this is the
# intent. Skipped for a dry run, which only ever prints.
if [ "$dry" -eq 0 ] && [ "$allow_dirty" -eq 0 ] \
   && [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "uncommitted changes to tracked files; commit first, or pass --allow-dirty." >&2
  exit 1
fi

sha="$(git rev-parse --short HEAD)"
# Warn, do not refuse: staging exists precisely to try unpublished work, but
# shipping something origin has never seen is worth saying out loud.
if ! git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
  echo "note: HEAD ($sha) is not on origin/main -- deploying unpublished code." >&2
fi

# $path expands here (local var); ~ stays literal in double quotes and expands
# on the host, so the login home is resolved there rather than on the laptop.
remote_cmd="cd ~/$path && ./scripts/up.sh"
hu="$(health_url "$target")"

if [ "$dry" -eq 1 ]; then
  echo "+ git push $target HEAD:main"
  echo "+ ssh $sshhost \"$remote_cmd\""
  [ -n "$hu" ] && echo "+ HEALTH_URL=$hu ${0%/*}/poll-health.sh"
  exit 0
fi

echo "==> deploying $sha to $target ($sshhost:$path)"
git push "$target" HEAD:main
ssh "$sshhost" "$remote_cmd"

if [ -n "$hu" ]; then
  echo "==> verifying $hu"
  HEALTH_URL="$hu" "${0%/*}/poll-health.sh"
  echo "==> $target is healthy at $sha"
else
  echo "==> no health URL configured for $target; verify it by hand." >&2
fi
