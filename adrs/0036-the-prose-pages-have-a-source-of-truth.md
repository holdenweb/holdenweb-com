# HW-0036: The prose pages have a source of truth, and it is not the backup

**Status:** Accepted

**Date:** 2026-10-16

**Amends:** [HW-0008](0008-content-is-delivered-not-committed.md), which stands
for three of the four content areas and is wrong only about the fourth.

## Context

HW-0008 decided that content "lives only in the host's
`hostdata/apps/<app>/<tree>`… it never passes through git", and recorded the
cost in its own Consequences: **"For `pages`, the served tree is the only copy
anywhere."** It named `scripts/backup.sh`'s `app-data.tar.gz` as that tree's
source of truth, and noted the archive is *declared* rather than
unconditional — so the only copy of the prose was protected by a mechanism an
app has to opt into.

That reasoning is sound for the other three areas and remains so. `pybooks`,
`blog` and `notebooks` are another repository's build output, reproducible by
rerunning a generator; committing them here would hold a second copy of
something whose source of truth is elsewhere.

The prose is different in kind. It is written, not generated. There is no
generator to rerun, so "reproducible" does not apply, and a backup was standing
in for version control.

Two things were checked on 2026-10-16 before deciding, because both were
assumed wrong at first:

- **The served tree was never at risk from a git operation.** `ops/DEPLOY.md:38-50`
  puts `data` and `logs` as siblings of `site` with `HOST_DATA_DIR=../data`,
  enforced by `PODPACK_ENVIRONMENT=staging` and podpack's
  `prepare-host-dirs.sh`. A capture aimed at `apps/os/site/hostdata` failed with
  "No such file or directory", which is that guard working. The risk was never
  `git clean`; it was having one copy.
- **The laptop held no content at all.** Its `pages` trees were byte-identical
  to podpack-pages' packaged seed. Nothing had been authored there, and
  podpack's seeding is one-shot (`registry.py:740`), so host edits could never
  have flowed back.

## Decision

The prose pages have a source of truth in **`~/sites/holdenweb-content`**, a
repository of its own holding `pages/md-pages/` and `pages/html-pages/`. It is
published by `just pages <target>`, whose source is `PAGES_SOURCE`, defaulting
there — the same shape as the three builder variables beside it
(`.justfile:37-44`).

**`PAGES_SOURCE`, not `PAGES_BUILD`.** The distinction is the decision: the
other three name a builder's output and can be thrown away, this names authored
source and cannot.

HW-0008 governs the rest unchanged. Three of four areas still never pass
through git, still arrive by `push-content.sh` into `refresh-content.sh`, and
still ride no deploy. What changes is that the served prose tree is now a copy
of something, rather than the thing itself.

## Consequences

**A backup stops being a source of truth**, which is the point. `app-data.tar.gz`
goes back to being a backup.

**There are now two copies to keep in step, and the asymmetry remains.**
Publishing goes one way: laptop to host. An edit made on the host still flows
back nowhere, and now it is worse than before, because the repository will
quietly disagree with what is served. The habit this requires — edit in
`holdenweb-content`, publish, never edit on the host — is not enforced by
anything. A `--mirror` publish is the only thing that would reveal a
host-side edit, by deleting it.

**The repository is local until Steve pushes it**, so until then the second
copy is on the same disk as the first. That is better than one copy and worse
than two machines.

**It holds binaries.** 5.4 MB over 59 files, including two 1.6 MB videos under
`edjas/assets/`. Git stores them whole on every change; they are published
material and rarely change, so this is cheap today and would not stay cheap for
a lane that churned.

**A mistake in `refresh-content.sh` became recoverable.** Its defaults are
`APP=pages TREE=html-pages`, so a bare invocation writes the prose tree — which
was the one unrecoverable target on the site and now is not. The defaults are
annotated rather than removed; removing them is a separate decision.

## Alternatives considered

**Commit the content into this repository.** Rejected for HW-0008's own
reasons, which still hold: the repository holds what a deploy carries, content
is not deployed, and a 721-file re-export has no business in an image layer. A
separate repository gets version control without putting content on the deploy
road.

**A plain directory outside the checkout.** This is what was first asked for,
and it was the smaller change. Rejected by Steve on 2026-10-14: it would move
the content without versioning it, leaving its safety to whatever backs up a
home directory — which is the substitution this record exists to end.

**Leave it, and rely on the backup.** Rejected. A backup answers "what did this
look like last night"; it does not answer "what changed, when, and why", and it
is declared rather than unconditional (podpack ADR-0035), so the protection
depends on an app's own claim.

**Give `pages` a builder, so it matches the other three.** Rejected as
ceremony. Markdown and HTML served as written need no build step, and inventing
one would add a stage whose only purpose is symmetry.

---

*Note for a reader following references: [HW-0009](0009-no-generator-runs-on-the-serving-host.md)
names the blog's source as `~/Projects/Python/sitescraper/build`. That path does
not exist; the builder is `blogscraper` and writes to
`~/Projects/Python/blogscraper/build`. The record is immutable, so the error is
recorded here instead; `README.md` and `.justfile` are correct as of this date.*
