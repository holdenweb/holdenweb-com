# HW-0035: A cookie is tightened to what it is worth, and a stand-in says what it stands in for

**Status:** Accepted

**Date:** 2026-10-14

## Context

This site issues two cookies that matter. Flask's `session` carries a browsing
session; flask-login's `remember_token` carries the right to *be* a user, for
as long as it lives. They had been treated as one thing, and set in the same
two lines:

```python
app.config.setdefault('REMEMBER_COOKIE_SAMESITE', 'strict')
app.config.setdefault('SESSION_COOKIE_SAMESITE', 'strict')
```

One of those lines worked. Flask ships `SESSION_COOKIE_SAMESITE` in its own
defaults, so by the time `_wire` runs the key is already present and
`setdefault` finds it and does nothing; `REMEMBER_COOKIE_SAMESITE` is not a
Flask key, so that one took. Two adjacent lines, one live and one dead, failing
identically to the eye. The running site was serving
`session=...; HttpOnly` — no `SameSite`, and no `Secure` either, since
`SESSION_COOKIE_SECURE` is also a Flask-shipped key and was never set at all.
`REMEMBER_COOKIE_SECURE` was simply absent, so the longer-lived credential went
out in clear too.

This was not a typo. `_wire` is written **entirely** in `setdefault`, by a
deliberate convention its own docstring states: podpack has already applied
`config_overrides` by then, so a caller's override wins over the site's
constants. The convention is sound and the idiom is right for every key the
site invents — and silently inert for every key the framework pre-populates.

Discovered on 2026-10-14 by booting the site and reading its config back,
after a survey of the estate took the source at its word and reported
`SameSite=strict` as being in force.

## Decision

**Cookie policy is assigned, not defaulted**, as one block, because a key the
framework pre-populates can be set but not defaulted. This is the documented
exception to `_wire`'s `setdefault` convention, and the docstring says so.

**`Secure` is derived from `PODPACK_ENVIRONMENT`**, not hardcoded — podpack
ADR-0039's argument applied one layer out: a derived value cannot be forgotten
and cannot drift from the deployment it describes. Hardcoding `True` would
break the laptop, where the dev site speaks plain HTTP, the browser would
withhold the cookie, and login would fail with nothing on screen to explain it.

**Each cookie's `SameSite` is tightened to what that cookie is worth, and the
asymmetry is the point.** The session cookie is `Lax`: confirmation and
password-reset arrive as links in mail, and `Strict` sends no cookie on a
cross-site top-level navigation, so `Strict` would have broken the account
flows the moment it started working. The remember cookie stays `Strict`: it is
a credential, nothing depends on being remembered *on arrival*, and its whole
failure mode is that a visitor who followed a link logs in again.

**And `Strict` on the remember cookie is partly a stand-in, which this record
exists to say out loud.** The site has no site-wide CSRF protection: `Lax`
still sends a cookie on a cross-site top-level `GET`, and nothing here checks a
token on a route that is not a `FlaskForm`. An app cannot close that —
flask-security requires `CSRFProtect` before its own init, and apps install
after it — so it is the site's to fix or to leave. Until it is fixed, `Strict`
is carrying some of that weight.

## Consequences

**A reader can no longer trust `_wire` by reading it.** The file now mixes two
idioms on purpose, and the hazard it documents is general: every Flask-shipped
key `_wire` appears to set is suspect, and `MAX_CONTENT_LENGTH`,
`MAX_FORM_MEMORY_SIZE`, `MAX_FORM_PARTS` and `PREFERRED_URL_SCHEME` are all in
that class. **Verify a setting by reading it off a booted application, not out
of the source.** That is the general lesson here and it cost an afternoon's
survey to learn.

**A caller loses an override it never had.** The four cookie keys no longer
defer to `config_overrides`. Nothing in either suite sets them, so nothing
broke; a test that needs to vary them sets them after `create_app` returns.

**`Secure` reaches the deployed site for the first time**, so the first deploy
carrying this wants one manual check that login still works on staging. An
unrecognised `PODPACK_ENVIRONMENT` counts as not-local and therefore gets
`Secure`, matching podpack's own rule — a typo in that variable makes the site
stricter, not laxer, which is the right direction to fail in.

**`Strict` on the remember cookie is now a decision with a trigger.** When
site-wide CSRF protection lands, the defensive argument above weakens and
`Lax` becomes a reasonable reconsideration rather than a loosening for
symmetry's sake. Without this record that reasoning lived only in a commit
message, and the next person to notice the asymmetry would have tidied it away.

**Visitors arriving from a mail link are not remembered.** That is the accepted
cost. It is visible, it is self-correcting, and it is the right trade for the
one cookie that is worth a password.

## Alternatives considered

**Keep `setdefault` and fix the value.** Impossible, and this is the trap worth
recording: there is no value of `SESSION_COOKIE_SAMESITE` that `setdefault` can
install, because the key is always already there. The line was not wrong, it
was inert.

**`Strict` for both, as the dead line claimed.** Rejected on evidence rather
than taste: it would break registration confirmation and password reset, which
are this site's account feature (HW-0015). Had that line ever worked, the
account flows would have broken on the same day.

**`Lax` for both, for symmetry.** Rejected. Symmetry is not a security
argument, and the two cookies are not worth the same. The weaker rule should
not be applied to the stronger credential to make a config block read evenly.

**Compare against Flask's defaults and `setdefault` only where the value is
untouched**, preserving the override contract for these keys too. Rejected as
more machinery than the problem: it would hardcode knowledge of Flask's default
values, which is a dependency on another project's constants that nothing would
notice going stale.

**Set the cookie attributes per-response with `set_cookie`.** Rejected — the
session cookie is Flask's to emit, and the configuration is the supported way to
govern it. A per-response call would apply to cookies this site does not set.
