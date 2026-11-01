# HW-0037: The site sends as itself, through a mailbox of its own

**Status:** Proposed — supersedes [HW-0030](0030-the-site-sends-as-a-person.md)
once production has cut over; until then HW-0030 describes what runs.

**Date:** 2026-11-01

## Context

HW-0030 has the site sending as `steve@holdenweb.com` through `smtp.gmail.com`
with a Gmail App Password. Two of its premises were wrong when it was written.

- **The account is Google Workspace, not consumer Gmail** (Steve, 2026-10-12),
  so the costs it weighed — including its rejection of a mail service on scale
  — were weighed for the wrong account.
- **"A deployment can override any of it from the environment" was never
  true.** `_wire` reads `MAIL_PASSWORD` from the environment and nothing else:
  with `MAIL_SERVER` and `MAIL_PORT` set there, `app.config` still said
  `smtp.gmail.com:465` (podpack's briefing, tested 2026-10-14; neither
  `src/holdenweb/__init__.py` nor `config/app.toml` has changed since).

And the site must now **receive** mail as well as send it. The contacts app
tracks the threads its enquiries start, and nothing here can read a message.
This domain's MX is Google, and `info@holdenweb.com` — the address in every
page's footer — is to be a Google Group for people (Steve, 2026-10-12).

podpack's ADR-0040 gives each site a mailbox in `mail.holdenweb.com` and each
deployment an address there, and weighs the alternatives to doing so. This
record is what it means for this site.

## Decision

**This site's mnemonic is `hw`, and its mailbox is `hw-admin`.**

| Deployment | Sends from, and receives at |
| --- | --- |
| staging — `os.holdenweb.com`, `hw-stag` on opal17 | `hw-stag@mail.holdenweb.com` |
| production — `holdenweb.com`, `hw-prod` on opal17 | `hw-prod@mail.holdenweb.com` |

**All of the site's mail goes this way, transactional mail included.**
Registration confirmation and password reset leave from the deployment's own
address, not from a person. `info@holdenweb.com` stays with people, and the
site never reads it.

## Consequences

**The Gmail App Password retires, which under HW-0017 means it is revoked** —
in Google, once production's mail has moved and been seen to work — not merely
deleted from `secrets.env`. After that, nothing in Steve's own account is
upstream of the site's login.

**A reset mail now comes from a role address**, which HW-0030 rejected because
"nobody reads `noreply@`". A reply lands in `hw-admin`, and nothing reads it
there until the receiving app does, unless somebody logs in to the mailbox. An
Opalstack address can forward to a person as well as deliver, which would close
the gap; that is not set up.

**Transactional mail and correspondence share an address.** The briefing
recommended keeping them apart. They stay distinguishable: the contacts app can
put a `+token` in `Reply-To:` — sub-addressing is delivered, checked 2026-11-01
— and an untagged reply is then not correspondence.

**Staging can read production's correspondence and send as production.** That
is ADR-0040's trade, accepted here because one person runs both deployments.

**The cut-over goes staging, then production**, each deployment taking the
mailbox's password into `secrets.env` by hand, once (ADR-0040). A deployment
that has not cut over sends exactly as HW-0030 describes.

**Where mail goes becomes a deployment setting**, because it now varies by
deployment — the condition under which HW-0030 said it would move to `.env`.
The address and the login are in `.env` and the password in `secrets.env`, and
a reader no longer has to read Python to find out.

## Alternatives considered

The provider-level choices — Workspace, mail on the deployment's own hostname,
a mail service, a mailbox per deployment — are ADR-0040's, and are not
repeated here.

**Keep transactional mail on Gmail and move only correspondence.** Keeps the
two apart, as the briefing recommended, but leaves the site's login hanging on
a person's account and its App Password, with two transports to configure and
to check.

**Send from Opalstack as `@holdenweb.com`.** This domain's SPF already includes
Opalstack, so it would pass. Replies would go to Google's MX, where nothing of
the site's can read them.

**Poll the administrator's own mailbox.** The site would hold delegated access
to a person's mail to find the fraction addressed to it.
