# Backlog: findings awaiting an issue

*Raised 2026-08-19, while writing [`operations.md`](../operations.md). Held
here for triage into GitHub Issues — both `holdenweb/holdenweb-com` and
`holdenweb/podpack` have Issues enabled and are currently empty, so nothing has
been filed yet.*

Each item names the repository it belongs to, the evidence that it is real, and
what fixing it involves. **Tier 1** was found while writing the playbook;
**Tier 2** is the standing known-gaps register from
[`operations.md` §17](../operations.md), recorded here so the two lists do not
drift apart.

| # | Repo | Item | Kind |
| --- | --- | --- | --- |
| 1 | holdenweb-com | `MAIL_PASSWORD` still at the example value in production | **operational** |
| 4 | holdenweb-com | Reset links go out as `http://`, carrying the token in clear | **security** |
| 5 | holdenweb-com | `PROJECT-BRIEF.md` names the profile `dbport`; it is `postgres-port` | docs |
| 6 | holdenweb-com | `README.md` stale on dependency sources | docs |
| 7 | holdenweb-com | `environment = "local"` in the production config | cosmetic |
| 8 | holdenweb-com | Nothing polls `/healthz` | gap |
| 9 | holdenweb-com | No log rotation | gap |
| 10 | holdenweb-com | No maintenance page | gap |
| 11 | holdenweb-com | Migrations have no tested downgrade | gap |
| 13 | holdenweb-com | Only the front page renders the site navigation | correctness |

*Numbers are stable identifiers, so a gap means an item was struck rather than
renumbered. Struck so far: **2** (substrate now at podpack 0.9.0b1, 2026-08-20),
**3** (`pp-pdf` now carries one `r*` tag, `r0.2.0`, matching its version, on
`origin` as well as locally, verified 2026-08-21), and **12** (ADR-0027's stale
profile name, 2026-08-20).*

---

## Tier 1 — found 2026-08-19

### 1. `MAIL_PASSWORD` is still the example value in production

**Repo:** holdenweb-com — **the only item here that means something is broken
right now.**

*Evidence.* Confirmed by inspection of the host earlier in the same session;
`config/app.toml:16` declares `MAIL_PASSWORD` under `[site] secrets`, so the
site boots — the check is that the variable is *set*, not that it is correct.

*Why it matters.* Password reset and every other outbound mail fails
authentication. The site gives no sign of it until a visitor asks for a reset,
which is precisely the case flask-security answers generically.

*Fix.* [`operations.md` §8](../operations.md): set the real App Password in
`secrets.env` on the host, `podman compose up -d web`, then
`podman compose exec web flask --app holdenweb mail check`, which authenticates
for real and exits non-zero on failure.

### 4. Reset links go out as `http://`, and `base_url` is not the fix

**Repo:** podpack — **not this site**, which is the correction. This item said
until 2026-08-21 that the fix was `base_url = "https://holdenweb.com"`. It was
wrong twice over, and both errors came from reading a setting's name instead of
following what actually builds the link.

*Evidence.* Steve asked the live site at `os.holdenweb.com` for a password
reset and received a mail containing `http://os.holdenweb.com/reset/<token>`.
Reproduced against this site's own factory: with `X-Forwarded-Proto: https`
present, `url_for(..., _external=True)` still returns an `http://` URL, because
there is no `ProxyFix` in the stack and `PREFERRED_URL_SCHEME` does not apply
inside a request context. gunicorn is started from `Containerfile:98` with no
`--forwarded-allow-ips`, so it defaults to `127.0.0.1` — which under rootless
podman is not the address the port forwarder presents, so it drops the header
before Flask sees it.

*Why `base_url` was never the fix.* It feeds exactly one function,
`podpack.absolute_url`, and **nothing calls it** — not this site, not podpack.
Flask-Security builds the reset link at `recoverable.py:32` with
`url_for_security(..., _external=True)`, which is plain Flask `url_for`.

*Why the domain is not the fix either.* The host in that link was already
correct: nginx passes `Host` through, and the URL is built inside the request
that asked for it. Writing `holdenweb.com` into a committed config file would
have been actively wrong — the site answers on `os.holdenweb.com`, the binding
belongs to Opalstack's control panel, and it can change without a redeploy.

*Why it matters.* nginx answers `http://` with a 301 to `https` and sends HSTS
for a year, so the link works and has always worked. HSTS protects only a
browser that has visited before, so a recipient opening the mail on a fresh
device sends the reset token in the path of a cleartext request before the
redirect.

*Fix.* Done in podpack as `PODPACK_PROXY_HOPS` (ADR-0036, commit `fd26a12`):
`ProxyFix` applied when the host declares how many proxies are in front of it.
An environment variable rather than an `app.toml` key because the same
committed config runs on an unproxied laptop and a proxied host.

**Still to do here**, and it needs a podpack release first — the fix is
committed but unpushed and unpublished:

1. Release podpack past 0.9.0b1 and take it here.
2. Add `PODPACK_PROXY_HOPS=1` to `secrets.env`'s neighbour `.env` on the
   production host, and `podman compose up -d web`.
