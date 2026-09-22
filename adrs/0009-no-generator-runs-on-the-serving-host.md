# HW-0009: No generator runs on the serving host

**Status:** Accepted

**Date:** 2026-09-22

## Context

The host half of a content refresh cannot be avoided. `hostdata/apps` is owned
by container subuids, so the copy has to happen inside `podman unshare` on the
box itself; a laptop cannot write those files over ssh as itself. Before
`ops/push-content.sh` existed, that meant copying the source up by hand and then
ssh-ing in to run the refresh — two steps, and the second easy to forget.

The obvious way to remove the awkwardness is to move the work to the host: check
out the three generator repositories there and run their builders where the
files have to land. That was the fork.

## Decision

The laptop builds; the host only receives. No content generator runs on the
serving host, and no generator repository is checked out there.

`ops/push-content.sh` is a single laptop-side command that performs both halves:
rsync the built directory into a scratch directory on the host, run
`ops/refresh-content.sh` there against the named `--app` and `--tree`, and
remove the scratch directory on the way out, whatever happened. It names its
target the way `ops/deploy.sh` does (HW-0001).

Each generator's output directory is configuration rather than a path baked into
a script: `ORPY_BUILD`, `SITESCRAPER_BUILD`, `NOTEBOOKS_BUILD`, defaulted in
`.justfile` to where each builder writes today.

`ops/refresh-content.sh` is not a host-only script. The same file serves this
checkout's own development instance, which is what `just <area> local` runs.

## Consequences

**The host needs no Python toolchain for content**, no checkouts of the three
generator repositories, no webhook and no CI. What arrives is HTML.

**Content is transient on the way in.** The scratch copy is removed whatever
happens next, and `refresh-content.sh` sets modes and ownership
deterministically rather than preserving whatever umask produced the files on
another machine — "whatever umask produced it there has no business deciding
what a web server can read here."

**Publication requires that one laptop.** There is no path to update content
from anywhere else, which is a real single point of failure for the *ability to
publish*, though not for the site itself.

**The reproducibility of three areas rests on source trees this repository only
names by default path.** `~/Projects/Python/orpy` and
`~/Projects/Python/sitescraper` are not part of this estate's backups and are
not referenced anywhere except as a `just` variable's default.

**Content can only go where a deploy can go.** The target is a git remote, so
production will error until its remote exists — the same behaviour as a code
deploy, which is the point of sharing the mechanism, but it does mean there is
no such thing as a content-only destination.

## Alternatives considered

**Run the builders on the host from checkouts there.** Rejected: it puts a
second copy of three projects' source on the serving box, with a toolchain to
maintain and update, to save an rsync.

**A CI pipeline that publishes content.** Rejected as out of keeping — nothing
else about this site is automated that way, and it would couple three unrelated
repositories to this one's deployment.

**rsync plus a hand-run ssh**, which is what this replaced: "Refreshing a
content tree on a remote deployment meant copying the source up by hand and then
ssh-ing in." The two-step form is not wrong, it is just the version that gets
half-done.
