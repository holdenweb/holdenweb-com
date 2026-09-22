# HW-0018: The committed lock resolves everything from PyPI

**Status:** Accepted

**Date:** 2026-09-22

## Context

For five weeks — from the restructure as a podpack site on 2026-08-12 to
2026-09-16 — this site's `pyproject.toml` carried `[tool.uv.sources]` entries,
because the framework and three of its apps had no publisher of their own.
Both forms broke things that only showed up away from the laptop.

A **path source** (`{ path = "../podpack" }`) cannot be satisfied by a container
build context, "which has none by construction", so `uv sync` failed in the
image, in `ops/rebuild.sh`'s disaster-recovery path, and in CI alike.

A **bare git source** followed whatever each remote's default branch had moved
to, "silently, with no version bump to notice". Pinning to immutable revs fixed
that, and bought two more problems: a re-lock had to chase a cached git ref, and
the image build resolved against a remote *at build time*, needing git and a
network path to GitHub to do it.

All five distributions publish to PyPI now.

## Decision

**Every dependency in the committed lockfile resolves from `pypi.org/simple`.**
`pyproject.toml` declares ordinary version specifiers and carries no
`[tool.uv.sources]` block.

A path source is a local, uncommitted thing: the editable block lives in an
untracked `tool_uv_sources.toml`, to be pasted in for local work on an app and
taken back out. Working on a sibling checkout no longer means pushing before
re-locking here.

**The property is checked, not assumed.** When the git sources were retired it
was verified that "uv.lock carries zero git refs and every package resolves from
pypi.org/simple", and it still holds: the committed lock has 61 registry entries
and one editable, which is this project itself.

## Consequences

**A fix reaches this site only when it is released.** That lag is real and has
so far been short: podpack's `@operator_required` was adopted here hours after
it landed upstream, and the `unset CDPATH` fix to six substrate scripts reached
this checkout five days after podpack carried it. Both closed by an ordinary
release and a floor bump, which is the intended rhythm rather than an accepted
standing cost.

**The build needs neither git nor a network path to GitHub**, which is what made
HW-0020 possible.

**uv's cache is the trap that did not go away.** A package listing fetched
before a release does not contain it, and `uv lock` then refuses a version that
is demonstrably published. `--refresh-package` does not shift it;
`uv cache clean <pkg>` does. That is recorded in `operations.md` §10 because it
cost an evening.

**Nothing enforces the rule.** `tool_uv_sources.toml` is untracked *and
unignored*: it stands in `git status` as `??`, so a single `git add .` would
commit the editable block and the next container build would fail with a path
that does not exist in its context. A `.gitignore` entry would close that, and
there is not one.

## Alternatives considered

**Path sources**, which is how development started. Rejected: no build context
and no fresh checkout has the sibling directory, so every environment except one
laptop was broken.

**Git sources pinned to immutable commits**, the interim from 2026-09-02 to
2026-09-16. Rejected once the apps had a publisher: it kept the build dependent
on a remote being reachable, and made a routine re-lock an exercise in cache
invalidation.

**A private index.** Never on the table — the apps are public, and PyPI is where
their users would look for them.