3. Confirm with `/_status`, which now reports `proxy.forwarded_proto` and
   `proxy.scheme` — no need to mail anybody a reset link to check.

### 5. `PROJECT-BRIEF.md` names the database-port profile `dbport`

**Repo:** holdenweb-com

*Evidence.* `PROJECT-BRIEF.md:96` gives
`podman compose --profile dbport up -d dbport`. `compose.postgres.yaml` defines
the service as `postgres-port` with `profiles: ["postgres-port"]`. The brief
predates the rename.

*Why it matters.* The command as written does nothing and says nothing useful,
in a document whose purpose is briefing somebody who does not already know.

*Fix.* One-line correction, both occurrences on that line.

### 6. `README.md` is stale on dependency sources

**Repo:** holdenweb-com

*Evidence.* `README.md:64` — "building currently requires the three
path-sourced dependencies (podpack, podpack-pages, podpack-qrcode, pp-pdf) to be
repointed at git remotes and re-locked". They are already git-sourced
(`pyproject.toml:34-38`), and there are four of them, not three.

*Why it matters.* It describes a blocker that no longer exists, and miscounts
what it lists — so a reader either does unnecessary work or stops trusting the
document.

*Fix.* Delete the note. It becomes wrong again shortly, when the git sources
are retired in favour of PyPI version specs.

### 7. `environment = "local"` in the production configuration

**Repo:** holdenweb-com

*Evidence.* `config/app.toml:6`. The file is bind-mounted read-only from git,
so production reads the same value the laptop does. podpack reads `environment`
and does nothing with it.

*Why it matters.* Nothing is broken. But `/_status` on the production host says
the site thinks it is local, and the next person to read it will spend time
establishing that this is harmless.

*Fix.* Either make the value meaningful (per-host, which means it stops being a
committed file's business) or remove it. Removing it is the smaller lie.

---

## Tier 2 — standing gaps, from `operations.md` §17

### 8. Nothing polls `/healthz`

**Repo:** holdenweb-com. The endpoint already answers
`{"database":"ok","status":"ok"}` without authentication — it is what the
container healthcheck uses — so external monitoring has something to ask and
nothing asks it. Today the site being down is noticed by a person. *(Note the
name: `/healthz`, no underscore, unlike `/_status`.)*

### 9. No log rotation

**Repo:** holdenweb-com. `hostlogs/` grows without limit; the laptop lab's
PostgreSQL log reached 19 MB against 62 MB of data. Nothing prunes it.

### 10. No maintenance page

**Repo:** holdenweb-com. Stopping `web` yields a 502 from nginx. A planned
window currently has to be handled at the front end, by pointing the Nginx
Proxy Port at a holding page — which works, but is not written down anywhere as
a procedure and has never been rehearsed.

### 11. Migrations have no tested downgrade

**Repo:** holdenweb-com. alembic has the direction, but the site's revisions are
not written or tested for it, so the rollback plan for any release carrying a
schema change is *restore last night's dump*. That is workable and is what
[`operations.md` §15](../operations.md) says — it is also the reason the backup
before a schema change is the one that matters most.

---

## Raised since — 2026-08-21

### 13. Only the front page renders the site navigation

**Repo:** holdenweb-com

*Evidence.* `sections` — the navigation podpack assembles from the installed
apps and puts in front of every template — is referenced in exactly one of this
site's templates, `src/holdenweb/templates/index.html:14`. In both
`templates/base.html:60` and `templates/security/base.html:59` the
`{% block navbar %}` is present and **empty**. podpack's own fallback
`base.html:32` does render it.

*Why it matters.* A site that writes no `base.html` gets the navigation; this
site wrote one and silently lost it. So every page other than `/` — the two
`pp_pdf` forms, everything under `/pages`, all the flask-security pages, and
404 — offers no route to the other installed apps. The logo links to `/` and
the bluebar handles login, so nothing is a dead end, but installing an app
currently adds it to one page's menu rather than to the site's.

*Fix.* Render `sections` in the `navbar` block, with podpack's
`src/podpack/templates/base.html:32` as the reference for markup and endpoint
handling.

Two things fall out of the same edit, and are the reason it is not a one-line
change:

- **`security/base.html` is a drifted copy-paste fork of `base.html`,** not a
  child of it. It carries Bootstrap 4.1.3 from stackpath where the site
  otherwise loads 4.6.1 from cdnjs, and no popper — so the login, register and
  password-reset pages already render against a different framework version
  than the rest of the site. Editing one base will not reach them.
- **`templates/security/base.saved.html` is a leftover** beside it, and wants
  deleting or explaining.


---

## Filing these

Nothing here has been filed: creating issues is a change to a shared, public
record, and that is the account holder's call rather than a side effect of
writing a document. When the time comes, each section above is already a title
and a body:

```bash
gh issue create --repo holdenweb/holdenweb-com \
  --title "MAIL_PASSWORD is still the example value in production" \
  --body-file - <<'EOF'
...paste the section...
EOF
```

Delete an item from this file once its issue exists, so that this list is
always what is *not* yet tracked.
