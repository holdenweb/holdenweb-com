# HW-0000: Template

**Status:** Template — copy this file, do not edit it in place.

**Date:** yyyy-mm-dd

## Context

What was true that forced a choice. The pressure, not the answer: what did not
work, what had to be reconciled, what would have gone wrong. Enough that a
reader who was not there can feel the problem before reading the decision.

## Decision

One paragraph, in the present tense, saying what we do. Not "we will" — an
accepted record describes how the system is.

## Consequences

What follows, including what got worse. A record with no costs in it is a
record nobody will trust. Say what this forecloses and what it makes someone
else's problem.

## Alternatives considered

What else was on the table and why it lost. This is the section that stops a
decision being reproposed in six months.

---

## How to use these records

**They are numbered `HW-nnnn`, and that is deliberate.** This repository's
prose already cites podpack's records as bare `ADR-nnnn` — `README.md` says
"login | podpack core (ADR-0033)" and `PROJECT-BRIEF.md` links half a dozen of
them. A second sequence spelled the same way would collide precisely where
somebody is trying to follow a reference. So: `ADR-nnnn` means podpack's,
`HW-nnnn` means this site's.

**A record here never restates one of podpack's.** podpack's records say why
the *framework* is as it is; these say what *this site* decided, which is
mostly one of two things: a choice podpack deliberately leaves to a site (which
apps, where they mount, which overlays, what the operator can see), or a policy
that is this site's alone (how content is published, what may be in the
lockfile, how records are kept). Where a record here depends on one of
podpack's, it cites it rather than repeating it.

**A record is immutable once accepted.** When a decision changes, write a new
one that supersedes it and mark the old `Superseded by HW-nnnn`. Do not rewrite
an existing record: the reasoning that was true at the time is the thing of
value, and a record edited into agreement with the present teaches nobody
anything.

Statuses in use: `Accepted`, `Deferred` (a decision not to decide yet, with the
trigger to watch for), `Rejected`, `Superseded by HW-nnnn`.

**What lives where.** These four overlap and would otherwise drift:

| | Answers | Changes when |
| --- | --- | --- |
| `README.md` | how do I run and update it? | the interface does |
| `PROJECT-BRIEF.md` | where am I, and what is this? | the shape of the site does |
| `operations.md` | what exactly do I type, and what will it do? | a procedure does |
| `adrs/` | why is it like this? | never — superseded instead |

**Date** is when the record was written, not when the decision was taken. Most
of the first batch were written on 2026-09-22, reconstructing decisions made
over the preceding seven weeks from the commits that carry them, so several
cite evidence from well before their own date. Where the timing matters, the
Context says so.
