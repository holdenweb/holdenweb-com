#!/usr/bin/env bash
# Deliver a committed revision to a target and rebuild it there. Development is
# on the laptop; this is the one command that moves a revision outward --
# staging first, production only after it has been seen working on staging.
#
# The host FETCHES the commit it is told to run. This pushes to GitHub on a
# per-target deploy ref, then over ssh has the host fetch from its own origin,
# check that exact commit out, and rebuild (HW-0034).
#
# It used to push straight into a live worktree on the host, which worked and
# had a hole in it: `receive.denyCurrentBranch=updateInstead` only updates the
# tree when the pushed ref is the checked-out branch. With HEAD detached -- which
# scripts/restore.sh actively tells an operator to do -- the push was accepted,
# the tree was never touched, up.sh rebuilt the OLD commit, and poll-health.sh
# passed, because it asks for "status":"ok" and never looks at the commit. A
# green deploy that deployed nothing. Hence both halves of what follows: the
# fetch-and-checkout, and the build-commit assertion at the end.
#
# Still a git checkout on the host, because that is what scripts/up.sh stamps
# GIT_SHA from -- an rsync'd tree has no HEAD and stamps `unknown` (ADR-0017).
# `git rev-parse HEAD` does not care whether HEAD is attached, so a detached
# deploy checkout stamps exactly as honestly as a pushed branch did.
#
# A target is still a git remote whose scp-style URL (opal17:apps/os/site) says
# where it lives, so there is no second copy of the host or path to drift
# (HW-0001) -- nothing is pushed to it any more, but ops/push-content.sh reads
# it the same way. The GitHub URL is deliberately NOT written down here: the
# host fetches from its own origin, set once when its checkout is made. Set each
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
# The full sha for the checkout: an abbreviation can become ambiguous in a
# repository that has grown since it was written down.
full_sha="$(git rev-parse HEAD)"
# Warn, do not refuse: staging exists precisely to try unpublished work, and it
# still can -- the deploy ref below is not `main`, so a commit reaches staging
# without being merged. Worth saying out loud all the same.
if ! git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
  echo "note: HEAD ($sha) is not on origin/main -- deploying unpublished code." >&2
fi

# One ref per target, written only by this script. --force-with-lease because
# deploying an earlier commit rewinds it, while a plain --force would also
# overwrite a ref somebody else had moved.
deploy_ref="refs/heads/deploy/$target"

# $path and $full_sha expand here (local vars); ~ stays literal in double quotes
# and expands on the host, so the login home is resolved there rather than on
# the laptop.
#
# `checkout --detach`, not `checkout -f` or `reset --hard`: it REFUSES when host
# edits or untracked files would be overwritten, instead of discarding them
# silently. A deploy that stops is recoverable; one that quietly throws away a
# config change somebody made on the host is not.
remote_cmd="cd ~/$path && git fetch --prune origin && git checkout --detach $full_sha && ./scripts/up.sh"

# What the container is actually running, asked of the container. Not /_status,
# which is operator-only (HW-0016) and would need an authenticated request; this
# reads the same value, which the Containerfile sets from ARG GIT_SHA.
stamp_cmd="cd ~/$path && podman compose exec -T web printenv PODPACK_BUILD_COMMIT"
hu="$(health_url "$target")"

if [ "$dry" -eq 1 ]; then
  echo "+ git push --force-with-lease origin HEAD:$deploy_ref"
  echo "+ ssh $sshhost \"$remote_cmd\""
  [ -n "$hu" ] && echo "+ HEALTH_URL=$hu ${0%/*}/poll-health.sh"
  echo "+ ssh $sshhost \"$stamp_cmd\"   # must report $sha"
  exit 0
fi

echo "==> deploying $sha to $target ($sshhost:$path)"
git push --force-with-lease origin "HEAD:$deploy_ref"
ssh "$sshhost" "$remote_cmd"

if [ -n "$hu" ]; then
  echo "==> verifying $hu"
  HEALTH_URL="$hu" "${0%/*}/poll-health.sh"
else
  echo "==> no health URL configured for $target; verify it by hand." >&2
fi

# Healthy is not the same as "running what you just deployed". The old transport
# could report a green deploy having changed nothing at all, and nothing here
# would have noticed, because the health check asks the site how it feels rather
# than which commit it is. This asks the commit.
#
# `|| true` so a container that cannot be reached produces the mismatch message
# below rather than an opaque ssh exit code.
echo "==> confirming the running commit"
running="$(ssh "$sshhost" "$stamp_cmd" 2>/dev/null | tr -d '\r' || true)"
if [ "$running" != "$sha" ]; then
  echo "deployed $sha but the container reports '${running:-nothing}'." >&2
  echo "The rebuild did not take. Look at the host before deploying again:" >&2
  echo "  ssh $sshhost 'cd ~/$path && git log -1 --oneline && git status --short'" >&2
  exit 1
fi
echo "==> $target is healthy, and running $sha"
