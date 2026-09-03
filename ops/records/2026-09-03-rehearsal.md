# Rebuild rehearsal — 2026-09-03 (DR-1)

The first end-to-end `RESTORE` rehearsal where the restore and the running-site
verification met. Contrast rehearsal 1 ([`2026-08-23-rehearsal.md`](2026-08-23-rehearsal.md)),
which left "the two halves never met"; the defects it and rehearsals 2–4 found
are fixed, and this run produced the number every prior one lacked — a recovery
time.

**Host:** opal17 (the live staging host). **Mode:** `RESTORE`. Driven by hand;
live `os` stopped for the window, and `~/apps/os/site` with its `hostdata` left
untouched throughout — so the fallback was always `./scripts/up.sh` from the
canonical directory, and the drill's risk was bounded to the downtime.

## Configuration

    WEB_PORT=15055                 # the real port, so the proxy reaches it
    SITE_HOST=os.holdenweb.com
    SITE_DIR=holdenweb-staging     # scratch dir, beside the untouched live one
    BACKUP=~/backups/os-holdenweb-com/20260903T110502Z
                                   # 4 rows across 4 tables, alembic 150cf4618ef7

## Result

    == rebuilt in 1m 4s, and answering on https://os.holdenweb.com

- **Ordering gates fired in sequence:** init-storage → init-postgres → postgres
  *Healthy* → migrate (exited) → web. Which also proves `up.sh` resolved
  **docker-compose**, not the gate-ignoring `podman-compose` — the provider
  question was live the same day (backlog #31), and this is the interactive path
  coming out right.
- `healthz` 200 on `127.0.0.1:15055`; container reads `PODPACK_PROXY_HOPS=1`;
  `https://os.holdenweb.com/healthz` → 200 — the public address, the half that
  never closed before.
- Restore's own check: every table's row count matched `rowcounts.txt`.
- Integration suite from the laptop against the public URL: **16 passed** —
  including `test_submitting_the_login_form_does_not_error`, so login works on
  the rebuilt site (the flask-security and migration fixes hold through a
  restore), and the nav still resolves after the `/python` → 301 retirement.

**Recovery time: 1m 4s** — from `up.sh` to a public 200; the number to quote
when asked how long the site is down for a rebuild. Clone and restore dominated;
the site is tiny.

## Not covered here

- The password-reset mail beginning `https://` (rebuild.md 5.4, "the one that
  matters"). `PODPACK_PROXY_HOPS=1` in the container is strong evidence it will
  be, but a read of a real reset mail is the only proof, and was not done in this
  run.
- DNS cutover and continuity — a rebuild is downtime by design; `operations.md`
  §7 phase 2 is a separate, still-unrun procedure.

## Verdict

**DR-1 discharged.** `ops/rebuild.sh` taken end-to-end into a scratch deployment,
reaching HTTP 200 local and public with matching row counts and a green
integration suite. The documented recovery path works, and its cost is about a
minute of downtime.
