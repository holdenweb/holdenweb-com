# HW-0014: A mail failure is reported to the visitor, in a sentence they can act on

**Status:** Accepted

**Date:** 2026-09-22

## Context

With the SMTP credential rejected, `POST /reset` answered 500 with a traceback.
flask-security calls `send_mail` from inside `forgot_password` and catches
nothing the backend raises, so a service problem the visitor could do nothing
about was handed to them as a server error — and the view flashes its own
cheerful "instructions have been sent" regardless, so the alternative to the 500
was a visitor waiting for mail that had never left.

The mechanism for fixing that is podpack's and is already recorded: ADR-0033
says "a site that sends mail may pass `PODPACK_MAIL_UTIL_CLS` so that a delivery
failure is reported rather than raised through flask-security's uncaught views",
and podpack's `auth.py` makes the call. What podpack leaves entirely open is
what such a class should *do* — and in particular whether the visitor is told at
all, or only the log.

## Decision

The visitor is told.

`ReportingMailUtil` logs the failure with its exception type, flashes the
visitor one plain sentence, and lets the request finish. Two guards shape the
telling:

**Outside a request context it degrades to log-only.** Mail sent from a CLI path
has nobody to flash, and dying inside `flash()` would turn a mail problem into a
crash somewhere unrelated.

**The sentence is withheld when `SECURITY_RETURN_GENERIC_RESPONSES` is on**,
because `send_mail` is reached only for an address that has an account, so
saying "we could not send it" would answer the question that setting exists to
refuse.

It catches `Exception`, not one family: smtplib, ssl and socket each raise their
own, and the useful fact is the same in every case — the message did not go.

## Consequences

**One class covers every mail-sending path in flask-security**, and the
request-context guard is what makes that true rather than aspirational.

**The visitor gets two flashes that disagree** — the site's failure notice
beside flask-security's success message. Accepted as better than silence, and
untidy enough to be worth recording rather than discovering.

**The disclosure posture is inherited, not chosen.**
`SECURITY_RETURN_GENERIC_RESPONSES` is set nowhere in this site or in podpack;
flask-security defaults it to `False`. The guard therefore never runs in
production today. It exists so that turning the setting on later cannot quietly
reopen the question, and a test exercises the branch so that it stays correct
while unreached.

**The companion check is a Flask command**, `flask --app holdenweb mail check`,
by podpack ADR-0031's rule: what needs no running application is a script,
anything that needs one is a command — and this builds the app, reads its config
and reaches into `app.extensions["mailman"]`. It would also have been unusable
as a script, because `scripts/` is not in the image: the Containerfile copies an
explicit allow-list and `scripts/` is excluded by omission rather than by any
`.dockerignore` rule.

## Alternatives considered

**Log the failure and say nothing to the visitor.** This is the option podpack's
mechanism equally permits, and it is the one this record rejects: a visitor who
is told can try another address or come back later, and a visitor who is not
waits for a message that will never arrive.

**Wrap the view, or catch `SMTPException` in an error handler.** Rejected: the
extension point exists, and catching one exception family would have missed the
others that a broken credential, a bad certificate or an unreachable host each
produce.

**Turn generic responses on and suppress the message.** Not taken, and not
rejected on its merits either — the site has simply never set it. Recorded here
so that whoever does set it finds the guard already waiting rather than having
to think about enumeration a second time.
