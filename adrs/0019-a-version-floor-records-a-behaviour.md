# HW-0019: A version floor records a behaviour this deployment depends on

**Status:** Accepted

**Date:** 2026-09-22

## Context

Most of what this site needs from podpack and its apps is not an API.

podpack 0.9.0b2 reads `PODPACK_PROXY_HOPS`; without it the site serves every
page perfectly and mails `http://` password-reset links. 0.9.0b3 unpacks a
restore inside the user namespace; below it a restore on Opalstack fails on
every file — *after* replacing `.env` and `secrets.env`, so the checkout is left
wearing the backup's identity and holding none of its data. podpack-qrcode 0.2.1
names an endpoint that does not exist, which podpack treats as a boot failure.

None of those changes a signature. Nothing but a version specifier can record
that this deployment depends on them, and a site that resolved an older release
would look entirely healthy until the day it mattered.

## Decision

Each podpack-family floor in `pyproject.toml` is the version carrying something
this deployment depends on — not merely the newest available — and the comment
beside it names the behaviour and what breaks below it. Floors move
deliberately, release by release, with the reason written down.

No upper bound is put on those floors: the lockfile already fixes what is
installed, so a ceiling would only forbid a future release without evidence
against it.

Pre-releases are opted into by naming one in the specifier rather than by a
global flag, because uv permits a pre-release only where the specifier asks for
one.

## Consequences

**The dependency list is the site's most compact operational record** — five
floors, each with a failure mode attached, in the file a reader opens first.

**It is maintained by hand, and the hand slips.** Of seven podpack floor moves,
three carry a real reason and four do not: two are "Update version." with an
empty body, one is "Fix mescallaneous bugs and tidy up docs.", and the current
move to 0.9.3 is an uncommitted working-tree edit with no message anywhere. The
rule above is what the site intends; these are the lapses, named so the record
is not read as a description of settled practice.

**A floor sometimes moves for a behaviour no page here exercises yet** — the
podpack-pages floor went to 0.3.4 to stop a resolve falling back to a version
that would lose the site's chrome on content trees still to come. That is the
rule working: the floor records a dependency, not a usage.

**The comment block has drifted from the specifier it sits above.** It still
documents only 0.9.0b2 and 0.9.0b3 and says "this opts podpack in and nothing
else", while the specifier names no pre-release at all and the lock holds none.
The rule survives; every current instance of it wants rewriting.

**The rule covers the podpack family only.** `werkzeug`, `flask`,
`psycopg2-binary`, `argon2-cffi`, `flask-mailman`, `flask-paranoid` and
`alembic` carry floors with no behavioural comment, and
`podpack-notebooks>=0.1.1` is explicitly "the app as installed here" — a floor
recording nothing.

**One unexplained ceiling remains**: `python-dotenv (>=1.0.1,<2.0.0)`, a
poetry-era leftover that no comment defends. The ceilings on `requires-python`
and on the build backend are ordinary and not at issue.

## Alternatives considered

**Leaving a floor where an older specifier already satisfied it.** Rejected: "a
floor is the only place that can say a deployment depends on behaviour rather
than on an API."

**Allowing pre-releases globally with `--prerelease=allow`.** Rejected after
measurement — the flag is not scoped per package, and it "pulled sqlalchemy
2.1.0b3 and wtforms 3.3.0b3 into a scratch venv".

**Pinning exact versions instead of floors.** Not a fork the record shows being
taken, but the argument against it is this record's own: the lock already fixes
what is installed, so a pin would say nothing new while losing the ability to
say *why* the version matters.
