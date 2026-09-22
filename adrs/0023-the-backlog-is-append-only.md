# HW-0023: The backlog is append-only, and what is still open is derived from it

**Status:** Accepted

**Date:** 2026-09-22

## Context

`ops/records/backlog.md` carries every finding since 2026-08-19 — 1,236 lines as
at 2026-09-22 — each with the evidence that raised it and, where closed, the
evidence that closed it. Item numbers are stable, so the list has gaps where
items were struck.

That is exactly what makes it the wrong thing to read when the question is
"what is still open?". A hand-made copy of the open items was tried first and
listed the open numbers literally, which makes it wrong the first moment an item
is fixed while saying nothing about having become wrong. (No such file survives
in git history; the account is the author's own, written at the time.)

## Decision

`backlog.md` is appended to and struck from, never rewritten.

The open set is *derived* from it by `ops/open-backlog.py` — `just still-to-do`
— into `ops/records/still_to_do.md`, which declares itself a copy and defers to
the backlog on any disagreement.

The derivation rules live in the script rather than in a list: the summary table
is the authority on what is live, a row is open unless its Item cell says
`**fixed**`, headings beginning Tier/Raised/Filing are structural, and an open
number with no section of its own still gets a stub, "because silently dropping
a number is how a backlog loses an item". `--check` reports staleness without
writing, reusing the existing extraction date so it does not cry drift merely
because a day has passed.

## Consequences

**An item marked fixed simply stops appearing**, and the recipe needs no
maintenance — the script never has to learn a number.

**The backlog edit and the regenerated extract land together**, usually in one
commit, and the commit message reports the count: "still_to_do.md: 10 open down
to 9." It has already gone wrong once: an audit amended the backlog alone and
the extract only caught up in the next commit, so the tree carried a stale copy
across a commit boundary — which is precisely the risk this arrangement is
supposed to bound, demonstrated.

**Nothing enforces regeneration.** CI runs pytest, there are no hooks, and
`just still-to-do --check` has to be remembered.

**The backlog grows monotonically**, and will eventually need a reader willing
to scroll. That is the accepted price of never losing the evidence that closed
something.

## Alternatives considered

**A hand-maintained list of open items.** Tried, and the reason this exists.

**Rewriting the backlog in place as items close.** Rejected: it loses the
evidence that closed them, and the stable numbering that lets a commit message
say "item 30" and mean something for ever.

**Tracking the open numbers in the script.** Rejected in favour of deriving them
from the table, so that closing an item is an edit to one file rather than two
places that must agree.
