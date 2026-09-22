# HW-0015: Sign-up is public, gated by email confirmation, and confers no privilege

**Status:** Accepted

**Date:** 2026-09-22

## Context

On 2026-09-01 the site was found wide open. `SECURITY_REGISTERABLE` was `True`
with `SECURITY_CONFIRMABLE` unset — flask-security defaults it `False` — so
anyone could self-register and land an active session. `/config` sat behind only
`@auth_required('session')`. Together, those two let any anonymous visitor
register an account and read every secret the application holds.

Registration was closed outright the same day, in the same commit that fixed
`/config`. Three days later it was reopened: the site does want an account
feature, and closing registration had only ever addressed one half of a finding
whose other half did not depend on it.

podpack installs flask-security, the models, the datastore and the admin
predicate (ADR-0033). It says nothing about whether a site takes registrations,
on what terms, or what a registered account may reach.

## Decision

The site takes public registrations. `SECURITY_REGISTERABLE` and
`SECURITY_RECOVERABLE` are on, paired with `SECURITY_CONFIRMABLE`, so a
registrant gets no session until they follow a link mailed to the address they
gave. A test asserts both — that `/register` answers 200 and that confirmation
is on — so reopening registration cannot silently drop the gate.

**Privilege attaches only to membership of the `admin` role.** A confirmed
non-admin reaches nothing an anonymous visitor does not, beyond its own identity
in the navigation and eligibility for a password reset. No route anywhere in the
site is guarded by session alone.

## Consequences

**Mail becomes load-bearing for identity.** An SMTP outage stops sign-up and
password reset, not just notifications — which is why HW-0014 exists, and why
the mail check is part of the operator's toolkit rather than a nicety.

**Turning confirmation on made an unconfirmed account unable to sign in**, and
nothing in `flask users create` sets `confirmed_at`: neither flask-security's
datastore nor its CLI ever does, and podpack's `User` is a bare `FsUserMixin`
with no default. That is a hazard the code makes possible, not an incident that
happened — the one time it was checked against the real deployment, every
existing account already carried a `confirmed_at` and there was nothing to
grandfather. `operations.md` §12 carries the check and the fix-up snippet for
the next host, where it may not be true.

**Enabling confirmation changed password reset**, because `send_mail` is now
reached only for a confirmed account — which the reset-failure test fixtures had
to absorb.

**"Reaches nothing extra" is reasoning, not a test.** It rests on there being no
session-only guard anywhere in the site, which is checkable by reading and is
not checked by anything that runs: no fixture stands up a confirmed non-admin.
Worth a test the day a second privilege level appears.

## Alternatives considered

**Closed registration**, which the site actually operated from 2026-09-01 to
2026-09-04. Rejected on reflection: it removed a feature the site wants in order
to fix a hole whose dangerous half — an unguarded `/config` — was closed
independently and would have needed closing anyway.

**Open registration with confirmation off.** That is the instant-account hole
itself.

**`SECURITY_LOGIN_WITHOUT_CONFIRMATION`**, to spare the deploy any risk of
locking existing accounts out. Not taken: it makes the gate ornamental, which is
worse than not having one, because it looks like a gate.
