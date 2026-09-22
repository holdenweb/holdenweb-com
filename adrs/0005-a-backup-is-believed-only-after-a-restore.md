# HW-0005: A backup is believed only after a restore, and "occasionally" is a calendar

**Status:** Accepted

**Date:** 2026-09-22

## Context

The principle is not this site's to claim. `scripts/verify-backup.sh` arrives
from the substrate saying it already: "A backup regime is a claim about the
future, and the only evidence for it is a restore that has actually happened.
This is the cheap half of that ... The expensive half is `scripts/restore.sh`
into a scratch deployment, which is what finally proves the data comes back.
**Do that occasionally; do this nightly.**"

The sentence began here — `ops/restore-rehearsal.sh`, 2026-08-19 — and podpack
carried it into the substrate the next day. What came back with it was the word
**occasionally**, which is not a schedule. Filling that in is this site's
decision.

There was a second thing to settle. podpack's arrival replaced this site's own
three-day-old backup scripts, and one capability got thinner in the swap:
`restore-rehearsal.sh` had restored into a scratch database beside the live one
and counted the rows that came back, whereas `verify-backup.sh` reads every
archive through the tool that would restore it and stops there — because
"restore into a scratch namespace" is not a thing every backing store spells the
same way. Verification that an archive is *readable* is not verification that it
*applies*.

## Decision

The nightly pair is the cheap check and is explicitly not the proof: `backup.sh`
at 03:17 and `verify-backup.sh` at 04:23 on the host, both logged.

The proof is `scripts/restore.sh` into a scratch deployment, and "occasionally"
is written down as a calendar in `operations.md` §16: monthly into a scratch
deployment, monthly from the laptop's own copy, and — the trigger that matters
more than either interval — **a backup and a rehearsal of it before any schema
change.**

Each rehearsal is written up as a dated, append-only record under `ops/records/`,
kept "because a later run that disagrees needs something to disagree with", and
each record states what the run did *not* cover as well as what it did.

## Consequences

**The recovery path is a measured number rather than an assumption.** The
rehearsal of 2026-09-03 rebuilt the live staging host into a scratch deployment
and reached a public 200 in 1m 4s from `up.sh` — with clone and restore
dominating the rest — every table's row count matching, and the integration
suite green against the public URL.

**The evidence came from failures.** The first rehearsal cost eleven defects,
five of them in the document itself. Separately, getting `restore.sh` to run
against this site's data took three attempts on 2026-08-24, and "the two that
failed were worth more than the one that worked: the first found that
`restore.sh` could not run on Linux at all, and the second that a document
describing it can be wrong in ways only a real host reveals."

**Half the calendar is unexercised.** The scratch-deployment restore has been
run twice, both on `opal17`. The monthly rehearsal *from the laptop's copy* has
never been run: the pulled mirror has been proven to transfer (HW-0006) and
never proven to restore. It is booked, not practised.

**Nothing enforces a monthly drill on a site with one operator**, which is the
standing cost of putting the proof in a calendar rather than in a script. The
nightly tick remains worth exactly what it says it is worth, and `operations.md`
§5 says so in bold rather than letting it be read as more.

**§16's table has already gone stale in one row** — it still lists the
five-minute health poll as "not running yet", which HW-0004 has since made
false. A calendar is a document like any other and drifts like one.

## Alternatives considered

**Treating `verify-backup.sh`'s nightly exit 0 as the backup check.** Rejected
in the same commit that adopted podpack's scripts, which chose to say the
capability was thinner rather than gloss it.

**Keeping this site's own `restore-rehearsal.sh` alongside podpack's scripts.**
Rejected because it was "already the third divergent copy of this idea in
`~/sites`" — the argument that retires a script is usually the number of copies
of it, not its quality.

**Rehearsing into the live deployment.** Rejected in favour of a scratch
directory beside an untouched live one, so a drill's blast radius is a chosen
window rather than the site.
