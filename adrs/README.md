# Architectural decision records

> **Record · why this site is the way it is.** Immutable once accepted;
> superseded rather than edited.

Why holdenweb.com is as it is. Each record states the pressure that forced a
choice, what we decided, what it cost, and what else was on the table — that
last section being the one that stops a decision getting reproposed in six
months.

**These are numbered `HW-nnnn`, and podpack's are `ADR-nnnn`.** This
repository's prose already cites podpack's records by bare number, so a second
sequence spelled the same way would collide exactly where somebody is trying to
follow a reference. A record here never restates one of podpack's; where it
depends on one, it cites it.

Start from [the template](0000-template.md), which also sets out what belongs
here as against in `README.md`, `PROJECT-BRIEF.md` or `operations.md`.

These were written on 2026-09-22, reconstructed from the commits, the backlog
and the operational documents that carry the reasoning. The decisions themselves
were taken over the preceding seven weeks, so a record's **Date** is when it was
written, not when the choice was made.

## Deployment

| | |
| --- | --- |
| [HW-0001](0001-a-deploy-target-is-a-git-remote.md) | **A deploy target is a git remote.** Its scp-style URL is the whole of its definition, and a missing one is an error that prints the fix. Scoped to the two push tools; the pull direction still guesses. |
| [HW-0002](0002-a-revision-arrives-by-push-into-a-live-worktree.md) | ~~**A revision arrives by push into a live worktree.**~~ *Superseded by HW-0034* — the push had a hole that reported success: with HEAD detached on the host it updated nothing and the health check still passed. |
| [HW-0034](0034-the-host-fetches-the-commit-it-is-told-to-run.md) | **The host fetches the commit it is told to run.** Published to a per-target deploy ref, fetched and checked out detached on the host, then rebuilt — and the deploy fails unless the container reports the commit it was given. |
| [HW-0003](0003-the-gating-extends-past-compose.md) | **The gating extends past compose, to the laptop and to the public URL.** Both ends refuse rather than degrade. Production is not gated yet, and the record says so. |

## Availability

| | |
| --- | --- |
| [HW-0004](0004-three-checks-at-three-distances.md) | **Three checks at three distances, and the standing one is rented.** Inside the container, at deploy time from the laptop, and every five minutes from the internet. It asks `/healthz`, because the front page answers 200 straight through a database outage. |
| [HW-0005](0005-a-backup-is-believed-only-after-a-restore.md) | **A backup is believed only after a restore, and "occasionally" is a calendar.** podpack supplies the principle; this site fills in the cadence, the triggers and the written-up rehearsals. |
| [HW-0006](0006-the-off-machine-copy-is-a-laptop-mirror.md) | **The off-machine copy is a laptop mirror, pulled by hand.** The only other machine in the estate. Its recovery point is the interval between runs — 20 days, as at 2026-09-22. |
| [HW-0007](0007-the-backup-schedule-is-a-tracked-file.md) | **The backup schedule is a tracked file, and each line carries its own environment.** Cron ran in a stripped environment and the jobs refused rather than writing a hollow backup. |

## Content

| | |
| --- | --- |
| [HW-0008](0008-content-is-delivered-not-committed.md) | **Content is delivered, not committed.** 879 files that never pass through git and never ride a deploy. Both alternatives were lived through before this one. |
| [HW-0009](0009-no-generator-runs-on-the-serving-host.md) | **No generator runs on the serving host.** The laptop builds, the host receives HTML. Publication needs that one laptop. |
| [HW-0010](0010-a-content-refresh-merges.md) | **A content refresh merges, and removal must be asked for.** `--mirror` is typed out in words; the confirmation is gated on a tty and the removal deliberately is not. |

## What this site is made of

| | |
| --- | --- |
| [HW-0011](0011-every-feature-that-can-be-an-app-leaves.md) | **Every feature that can be a podpack app leaves this repository.** Seven apps, six of them elsewhere. What stays is chrome, addresses, and the extensions the site owns. |
| [HW-0012](0012-retired-addresses-keep-resolving.md) | **Retired content addresses keep resolving, and the redirect belongs to the site.** Including routes registered inside another app's mount point. A 301 is a promise. |
| [HW-0013](0013-the-chrome-is-the-sites-and-reaches-other-peoples-pages.md) | **The chrome is the site's, and it reaches other people's pages by the shortest hook.** No framework; style an app's class names rather than fork its template. The `pdf` forms are the recorded exception. |
| [HW-0014](0014-a-mail-failure-is-reported-to-the-visitor.md) | **A mail failure is reported to the visitor, in a sentence they can act on.** podpack supplies the hook; what the failure says is the site's. |

