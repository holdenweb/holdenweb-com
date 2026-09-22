# HW-0032: A gap in the framework is fixed in the framework, and the floor is the receipt

**Status:** Accepted

**Date:** 2026-09-22

## Context

This site is podpack's proving ground, so it is where podpack's gaps are found:
by needing something the framework does not have, in the middle of doing
something else.

Every obvious response is wrong in a way that shows up later. Forking podpack
ends the point of having a framework. Committing a path source breaks every
environment but one laptop (HW-0018). Patching this site's copy of a managed
file creates drift the next substrate sync reconciles away (HW-0020). Waiting
for a release before doing the work leaves the site broken in the meantime.

## Decision

Write the smallest local version that works now, file the gap against the
framework's repository in this site's single backlog (HW-0024), and then wait
for a release — at which point the local version is deleted and the floor moves
to the release that carries the fix (HW-0019).

**The floor is the receipt.** It is the only artefact that records "this
deployment depends on that fix", and it is why the cycle can be closed without
anybody remembering.

## Consequences

**Two worked examples, both closed, with their durations:**

`/config`'s operator guard was nine hand-rolled lines here. podpack took the
decorator as `@operator_required`, released it in 0.9.3, and this site's copy
went the same day — the floor moved with it.

The `unset CDPATH` fix touched six substrate-managed scripts. They were
deliberately *not* patched here — "patching holdenweb's copies directly would
create substrate drift ... and the next sync would reconcile it away" — so the
fix went upstream and arrived five days later with a substrate upgrade.

**The site carries duplicated code for as long as the cycle takes**, and
duplicated code with a known replacement is the kind that gets forgotten. The
backlog item is what stops that, which is why filing it is part of the decision
rather than an afterthought.

**The cycle needs somebody who can release podpack**, which in this estate is
the same person. For any other consumer of podpack, the wait is unbounded and
this record's advice would not hold.

**"Fixed upstream" and "taken here" are separate events** and the backlog
records them separately — a distinction that only exists because the site
installs from an index rather than from a sibling checkout.

**HW-0020 is the exception, and states its own test.** Where podpack's default
has to stay as it is for other sites, the divergence is legitimate and stays
here.

## Alternatives considered

**Fork podpack.** Ends the experiment. The whole claim of the estate is that a
site is a configuration file plus a list of installed apps, and a fork is a site
that has stopped being one.

**Commit a path or git source to get the fix immediately.** Tried and retired
(HW-0018): it breaks the container build, CI and every fresh checkout, to save
hours.

**Patch the managed copy and let the next sync reconcile it.** Rejected for the
CDPATH scripts, and the reasoning is in the backlog: `substrate status --check`
exists precisely to catch a managed file that no longer matches podpack, so
creating drift to save a few days spends a mechanism that is worth more than the
days.

**Wait for the release before doing anything.** Not taken: the site stays broken
meanwhile, and the local version is usually how the right shape of the upstream
fix is discovered.
