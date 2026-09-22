# HW-0011: Every feature that can be a podpack app leaves this repository

**Status:** Accepted

**Date:** 2026-09-22

## Context

Before the conversion this repository served everything itself: an HTML tree and
a Markdown tree behind a `ContentSource` abstraction, the QR-code generator, the
PDF booklet maker and page splitter, and the forms behind them. All of it
worked.

The conversion to podpack made extraction *possible*. It did not make it
obligatory, and extraction has a standing price: a one-line fix to the blog
becomes a release in another repository, a floor bump here, and a re-lock.

## Decision

Every feature that can be a podpack app is one, distributed separately. Seven
apps are installed and six of them live elsewhere — in four distributions, since
`podpack-pages` ships `pages`, `pybooks` and `blog` between them (podpack
ADR-0038).

What stays here is what cannot be generalised: this site's identity. Its own
package, installed as the app `main`, keeps the front page, `/config`, `/ip`,
the legacy redirects (HW-0012), and `templates/` plus `static/` — **and the
extensions that are the site's rather than any feature's.** `_wire` attaches
flask-mailman and flask-paranoid, sets the registration and session policy,
names the mail utility that reports delivery failures, registers the 404
handler, and adds a `mail` CLI group. That boundary is podpack ADR-0025's, and
it is 50 lines of real policy, not a formality.

**The site does not remap.** `config/app.toml` has no `[site.mounts]` key at
all: each app is accepted at the mount it asks for, and where that differs from
the address the site used to serve, the site pays in permanent redirects rather
than in configuration.

## Consequences

**`src/holdenweb/__init__.py` is a factory delegation plus `_wire`**, and
`views.py` is a front page surrounded by redirects. That is the whole of the
site's code.

**The features are versioned independently and reusable**, which is what
`podpack-demo` exists to prove — a second site built from podpack's
documentation rather than copied from this one.

**Nothing about the blog, the courses, the notebooks, the QR generator or the
PDF tools can be changed in this repository any more.** A fix is a release
somewhere else and a floor bump here (HW-0019).

**The packaged content is not the live content.** An app seeds its data once
(podpack ADR-0008), so an app upgrade does not deliver changed content to a host
that already has the directory — which is the constraint behind HW-0008.

**Two of the six apps kept their old address and four did not**, which is where
`views.py`'s redirect routes come from. Accepting each app's default mount is
cheap for the app and permanent for the site.

`HTTPContentSource` did not survive the move, but it had been mothballed before
it: the abstraction went with dead code, not with a working feature.

## Alternatives considered

**Keep the working code here and let `podpack-demo` carry the proof.** Rejected:
the demo's whole value is that it was *not* copied from here, and a site that
keeps its features cannot demonstrate that the plugin contract is enough.

**Extract only the obviously general things and keep the PDF tools in-repo.**
Rejected once the external app was verified a superset of the built-in — the
same three routes plus `secure_filename`, a page ceiling and correct packaging —
and it asked for the mount the built-in already had, so nothing moved that a
visitor could see. That last property made `pdf` the easiest one to take, and it
is the only app for which it was a selection criterion.

**Remap the apps with `[site.mounts]` so the old addresses kept working.**
Rejected in favour of redirects: a mount override is invisible in the app's own
documentation and has to be maintained for ever, whereas a redirect is visible
in `views.py`, testable, and tells a visitor what happened.
