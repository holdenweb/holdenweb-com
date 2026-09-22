# HW-0028: One migration history, re-parented so that it serves a database older than itself

**Status:** Accepted

**Date:** 2026-09-22

## Context

holdenweb.com had a production database before it had alembic. Its first
revision, `150cf4618ef7`, baselined a schema that already existed — that is what
a baseline is for, and it worked for the one database it was written against.

It also made `alembic upgrade head` useless anywhere else. An empty database has
nothing to baseline, so a fresh deployment, a scratch restore rehearsal and a
developer's laptop all got a history whose first step assumed tables it did not
have. podpack ADR-0009 gives the site one history driven by its app list; it
does not say how a history that began mid-life is supposed to serve a database
that has not begun.

## Decision

Write the missing root *afterwards* and re-parent the baseline onto it.

`69b5755e12e0` creates `user`, `role` and `roles_users` — "everything a fresh
database needs to run the site" — and declares `down_revision = None`.
`150cf4618ef7`, the original baseline, now declares `down_revision =
'69b5755e12e0'`.

The production database was already stamped at the baseline, so it never runs
the new root and is untouched. An empty database runs both, in order, and builds
correctly.

**The baseline's converging alters are made conditional rather than
unconditional.** They exist to bring the pre-alembic schema into line, where
columns were `NOT NULL`; a database built by the new root already has them
nullable. So the revision inspects the table and alters only what needs
altering — "and skipping matters on SQLite, which cannot ALTER COLUMN at all"
(HW-0027).

## Consequences

**One history serves three populations**: the live database that predates it, an
empty one, and a SQLite file. No branch, no `stamp` ritual in the deployment
procedure, no second history to keep in step.

**The root revision's date is later than the revision it precedes**, which looks
wrong in a listing and is the whole trick. Its docstring says so, because
nothing else can.

**A conditional migration is a migration that does different things in different
places**, which is exactly what makes migrations hard to reason about. It is
accepted here because the condition is a fact about the schema that the revision
can *ask* — not a flag, not an environment variable.

**Rolling back is still not a thing.** The `downgrade` direction exists in both
revisions and the site's revisions "are not written or tested for it"; the
rollback plan for a release with a migration is to restore last night's dump
(HW-0002).

## Alternatives considered

**Leave the baseline as the root and tell fresh databases to `stamp` past it.**
Rejected: it puts a manual step into every rebuild, restore rehearsal and
developer setup — precisely the places where nobody remembers, and where the
rehearsals show that an extra step is where evenings go.

**A second history for fresh databases.** Rejected against podpack ADR-0009: two
histories is two things that must agree for ever, and the whole value of one
history is that `upgrade head` means the same thing everywhere.

**Unconditional alters in the baseline.** They are what the autogenerator wrote
and they would break every SQLite run, which is most of the fast loop.
