# HW-0008: Content is delivered, not committed

**Status:** Accepted, and amended by
[HW-0036](0036-the-prose-pages-have-a-source-of-truth.md), which keeps every
argument below for `pybooks`, `blog` and `notebooks` and changes only the prose
`pages`: the served tree is no longer the only copy anywhere, because the prose
now has a repository of its own.

**Date:** 2026-09-22

## Context

The site has four content areas holding 879 files between them as at
2026-09-22 — 135 in `pybooks`, 721 in the blog export, 3 notebooks, and 4 + 16
in the two `pages` trees. Those counts drift, which is why they are dated.

Three of the four are the build output of a tool in *another* repository: orpy's
`build.py --fragments`, sitescraper's `blogscraper export`, podpack-notebooks'
`build.py`. Putting their output in this repository's history would hold a
second copy of something whose source of truth is somewhere else.

The site has already tried the two obvious arrangements and left both. The
content began *committed in this repository* — `e5575f0` deletes
`src/holdenweb/data/html-pages/` and `md-pages/` along with `content.py` and its
tests, some two thousand lines. It then travelled *inside the app
distribution*: "The content itself ships with the app and is seeded to the host
data root on first install." podpack ADR-0008 makes that seed a one-off, so the
second arrangement had a wall at the end of it, which `operations.md` states
plainly: "What an app upgrade does not do: deliver changed content. App data
seeds once."

podpack settles where an app's data lives (ADR-0007) and that a package seeds it
exactly once (ADR-0008). It does not say whether a *site's* content belongs in
version control, nor how it gets to a host.

## Decision

Content lives only in the host's `hostdata/apps/<app>/<tree>`, which this
repository gitignores. It is delivered straight into that tree by
`ops/push-content.sh` into `ops/refresh-content.sh`; it never passes through
git, and it never rides `ops/deploy.sh`. A deploy carries everything that *is*
in git — code, `config/`, the alembic history, the compose files — and nothing
that is not.

Three of the four areas are built on the laptop by their own generator. The
fourth, the prose `pages`, has no builder at all and is maintained on the host;
the same delivery road is available to it, there is simply nothing upstream
feeding it.

No rebuild and no restart is involved: `podpack_pages` resolves a page by
reading the file on every request, so a refreshed tree is live the moment it
lands.

## Consequences

**A typo fix is live in seconds and leaves no trace in the repository**, and a
721-file re-export never lands in a commit or an image layer.

**For `pages`, the served tree is the only copy anywhere.** The other three can
be rebuilt from their generators; the prose pages exist on the host and in the
backup, and nowhere else. That makes `scripts/backup.sh`'s `app-data.tar.gz`
their source of truth — and worth knowing: that archive is *declared*, not
unconditional. `backup.sh` builds its tar arguments from `plan.json`, so it
holds the apps that report data, honouring their excludes (podpack ADR-0035). An
app that declared none would be silently absent.

**git no longer answers what the site said on a given date.** The deploy history
records the chrome, not the words. The backup is the only history content has.

**A content mistake cannot be undone by reverting a commit**, which is why the
removal path is guarded as carefully as it is (HW-0010).

**git still names where content goes**, even though none of it travels that way:
`ops/push-content.sh` reads `git remote get-url <target>` and parses the same
scp-style URL as `ops/deploy.sh`, so the host and the path are written down once
(HW-0001).

## Alternatives considered

**Commit the content here and let `ops/deploy.sh` carry it.** This is where the
site started, and the diffstat of `e5575f0` is what leaving it looked like. It
puts every content change behind an image rebuild and drags generated HTML
through the history of a repository that is otherwise all source.

**Ship content inside the app distribution and update it by bumping the
version.** Also tried, and a dead end by design rather than by accident:
podpack ADR-0008 seeds once and never redelivers, so a content change would
need a release that could not reach an existing site.

**A webhook or CI job publishing content on push.** Nothing else on this site is
automated that way, and it would require the generators' repositories to know
about this one.
