# HW-0033: The framework arrives on two tracks, and only the check knows whether they are in step

**Status:** Accepted

**Date:** 2026-09-22

## Context

podpack reaches this site twice, by two mechanisms that have nothing to do with
each other.

**The library** — the application factory, the registry, the login wiring —
arrives as a wheel, moved by `uv lock` and pinned by a floor in
`pyproject.toml` (HW-0019).

**The substrate** — the Containerfile, the compose files, the seven scripts,
the alembic scaffolding, the database configuration — arrives as files *in this
repository*, moved by a separate, deliberate `podpack substrate upgrade` against
a manifest of per-file hashes and classes (`verbatim`, `rendered`, `config`,
`seeded`; podpack ADR-0026).

Nothing makes the two move together, and a site can perfectly well run a new
library against old scripts, or the reverse.

## Decision

The two tracks are allowed to sit at different versions, and the authority on
whether they agree is `podpack substrate status`, which compares
`substrate.json`'s recorded version against the installed one, file by file.

Upgrading is therefore two acts: a lock change for the library, and a substrate
upgrade for the files — each with its own commit, its own evidence and its own
opportunity to refuse.

## Consequences

**They are out of step right now, and visibly so.** `substrate.json` records
podpack 0.9.1 while `pyproject.toml` requires 0.9.3, and the check's first line
says exactly that: "substrate recorded at podpack 0.9.1; compared against
0.9.3". A substrate upgrade is due, and HW-0020's locally edited `Containerfile`
is the first thing it will have to reconcile.

**Being out of step is not an error, and nothing treats it as one.**
`--check` exits 0. That is the right default — a site may take a library fix
without wanting new scripts — and it means the drift is only ever noticed by
somebody who runs the check.

**The substrate is the reason a fix cannot simply be applied here** (HW-0032):
a managed file patched locally is reconciled away at the next sync, so the fix
has to travel the substrate track, which moves only when somebody moves it.

**A restore has to get both right.** `scripts/restore.sh` brings back a tree and
a database from a backup; whether the tree's substrate matches the library the
lock will install is a question the rehearsals ask and the backup does not
answer by itself.

**Two tracks is two changelogs to read** at every podpack release: what changed
in the library, and what changed in the files. The release notes are one
document; the consequences land in two places.

## Alternatives considered

**Ship the substrate as package data and read it from the installed wheel**,
so there is one version and no drift. That is not available and podpack
ADR-0026 explains why: these files must be *in* the site's repository, because
compose, git and the operator all read them from the working tree, and because a
site must be able to edit them (HW-0020).

**Gate the library floor on the substrate version**, refusing to boot if they
disagree. Rejected as too strict for a real estate: most library releases do not
touch the substrate, and a hard gate would make every one of them a two-step
upgrade.

**Run `substrate status --check` in CI.** Not taken, and the obvious candidate
for the next improvement — it is the one mechanism that can see the drift, and
today it only speaks when asked.
