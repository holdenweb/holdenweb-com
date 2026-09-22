# HW-0021: A document declares its kind and its reader

**Status:** Accepted

**Date:** 2026-09-22

## Context

By 2026-08-23 `ops/` held a procedure, a backlog and an 842-line rehearsal
transcript side by side, with the two scripts that serve the procedure. From the
outside they looked alike, and their failure modes are not alike: **a reference
goes stale when the system changes, a procedure goes stale when nobody runs it,
and a record cannot go stale at all, because it is history.**

The distinction had already been arrived at once by accident. Splitting
`operations.md` §6 from `ops/rebuild.md` worked precisely because one is
consulted by somebody who knows what they want and the other is followed by
somebody who knows nothing — but nobody had said so.

The hazard is concrete: an operator at three in the morning opening the
transcript of a rehearsal and following it as though it were the procedure.

## Decision

Every document opens with a one-line blockquote naming its kind and its reader,
and — where it is not obvious — where it will eventually live. The kinds are
**Introduction** (`README.md`), **Orientation** (`PROJECT-BRIEF.md`),
**Reference** (`operations.md`), **Procedure** (`ops/rebuild.md`) and **Record**
(`ops/records/*`).

A record says so in its own header and forbids being followed. Records of an
*event* are named by date, so they sort in the order they are ever wanted; the
standing records — the backlog and its extract — are not dated, because they
have no event.

## Consequences

**An operator can tell in one line whether to read a document or obey it**,
which is the whole of the value.

**The convention was applied in one sweep and has not been applied since.** Of
ten tracked Markdown files, four carry no kind header, and every document added
after the decision lacks one: `ops/DEPLOY.md`, `ops/MESSAGES.md`,
`ops/records/2026-09-03-rehearsal.md` and `ops/records/still_to_do.md`. The five
that carry headers are exactly the five the original commit touched. The
record-kind header in particular has never been written a second time —
including on the second rehearsal, which now sits in `ops/records/` beside a
transcript whose header says "Not a procedure: do not follow it", which is
exactly the hazard the decision named.

**Nothing enforces it.** No test, script or recipe mentions the kinds, so
adherence is a habit and the habit has lapsed.

**It tells a later editor what may be revised.** When the app rename swept the
documents, `ops/records/` was left alone on purpose: "those are dated records of
what was true then, and `backlog.md` declares itself append-only." A kind header
is what makes that rule visible to somebody running a search-and-replace.

## Alternatives considered

**A directory per kind**, so the filesystem carries the distinction. Partly
taken — `ops/records/` exists — and partly rejected, because a document's kind
has to be legible when it is opened directly, which is how documents are usually
met.

**A naming convention instead of a header.** Rejected: a filename has to serve
too many other purposes, and a reader who has already opened the file is past
it.

**Leaving it implicit**, as it had been. Rejected because it had already
produced a transcript indistinguishable at a glance from a runbook, in the
directory an operator reaches for under pressure.
