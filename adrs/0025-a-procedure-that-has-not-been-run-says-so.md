# HW-0025: A claim that rests on having run something says whether it was run

**Status:** Accepted

**Date:** 2026-09-22

## Context

`operations.md` was written in one pass on 2026-08-19, covering what podpack
leaves to the site: backups, restores, moving hosts, rotating credentials, going
out of service. Much of it describes a production host that does not exist, so
some of it could not be executed while being written.

A runbook of plausible commands is worse than no runbook: it is trusted at the
moment its reader is least able to check it. The writing proved the point on
itself, discovering that the health endpoint is `/healthz` and not the
`/_healthz` the first draft had confidently given.

## Decision

A claim that rests on having run something says whether it was run. ✅ means run
while writing; ⚠️ means not run, and says what remains unverified and why.
Verification claims carry their date and their numbers — "✅ Verified on this
site: `4 tables carry data`, `5 rows across 4 tables`".

The rehearsal records are the same rule at document scale: each run of
`ops/rebuild.md` is written up with what it proved, what it did not, and what it
cost.

**The procedures use a different and stronger convention, deliberately.**
`ops/rebuild.md` states that "every command below is literal" and gives each
step its expected output: "Every step gives the command and **what you should
see**. Where they disagree, that is a finding." A reference marks the claims
that rest on evidence; a procedure carries the evidence inline, at every step.
The split follows the document kinds of HW-0021.

## Consequences

**The document is honest about its own coverage.** The ⚠️ items are precisely
the production-host procedures — a known gap rather than a hidden one.

**The marks have to be maintained through every edit, and a stale ✅ is worse
than no mark.** The 2026-09-21 reconciliation found a section still claiming a
deep check was untried after it had been run twice.

**The convention is narrower than it looks.** It lives in `operations.md` alone
— `ops/rebuild.md`, `ops/DEPLOY.md`, `README.md`, `PROJECT-BRIEF.md` and
`ops/MESSAGES.md` carry no marks at all — and within `operations.md` it attaches
to five sections against twenty-eight fenced command blocks. What is marked is a
*claim*, not every command; the ADR says so because the legend does not.

## Alternatives considered

**Write the playbook unmarked, as most runbooks are.** Rejected: "the
alternative — a playbook of plausible commands — is worse than no playbook,
being trusted at the moment somebody is least able to check it."

**Document only what has been run.** Rejected: the production procedures have to
exist before production does, or the first production event is also the first
draft.

**Mark every command rather than every claim.** Not chosen, and the file shows
why: most commands are illustrations inside an explanation, where a tick would
be noise. The cost is that the legend promises more than the convention
delivers.
