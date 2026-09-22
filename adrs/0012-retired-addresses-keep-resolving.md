# HW-0012: Retired content addresses keep resolving, and the redirect belongs to the site

**Status:** Accepted

**Date:** 2026-09-22

## Context

The content has moved twice under visitors' feet: out of this package into
`podpack-pages`, and then the Python course books out of the pages app into
`pybooks`, with an experimental static tree at `/python` retired along the way.

This is a thirty-year-old site. Each move orphans bookmarks and search-engine
entries for addresses that were never the apps' — they were the site's, and
several of them predate podpack by a decade.

The first redirect was not written for bookmarks at all. When the course books
moved, the "Python" navigation entry kept pointing at `/python` because *it
could not point anywhere else*: a podpack `Section` is a label and an endpoint,
resolved by `url_for` with no arguments (podpack ADR-0022), so it cannot carry
the `name` argument `pages.page` needs. The route had to exist for the
navigation to work. It became a pure bookmark redirect only later, when
`pybooks` arrived with a nav entry of its own.

## Decision

The site's own app keeps a permanent 301 for every retired content address —
`/note/<name>`, `/page/<name>/`, `/asset/<path>`, `/python/` and its subtree,
`/pages/python-classes/` and its subtree — and those routes live *here*, not in
the app that now serves the content, because the old address belonged to the
site. `/asset` strips the old tree name (`html/`, `md/`) that the unified
namespace dropped. Each redirect has a test.

This extends to registering routes **inside another app's mount point**. When
the course books moved, the site's own app could not own `/pages/python-classes`
without shadowing the pages app; once the pages app no longer served anything by
that name, the site took the address back. podpack ADR-0006 says the shape of
the address space belongs to the site, and this is that carried past the point
where any app is mounted there.

## Consequences

**`views.py` is now mostly redirects, and can only grow.** Knowledge of retired
layouts — that assets once carried a tree name — is kept alive here
indefinitely, in the only place that still remembers.

**One route exists by routing precedence.** `/pages/python-classes/<rest>` has
more static segments than the pages app's `/<path:name>` catch-all, so Flask
matches it first. That is a dependence on Werkzeug's rule ordering, and it is
pinned by a test that says so rather than left to be rediscovered.

**A permanent redirect is a promise.** It cannot be withdrawn without breaking
the thing it was added to protect, so each one is a commitment taken on the
site's behalf, for ever, by whoever adds it.

**The promise is about content addresses.** `/config` was deliberately taken
away from every reader who is not an operator, and answers 404 to the rest
(HW-0016) — with no redirect, because that was a removal rather than a move.
Registration was closed for three days in September and then reopened
(HW-0015), so `/register` never needed one either.

## Alternatives considered

**Let the old addresses 404.** Nearly free for `/python`, whose static tree was
never in git, a mount or a backup — a clean-checkout build already 404'd it. It
was repointed anyway, first because the navigation needed the endpoint to exist,
and afterwards because a bookmark from 2015 is not worth less than one from last
week.

**Teach `podpack-pages` the old addresses.** Rejected: the app serves one
namespace, and these URLs are this site's history rather than the app's. An app
carrying another site's retired routes is an app that cannot be reused.

**Remap the apps so the old addresses still worked** — see HW-0011, where the
same question is answered from the other side.