## Security

| | |
| --- | --- |
| [HW-0015](0015-sign-up-is-public-and-confers-no-privilege.md) | **Sign-up is public, gated by email confirmation, and confers no privilege.** Closed for three days in September after the site was found open, then reopened with the gate that was actually missing. |
| [HW-0016](0016-the-config-report-is-operator-only-and-redacted.md) | **The config report is operator-only, and redacts its values regardless of who is reading.** The guard slipped once; that is why there are two mechanisms. 71 of 363 keys redact, of which about five are secret. |
| [HW-0017](0017-a-rotation-ends-in-revocation.md) | **A rotation ends in revocation, and the new value never reaches a command line.** A rotated-but-not-revoked credential is still live. |

## Dependencies and the framework

| | |
| --- | --- |
| [HW-0018](0018-the-committed-lock-resolves-everything-from-pypi.md) | **The committed lock resolves everything from PyPI.** Path sources broke every environment but one laptop; git sources followed branches silently. A path source is now pasted in and taken back out. |
| [HW-0019](0019-a-version-floor-records-a-behaviour.md) | **A version floor records a behaviour this deployment depends on.** Not an API — a proxy hop count, a restore that works on Linux. The rule the site intends, with its lapses named. |
| [HW-0020](0020-a-managed-file-may-diverge-when-the-default-must-serve-other-sites.md) | **A managed substrate file may diverge when podpack's default has to serve other sites.** The git layer is the first such edit. Everything else goes upstream, as the CDPATH fix did. |
| [HW-0032](0032-a-gap-in-the-framework-is-fixed-in-the-framework.md) | **A gap in the framework is fixed in the framework, and the floor is the receipt.** Write the smallest local version, file it upstream, delete it when the release lands. Two worked examples, closed in hours and in days. |
| [HW-0033](0033-the-framework-arrives-on-two-tracks.md) | **The framework arrives on two tracks, and only the check knows whether they are in step.** The library moves by `uv lock`, the substrate by a deliberate upgrade. They are out of step right now, and `--check` still exits 0. |

## Records and working practice

| | |
| --- | --- |
| [HW-0021](0021-a-document-declares-its-kind-and-its-reader.md) | **A document declares its kind and its reader.** A reference, a procedure and a record fail differently. Applied in one sweep and not since — which the record says. |
| [HW-0022](0022-one-place-per-fact.md) | **One place per fact, and a command instead of an answer.** A duplicated procedure cost an evening in the first rehearsal. |
| [HW-0023](0023-the-backlog-is-append-only.md) | **The backlog is append-only, and what is still open is derived from it.** The derivation rules live in the script, so closing an item needs no maintenance. |
| [HW-0024](0024-one-backlog-for-every-repository.md) | **One backlog for every repository, and filing upstream is a separate act.** Four destination repositories, and nothing filed on any of them. |
| [HW-0025](0025-a-procedure-that-has-not-been-run-says-so.md) | **A claim that rests on having run something says whether it was run.** ✅ and ⚠️ in the reference; expected output at every step in the procedures. |
| [HW-0026](0026-the-message-catalogue-is-one-data-file.md) | **The message catalogue is one data file and two generated views.** Both committed, because the host has no toolchain at three in the morning. |

## The database, and the two suites

| | |
| --- | --- |
| [HW-0027](0027-the-fast-loop-runs-on-sqlite.md) | **The fast loop runs on SQLite; PostgreSQL authors the migrations and serves.** podpack's seeded `dev.env.example` argues against SQLite and is right — about authoring. Nothing enforces the split but a comment and this record. |
| [HW-0028](0028-one-migration-history-re-parented.md) | **One migration history, re-parented so that it serves a database older than itself.** The root was written after the baseline and put beneath it; the converging alters ask the schema rather than assuming it. |
| [HW-0029](0029-two-suites-and-ci-is-advisory.md) | **Two suites, and CI is advisory.** One proves the code in seconds, the other drives a browser at a real deployment. The gate that can stop a bad revision is on the target, not on the published branch. |

## Mail, and the edge

| | |
| --- | --- |
| [HW-0030](0030-the-site-sends-as-a-person.md) | **The site sends as a person, through a consumer account.** Identity depends on one Gmail App Password; everything else is a code-level default a host can override. |
| [HW-0031](0031-the-public-edge-is-rented.md) | **The public edge is rented.** Loopback in, Opalstack's proxy and TLS out. Believing `X-Forwarded-Proto` is a promise about the topology. |
