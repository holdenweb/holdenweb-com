# HW-0013: The chrome is the site's, and it reaches other people's pages by the shortest hook

**Status:** Accepted

**Date:** 2026-09-22

## Context

Two problems arrived together.

The front page and the inner pages had drifted into different layouts — logo
treatment, nav position, rules, column widths — and every page loaded Bootstrap
4.6.1, jQuery and popper from CDNs. An audit across this site and the installed
apps' form templates found exactly **one** functional consumer of Bootstrap's
JavaScript: the signed-in account dropdown.

Meanwhile the site's overrides had started to rot. flask-security hardcodes
`{% extends "security/base.html" %}` in every one of its templates, so that file
has to exist, and here it existed as a byte-copy of `base.html`. The copy
drifted: it reached Bootstrap 4.1.3 from stackpath while every other page was on
4.6.1 from cdnjs, it lost popper, and it carried an SRI integrity hash belonging
to 4.0.0-beta — so a browser honouring SRI refused to run Bootstrap's JavaScript
on login, register and both password-reset pages. Nobody noticed until the file
was read.

Six of the seven installed apps belong to other distributions (HW-0011), and
several ship form markup carrying class names this site did not write.

## Decision

**One `base.html` for every page, one stylesheet, and no CSS or JS framework.**
The account menu is a native `<details>` disclosure, which is what removed the
last consumer of Bootstrap's JavaScript.

**Where the site already holds an app's template, it restyles it there. Where it
does not, it styles the app's class names from `styles.css` rather than
acquiring a new override.** `podpack-qrcode`'s form keeps its
`.form-horizontal`, `.control-group` and `.control-label`, and this site's
stylesheet gives those names a look. Taking on an override purely for styling
would couple by path, and podpack ADR-0005 records the consequence: if the app
renames the template, the override silently stops applying and nothing fails.

**An override sits at the hook the app or framework already provides, and
carries only the site's own layer.** `security/base.html` is a comment, one
`extends` and one emptied block — the hook flask-security hardcodes.
`templates/podpack_pages/codehilite.css` re-themes the token classes at the file
the app includes inline, so the site's palette wins for every pages-kind app at
once.

## Consequences

**No CSS or JS *framework* is fetched anywhere, and the site's own chrome loads
no third-party JavaScript.** Two third-party fetches remain and are not
oversights: `base.html` links Cabin from Google Fonts, and every Markdown page
loads MathJax from a CDN through `podpack-pages`' own `markdown.html`, which
this site does not override.

**"One stylesheet" is true of the chrome, not of the pages as served.** The site
also ships `podpack_pages/codehilite.css`, and book pages link `course.css` and
`notebooks.css` out of their content trees.

**The stylesheet now depends on class names inside another distribution.** A
rename in `podpack-qrcode` leaves that form unstyled with nothing failing. The
coupling is also partial: three of the five non-site class names in that
template are styled, and `.col-5` and `.controls` are now inert markup.

**Losing Bootstrap's Reboot means `styles.css` carries its own element-level
baseline** for body, headings, links and form controls.

**The `pdf` form templates do not follow this record, and that is a known
exception rather than an example.** `templates/pdf/booklet_form.html` and
`pagesplit_form.html` are near-verbatim forks of the app's own: they differ only
in the `extends` target, a `class="appform"`, a deleted `<hr>` and some
whitespace — twenty lines of another project's prose duplicated to add one CSS
class, and neither carries the comment the other overrides do. `podpack-pdf`
offers a layout hook (`templates/pdf/base.html`, selected by `pdf_layout`)
designed for exactly this, and these forks bypass it. Bringing them into line is
work nobody has done.

**`codehilite.css` is a fork too**, and honestly labelled as one: CSS has no
inheritance, so the override is a hand-maintained copy carrying a standing
obligation to track the app's class set. It is still the right call, because it
is the app's own include point — but the reason is the hook, not the absence of
copying.

## Alternatives considered

**Keep Bootstrap for the app forms and the account dropdown while the chrome
becomes the site's own.** This was the position actually taken, in writing, and
reversed 48 minutes later the same morning once the audit found a single
consumer. A written decision overturned by an audit is the process working.

**Fork `podpack-qrcode`'s form template to give it the site's classes.**
Rejected in favour of styling from here: an override couples by path and reverts
silently on a rename, so taking one on for cosmetics buys a second failure mode
rather than avoiding one.

**Keep the `security/base.html` fork and just correct its asset links** — the
obvious minimal fix. Rejected because copies drift, and this one had already
silently disabled a framework on four pages without anybody noticing.

**Theme code blocks from `styles.css` instead of overriding the app's
`codehilite.css`.** Rejected because the app includes its own file inline from
the Markdown template, so overriding that file is the path that actually wins.
