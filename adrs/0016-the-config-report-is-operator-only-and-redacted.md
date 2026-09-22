# HW-0016: The config report is operator-only, and redacts its values regardless of who is reading

**Status:** Accepted

**Date:** 2026-09-22

## Context

`/config` serialises the whole Flask config — `SECRET_KEY`,
`SECURITY_PASSWORD_SALT`, `MAIL_PASSWORD`, and `SQLALCHEMY_DATABASE_URI` with
the database password inside it. Until 2026-09-01 it sat behind
`@auth_required('session')`, so any authenticated session could read it: a route
guarding strictly more sensitive content than `/_status` with strictly less.

That is the slip this record is about, and the point is that it was a *guard*
that slipped. A route whose safety is entirely a decorator is one decorator away
from publishing its contents.

## Decision

Three things, of which only the third is unusual.

**The route exists.** An operator wants to know what the running application
thinks its configuration is, and a diagnostic endpoint is worth having.

**It is operator-only, not merely authenticated.** It carries podpack's
`@operator_required`, which asks this site's configured admin predicate, treats
a raising predicate as a refusal, and answers 404. The 404-not-403 reasoning and
the rejection of flask-security's `roles_required` are podpack's, recorded in
its own docstring and backlog item 30; this site chose them first, in September,
and now inherits them.

**Every value that looks like a secret is redacted regardless of the guard.**
Any key carrying `SECRET`, `PASSWORD`, `SALT`, `TOKEN` or `KEY` — plus
`SQLALCHEMY_DATABASE_URI`, whose name does not advertise the password inside it
— is replaced by `<redacted, N chars>`. Keys still show; values do not. The
guard defends the config's shape, the redaction defends its secrets, and a
separate test pins each.

## Consequences

**An operator sees that a credential is set and how long it is, never what it
is** — enough to spot the usual mistakes, and nothing to shoulder-surf,
screenshot, or paste into a support log. That is the house rule for secrets
everywhere in this estate: report shape, never value.

**A name-based denylist trades false negatives for false positives, and this one
is heavy on the second.** Measured against the shipped config, 71 of 363 keys
are redacted and about five of them carry a secret. The rest are booleans,
integers, template paths and flash messages: `SECURITY_PASSWORD_HASH`
(`argon2`) reads `<redacted, 8 chars>`, `SECURITY_PASSWORD_LENGTH_MIN` (8) reads
`<redacted, 1 chars>`, and a 94-character flash message reads as its length.
So the login settings an operator would most want to diagnose are exactly the
ones a `PASSWORD` substring hides. The false negative is real too — a secret
under a key carrying none of those markers would print — but it is the smaller
of the two problems in practice.

**`/config` and `/_status` are now guarded alike, and neither publishes a secret
value.** They are not equivalent: `/config` also returns the site map and 363
key names, and `/_status` reports database identity asked of the server and
per-app directory writability. "No more than `/_status` says" is the aim
recorded in backlog item 34, not an achieved state.

**Removing the decorator fails `test_config_is_not_public`** — verified by doing
it, not by reading it.

## Alternatives considered

**The guard alone, without redaction.** Rejected, and this is the whole point of
the record: the guard regressed once, and that regression *was* the incident. A
second, independent mechanism means the next slip is embarrassing rather than
disclosing.

**A bare `<redacted>` placeholder.** Rejected in favour of the shape indicator
the estate's secret tests already use — a length distinguishes "unset" from
"set to the wrong thing", which is most of what an operator is looking for.

**An allowlist of keys safe to print**, which would invert both error
directions. Not considered at the time; it is the obvious answer to the false
positives measured above, and the reason this record does not simply declare the
redaction good.

**Deleting the route.** Not taken: an operator wants to know what is set.
