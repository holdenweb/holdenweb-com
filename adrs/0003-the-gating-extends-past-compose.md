# HW-0003: The gating extends past compose, to the laptop and to the public URL

**Status:** Accepted

**Date:** 2026-09-22

## Context

podpack's substrate already gates the middle of a deployment. ADR-0016 requires
the Compose v2 provider precisely so that the ordering conditions hold: storage
ownership is fixed first, `migrate` waits on a healthy `postgres`, and `web`
waits on `migrate` having completed. Get the provider wrong and those conditions
are silently ignored, which is why the framework insists.

What the framework does not cover is either end. Before the push, an uncommitted
change to a tracked file will never reach the host, and a commit `origin` has
never seen may be about to. After the rebuild, a container can come up and not
serve: nginx answers 200 from its own error page with the container gone, so
from outside even a successful status code is not evidence. Each of those could
be handled by proceeding and reporting afterwards, or by stopping before the
next step.

The substrate ships seven scripts and none of them is a deploy script or a
health poll, so both ends are this site's to own.

## Decision

Both ends refuse rather than degrade, and the compose ordering in the middle is
podpack's (ADR-0016), inherited rather than re-decided here.

**Before anything leaves the laptop**, `ops/deploy.sh` refuses when
`git status --porcelain --untracked-files=no` is non-empty. Untracked files do
not count, because they are never pushed: a scratch `README.pdf` used to block a
deploy whose tracked tree was clean.

**After the rebuild**, `ops/deploy.sh` runs `ops/poll-health.sh` against the
target's public URL and treats a non-zero exit as "this deploy did not come up".
That check asserts the body carries `"status":"ok"`; `curl -f` alone is not
trusted, because nginx's own error page is a 200. Both are used — `curl -fsS`
first, then the body test.

**Three exceptions, each deliberate.** A commit that is not on `origin/main`
warns and continues, because staging exists precisely to try unpublished work.
`--allow-dirty` lets the operator override the first gate outright. `--dry-run`
prints the plan and touches nothing.

## Consequences

**A green deploy means the public address answered with `"status":"ok"` in the
body**, not merely that something returned 200.

**Production is not gated, and that is the gap this record must not paper
over.** `health_url()` returns an empty string for `production`, so
`ops/deploy.sh` falls through to "no health URL configured for $target; verify
it by hand" — proceed-and-report, on the target that will matter most. It is a
recorded to-do rather than an oversight: `ops/DEPLOY.md`'s "Adding production"
ends with filling that URL in, and the backlog carries it. Until then the
decision above is true of staging and aspirational for production.

**Nothing automatic proves each app still does its job.** `ops/deploy.sh` does
not run the integration suite, and neither does `ops/rebuild.sh` — its pytest
line sits inside a `cat <<EOF` block under the heading "Three things this script
cannot check, and one of them is the point". The suite is a human obligation on
both paths, booked per-deployment in `operations.md`. The failure that leaves
open is on the record: "the QR code app answered 200 for weeks while
contributing no navigation at all."

**The body rule is not applied everywhere yet.** `ops/rebuild.sh`'s own public
check uses `curl -s -o /dev/null -w '%{http_code}'` and accepts a bare 200 —
exactly the case `ops/poll-health.sh` exists to defeat. The rule as decided
covers `deploy.sh`; the disaster-recovery path has not been brought into line.

**The chain stops at the deploy.** "A check at deploy time is not a monitor. It
answers whether this deploy came up, not whether the site is up now, and between
deploys nothing asks." That sentence is why HW-0004 exists.

A note on provenance, since a record that implies more foresight than there was
is worth less: the three guards were designed together on 2026-09-01, in the
commit that introduced `ops/deploy.sh`. The phrase "every step is a gate that
refuses rather than degrading" was written three weeks later, on 2026-09-22,
while drawing the deployment diagram. The principle was named retrospectively;
the gates were not.

## Alternatives considered

**Counting untracked files as a dirty tree.** The original behaviour, removed
because it blocked deploys over files that could not possibly ship.

**Refusing an off-origin commit as well as an uncommitted one.** Rejected: it
would break the only thing staging is for.

**Trusting `curl -f` alone after the rebuild.** Rejected because nginx's error
page is a 200, so the status code cannot distinguish "serving" from "the proxy
is apologising".

**Reporting failures instead of refusing** — logging that the tree was dirty, or
that the site did not answer, and continuing. Rejected as the general policy
because every one of these failures is silent at the moment it matters and
expensive later; the cost of stopping is one command re-run.
