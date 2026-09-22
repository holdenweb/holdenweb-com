# HW-0017: A rotation ends in revocation, and the new value never reaches a command line

**Status:** Accepted

**Date:** 2026-09-22

## Context

The mail and database rotation runbooks covered the tidy case and not the one
that matters — rotating *because a value has leaked*.

`operations.md` §8 began from an already-issued Gmail App Password and never
said to revoke the old one. A rotated-but-not-revoked App Password still
authenticates, so after a "rotation" the leaked value was still live.

§9 set the database password with `ALTER ROLE … PASSWORD '<new>'`, which puts
the plaintext into process arguments visible to `ps` and `podman top`. The rule
that forbids that — never put a secret in a command-line argument — predates
this repository and is written down nowhere in it; what had not been settled was
which psql mechanism actually obeys it, and that the site's own shipped runbook
did not.

podpack ADR-0018 says where a secret lives. Nothing in podpack says how one is
changed, or that changing it includes killing the old one.

## Decision

**Rotation is generate, install, verify, then revoke — in that order.** A
rotation that does not end in revocation has not removed anything; it has only
added.

**The new value never appears as a command-line argument.** The database role's
password is set with psql's `\password`, which prompts, hashes client-side, and
sends only the verifier. `pg_hba` trusts the container's local socket, so the
superuser exec needs no password to get in and do it. Because `\password`
prompts, the documented invocation cannot use `podman compose exec -T`.

**A leaked value means purging its cached copies too**, not only issuing a new
one — the editor session files that cached the mail password being the case that
prompted saying so.

## Consequences

**Revocation comes last so that a typo cannot lock the site out of its own
mail** — which is also how password reset reaches anybody, so losing it loses
more than notifications.

**A half-rotated state is real and must not be left.** The connection pool masks
a database change until `web` is recreated, so the site can be running happily
on a credential that no longer exists.

**The superuser is a special case.** The cluster read `POSTGRES_PASSWORD` once
at init and never re-reads it, so `\password` changes the live cluster while
`secrets.env` only keeps a future rebuild consistent — and a restore that runs
`db-init` would recreate the old one.

**No log captures the plaintext today, and one is armed that would.**
`log_statement` is unset, so it defaults to `none` — but `postgresql.conf` sets
`log_min_duration_statement = 200`, and the compose overlay bind-mounts the
PostgreSQL log directory onto the host. A slow `ALTER ROLE … PASSWORD
'<plaintext>'` would therefore be written verbatim into a host-persisted file
that outlives the container. `\password` avoids that too, though not entirely
for free: it still sends an `ALTER ROLE` carrying the SCRAM verifier, which is
not a plaintext password but is not nothing either.

## Alternatives considered

**The `ALTER ROLE … PASSWORD '<value>'` one-liner.** Rejected: the value is in
the process arguments, visible to anything that can run `ps` on the host, for as
long as the statement takes.

**Generating a new App Password and moving on without revoking.** Rejected — it
is the behaviour that makes a rotation ceremonial. The superseded credential
keeps working, so nothing has been taken away from whoever has it.

**Editing `secrets.env` and rebuilding, as the rotation itself.** Rejected for
the superuser, which never re-reads it: the file and the cluster would disagree
silently, and the disagreement would surface at the worst possible moment, which
is a restore.
