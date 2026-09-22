# HW-0006: The off-machine copy is a laptop mirror, pulled by hand

**Status:** Accepted

**Date:** 2026-09-22

## Context

The host's backups sat on the machine they protect, which is not a backup. Both
deployments — staging and, when it exists, production — are apps on `opal17`, so
losing that one host loses both and every archive of either.

The estate has no second server and no object store; a grep across the
repository for one finds nothing. There is a laptop. That is the whole of the
available hardware, and it is asleep most nights.

The tree that has to travel contains `secrets.env` in clear (podpack ADR-0035
says so), so wherever it lands is a directory of live credentials.

## Decision

`ops/pull-backups.sh` rsyncs `~/backups/$SITE_NAME` on the host to
`~/backups/$SITE_NAME-remote` on the laptop, with `--delete`, into a destination
created `0700` with `rsync -a` preserving the source's modes. `SITE_NAME` is a
variable, so production is one environment assignment.

**It is run by hand.** The script's own header prescribes an 05:30 cron line and
that line has deliberately not been installed; the recurring schedule is left
for an eventual always-on host, because a sleeping laptop is a poor puller. The
monthly booking in `operations.md` §16 is the interim.

## Consequences

**There is now a copy that survives losing the host** — which there was not, and
which was the point.

**The recovery point of that copy is the interval between manual runs**, not the
nightly 03:17 backup. This is measurable rather than rhetorical: as at
2026-09-22 the mirror holds exactly one dated directory, `20260902T212038Z`, so
the off-machine recovery point is **20 days old** against a nightly backup on
the host. The host half is scheduled and running; the off-machine half is manual
by choice, and the gap between those two facts is the risk.

**The copy is unencrypted credentials on a laptop.** The instruction is to keep
it "on a disk you would lose in the same sentence as this laptop, or encrypt
it", which is another way of saying that a laptop compromise is also a
site-secret compromise. Encryption *at rest, where the copy lands* is left to
the operator. That is a different question from the one podpack ADR-0035 closed,
which was whether to encrypt the archive itself — rejected there because "a key
is a second thing to back up".

**`--delete` buys fidelity, not bounded growth.** The script's header reasons
from a rotation that does not exist: nothing in `backup.sh`, `verify-backup.sh`,
`ops/backup.cron` or podpack prunes old backup directories. What `--delete`
actually guarantees today is that the mirror is the host's directory and not a
union of everything it has ever held — so an accidental host-side deletion
propagates, and the mirror will not outlive the host's retention once there is
one.

**It has never been restored from.** The transfer is proven; the restore is
booked (HW-0005) and unexercised.

## Alternatives considered

**Leaving the backups on the host.** Stated and rejected in `operations.md`: "A
backup on the machine it protects is not a backup."

**An additive copy that never deletes.** Rejected in favour of `--delete`, so
the mirror stays a mirror.

**A push from the host instead of a pull from the laptop.** Not a recorded fork:
nothing says a push was weighed. It follows from the laptop being the only other
machine, and from a pull being the direction that works when the machine holding
the credentials is the one that initiates.

**Encrypting the pulled tree as part of the script.** Considered and left as the
operator's option, offered in the header as the alternative to choosing the disk
carefully.

**A scheduled pull on the laptop.** Deferred rather than rejected, with a stated
trigger: install it on an always-on host when there is one.
