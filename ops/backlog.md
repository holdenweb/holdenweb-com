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
| 2 | holdenweb-com | Substrate pinned at podpack 0.7.0; 0.8.0 is published | operational |
| 3 | pp-pdf | 29 inherited `r*` tags will fire the publish workflow | release hazard |
| 4 | holdenweb-com | `base_url` unset, so absolute URLs come from the request | correctness |
| 5 | holdenweb-com | `PROJECT-BRIEF.md` names the profile `dbport`; it is `postgres-port` | docs |
| 6 | holdenweb-com | `README.md` stale on dependency sources | docs |
| 7 | holdenweb-com | `environment = "local"` in the production config | cosmetic |
| 8 | holdenweb-com | Nothing polls `/healthz` | gap |
| 9 | holdenweb-com | No log rotation | gap |
| 10 | holdenweb-com | No maintenance page | gap |
| 11 | holdenweb-com | Migrations have no tested downgrade | gap |
| 12 | podpack | ADR-0027 still calls the port profile `dbport` | docs |

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

### 2. The substrate is pinned at podpack 0.7.0

**Repo:** holdenweb-com

*Evidence.* `substrate.json:170` — `"podpack_version": "0.7.0"`; the installed
podpack in this checkout is also 0.7.0. podpack 0.8.0 is on PyPI.

*Why it matters.* Three things arrived in 0.7.1–0.8.0 that this site does not
have. `scripts/configure-host.py` is the one that bites: the restore procedure
in [`operations.md` §6](../operations.md) depends on it, so the documented
restore cannot currently be followed on this site as it stands. Also missing:
the `configparser` fix that survives a `%` in a database password, the warning
about `$` in a value, and applying a substrate from an artefact.

*Fix.* `uv lock --upgrade-package podpack --refresh-package podpack`, `uv sync`,
`uv run podpack substrate status`, `uv run podpack substrate upgrade`; review any
`.new` conflicts, commit, deploy.

### 3. `pp-pdf` carries 29 inherited release tags

**Repo:** pp-pdf

*Evidence.* 29 tags matching `r*`, from `r0.10.0` to `r1.6.0`, inherited when
the package was split out of holdenweb.com. Its own version is `0.2.0`. The
publish workflow triggers on `.github/workflows/publish.yml:22` —
`tags: ["r*"]`.

*Why it matters.* A `git push --tags` in that repository fires the publish
workflow 29 times. Each run fails its tag-versus-`pyproject` agreement check
rather than publishing anything wrong, so this is noise and wasted CI rather
than a data hazard — but it is 29 red crosses and a plausible reason to start
ignoring the workflow's results.

*Fix.* Either delete the inherited tags from the remote once it is certain
nothing references them, or narrow the trigger to a pattern the inherited tags
cannot match. Until then: **push named release tags, never `--tags`.**

### 4. `base_url` is not set

**Repo:** holdenweb-com

*Evidence.* `config/app.toml` has no `base_url` under `[site]`.
`podpack.urls.base_url()` returns `None`, so `absolute_url()` falls back to the
request.

*Why it matters.* Absolute URLs — password-reset and confirmation links among
them — are then built from whatever the request carried. That is correct only
while the proxy passes host and scheme faithfully; a mis-set
`X-Forwarded-Proto` produces `http://` links to an `https://` site, and the
symptom appears in somebody's inbox rather than in a log.

*Fix.* Set `base_url = "https://holdenweb.com"` — the public URL, **no port**.
podpack refuses to boot on a `base_url` it cannot join to, so a typo fails
loudly.

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

### 12. ADR-0027 still calls the port profile `dbport`

**Repo:** podpack

*Evidence.* Three occurrences in
`adrs/0027-the-database-port-is-published-only-on-request.md` and one in the
ADR index. `compose.postgres.yaml` has defined it as `postgres-port` since the
overlay split (ADR-0028).

*Why it matters.* The same staleness as item 5, in the document a reader would
consult to understand *why* the port is unpublished -- and the command it gives
does nothing.

*Fix.* An ADR records what was decided when, so the body is arguably history.
The index summary is navigation and is simply wrong. Decide which, then fix
that one.

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
