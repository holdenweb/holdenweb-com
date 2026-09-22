# HW-0029: Two suites, and CI is advisory

**Status:** Accepted

**Date:** 2026-09-22

## Context

Unit tests prove the code that builds a site is right. They cannot say whether
the thing now serving on a real host is.

That gap is not hypothetical here: podpack's own `/healthz` stays 200 for a
non-fatal app failure by design (ADR-0030), the chrome resolves navigation from
whatever apps actually installed, and "the QR code app answered 200 for weeks
while contributing no navigation at all".

At the same time, this site's revisions reach the host by `git push staging`,
not by `git push origin` (HW-0002). Those are different remotes and, in
practice, different moments. Anything living on the published branch is
therefore downstream of the deployment, not upstream of it.

## Decision

**Two suites, aimed at two different objects.**

`tests/` proves the code. It needs no server, runs in seconds against in-memory
SQLite (HW-0027), and builds the real site from the shipped `config/app.toml`
rather than a parallel copy — so the app list under test is the app list that
deploys. `testpaths = ["tests"]` makes it the default.

`tests/integration/` proves a deployment. It drives a real browser against a
running site and aims itself: `--base-url`, else `$SITE_URL`, else the port and
bind address in the site's own `.env`, and it prints which site it is testing in
the pytest header "where it cannot be missed". Without a target it skips rather
than failing.

**CI is an advisory check, not a gate.** It runs on pushes to `main` and on pull
requests, with dummy secrets and no service; the gate that can actually stop a
bad revision is `ops/deploy.sh`'s, on the target (HW-0003).

## Consequences

**A green CI run says the code is sound, not that the site is up** — and
because CI watches `origin/main` while deploys go to `staging`, a revision can
be serving before CI has ever seen it. `deploy.sh` warns about exactly that and
does not refuse, "because staging exists precisely to try unpublished work".

**Nothing runs the integration suite automatically.** It is a human obligation
on both the deploy path and the disaster-recovery path: `ops/rebuild.sh` prints
the command under the heading "Three things this script cannot check, and one of
them is the point". So the suite that proves the deployment is the one nothing
schedules.

**The integration suite needs a browser installed** (`playwright install
chromium`), once per machine, which is why it cannot be part of the fast loop
and why CI does not run it.

**Building the site from the shipped config makes the unit suite sensitive to
configuration**, which is deliberate: an app list that cannot boot should fail
in seconds on a laptop, not at a container start on a host.

## Alternatives considered

**One suite, with the slow tests marked and skipped by default.** Rejected: the
two prove different things and are aimed at different objects — one at a tree of
source, one at a running deployment — and the aiming machinery has no business
in the fast suite.

**Make CI the gate**, by refusing to deploy a commit `origin` has not seen.
Rejected: it breaks the only thing staging is for. The cost is accepted with the
warning.

**Run the integration suite from `deploy.sh`.** Not taken. It would need a
browser on the deploying machine and would turn a deploy into a several-minute
operation; the deploy-time check is `ops/poll-health.sh` instead (HW-0004), and
the gap between those two is stated rather than closed.
