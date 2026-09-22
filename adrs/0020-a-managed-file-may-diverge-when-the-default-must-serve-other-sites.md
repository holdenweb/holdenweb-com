# HW-0020: A managed file may diverge when podpack's default has to serve other sites

**Status:** Accepted

**Date:** 2026-09-22

## Context

podpack's rendered `Containerfile` installs git in the builder stage, and
ADR-0012 records why: uv shells out to a real `git` for anything locked to a git
source, `python:3.12-slim` has none, and "not installing git at all" was
considered and rejected so that the failure would not land on whoever installs
their first app from a repository.

That reasoning arrived here with the file, and held here on its own terms for as
long as four of this site's apps resolved from GitHub. It stopped holding when
they all moved to PyPI (HW-0018): nothing `uv sync --frozen` does reaches for
git any more.

The site had faced the mirror-image question a fortnight earlier. Six managed
scripts under `scripts/` were failing on this laptop because of an exported
`CDPATH`, and they were deliberately *not* patched here: "patching holdenweb's
copies directly would create substrate drift — `substrate status --check` exists
precisely to catch a managed file that no longer matches podpack — and the next
sync would reconcile it away." The fix went upstream and arrived here five days
later in an ordinary release.

## Decision

A managed substrate file may be edited locally **when podpack's default has to
stay as it is for other sites**, and must not be otherwise. Everything else goes
upstream.

The git layer meets that test: podpack must keep installing git, because a site
that installs an app from a repository needs it. So the removal is this site's
to make, and this site's to carry.

Where such an edit is made, the removed material and the condition for restoring
it stay in the file, at the point a reader will hit them. `Containerfile` keeps
the commented `RUN` and names what would bring it back — a single git source
returning to `uv.lock`, an app pinned to a repository, a fork tried before
release — and records the measurement that justified taking it out: the builder
stage fell from 505.2 MB to 401.6 MB, while the shipped image came out identical
to the byte, because the second stage was already keeping git out of what serves
the site.

## Consequences

**The drift is visible but not enforced.** `podpack substrate status` now
reports `Containerfile  locally edited` with every other managed file `ok`, and
`--check` still **exits 0**. Nothing fails, nothing gates. That is exactly why
the restoring condition has to live in the file: a reader will meet it there,
and may never run the check.

**The next upgrade pays for it.** podpack keeps the site's version rather than
clobbering it when only the site has changed the file, and writes its own to
`Containerfile.new` for an explicit `--take-upstream` or `--keep` when both have
changed. Nothing is ever silently overwritten — but somebody has to decide. And
this is not a someday problem: `substrate.json` records podpack 0.9.1 while
`pyproject.toml` already requires 0.9.3, so an upgrade is due and this hunk is
the first thing it will have to reconcile.

**The operator message catalogue now says the opposite**, and this is the
larger practical cost. `ops/MESSAGES.md`'s `build-git-not-found` entry, severity
critical, still reads "(Fixed in the Containerfile; only bites a customised base
image.)" and instructs "Ensure the builder stage still installs git." Both
halves are now false for this site, and that entry is the one place an operator
meeting that message will look. Rewriting it to point at the commented `RUN` is
debt this decision created and has not paid.

**The saving is not in what serves the site.** It is 103.6 MB of builder layers,
kept wherever the build runs — which for this site is the host that serves it —
plus about twelve seconds whenever the base image moves and the layer has to be
rebuilt. Both figures are single measurements on one day, not standing
properties; and the absolute image size drifts with the tree, since `README.md`
is copied in and travels into the installed wheel. It is the *equality* between
the two builds that is the measurement, not the number.

## Alternatives considered

**Leave git installed, as the substrate renders it.** The zero-drift option, and
the one the CDPATH precedent argues for. Rejected on the measurement: 103.6 MB
and a network fetch, for a capability nothing in the lock asks for.

**Install it and delete it later in a single stage.** Rejected on ADR-0012's own
grounds — the layer above still carries the files, and the deletion only adds
another layer.

**Push the removal upstream into podpack.** Rejected, and this is what makes the
edit legitimate rather than lazy: podpack's default has to serve a site that
*does* install an app from a repository. A framework cannot take this site's
dependency posture as its own.
