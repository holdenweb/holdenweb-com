# HW-0030: The site sends as a person, through a consumer account

**Status:** Accepted

**Date:** 2026-09-22

## Context

The site has to send transactional mail: registration confirmation and password
reset are the account feature (HW-0015), so mail is load-bearing for identity
rather than a nicety.

It is one person's site. There is no organisation behind it, no transactional
mail vendor in the estate, and nobody to receive mail sent to a role address.

## Decision

Mail goes over SMTP to `smtp.gmail.com:465` with SSL, authenticating as
`steve@holdenweb.com` — which is also `MAIL_DEFAULT_SENDER` and
`SECURITY_EMAIL_SENDER`. All of that is set as code-level defaults in `_wire`,
with `setdefault`, so a deployment can override any of it from the environment
without an edit.

**The only value not in code is the Gmail App Password.** It is named in
`config/app.toml`'s `secrets` list, so the site refuses to boot without it
rather than discovering it is missing when a visitor asks for a password reset.

Mail policy stays with the site: podpack "neither knows nor cares which mail
server this is" (podpack ADR-0025, ADR-0033).

## Consequences

**A visitor's password-reset mail arrives from a person**, which for this site
is honest rather than a limitation.

**The site's ability to hand out accounts depends on one consumer account.**
Google's sending limits, its App Password policy, and anything that happens to
that account are all upstream of this site's login working. There is no fallback
backend configured.

**The credential is a Gmail App Password, and rotating it has its own
procedure** (HW-0017), including the part most rotations skip: revoking the old
one, because a superseded App Password keeps authenticating.

**Non-secret mail settings are in code rather than in `.env`**, which is the
opposite of podpack ADR-0018's default placement for host settings. That is
defensible — they are the same on every deployment of *this* site, and they are
`setdefault` so a host can still override — but it does mean a reader looking
for "where does mail go" must read Python rather than a configuration file.

**The operator has a way to check it**: `flask --app holdenweb mail check`,
a command rather than a script because it needs a running application
(HW-0014).

## Alternatives considered

**A transactional mail service** (SES, Postmark, Mailgun). The right answer for
anything with users to lose, and rejected here on scale: it is an account, a
domain verification and a bill for a site that sends a handful of messages a
month.

**A role address** such as `noreply@` or `admin@`. Rejected: nobody reads
`noreply@`, and a reply to a password-reset mail from this site should reach
somebody.

**Putting the mail host and sender in `.env` with the other host settings.** Not
taken, because they do not vary by host here; `setdefault` keeps the option open
for the deployment that needs it.
