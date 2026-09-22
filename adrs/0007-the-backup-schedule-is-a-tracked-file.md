# HW-0007: The backup schedule is a tracked file, and each line carries its own environment

**Status:** Accepted

**Date:** 2026-09-22

## Context

The first scheduled backup on `opal17` failed at its own precondition.
`backup.log` and `verify.log` recorded "the web service is not running" at 03:17
and 04:23, while the containers had in fact been up for twenty hours
continuously.

Cron had not failed to run. It ran in a stripped environment where
`podman compose ps` could not see the running containers, so `backup.sh` and
`verify-backup.sh` refused — correctly — rather than writing a hollow backup.
Two gaps did it, both classic for rootless podman and neither present in an
interactive login shell: cron's `/usr/bin:/bin` `PATH` does not include
`$HOME/bin`, where the compose provider lives, and `XDG_RUNTIME_DIR` was unset,
so podman looked away from `/run/user/<uid>` and found no socket.

What made it hard to place at all was that nothing in the logs said when a run
had fired.

The schedule was already a tracked file by then — `ops/backup.cron` was
installed with `crontab ops/backup.cron` from its first version, and already
built its paths from `$HOME`. The incident did not establish that; it
established what the file has to carry.

## Decision

`ops/backup.cron` is tracked, installed with `crontab ops/backup.cron`, and
re-installed after any edit — the header says so in capitals, because crontab
keeps its own copy and does not read this one.

**Each line reconstructs the environment it needs, inline.** `PATH` and
`XDG_RUNTIME_DIR` are exported on the cron line itself rather than inherited
from cron or sourced from a profile. The header names what cannot be expressed
in the file at all: `loginctl enable-linger` as a one-off, and the
`DBUS_SESSION_BUS_ADDRESS` fallback if podman still cannot connect.

**Every run stamps its log** with an ISO-8601 UTC header, whose percent signs
are backslash-escaped because cron turns an unescaped `%` into a newline.

**No username is hard-coded**: paths come from `$HOME`, and `SITE_NAME` — hence
`BACKUP_ROOT` — is read from the host's `.env`.

## Consequences

**The reason a 3am job works is in the repository**, not in a shell profile on a
host nobody logs into. The schedule is reviewable in a diff and reproducible on
a second host: production is this file with one directory changed.

**The logs now say when each run fired**, which is precisely what was missing
when the original failure had to be diagnosed.

**The exports are repeated on every line.** That duplication is the price of not
having a wrapper, and it is the shape most likely to drift when a line is added.

**The file and the installed crontab can disagree silently.** Nothing checks
that what is running on `opal17` matches what is committed here; the only way to
find out is `tail -n 20 ~/backups/verify.log` on the host. `loginctl
enable-linger` remains an undetectable out-of-band prerequisite, and so does the
`containers.conf` provider pin written by hand on `opal17` on 2026-09-03 —
backlog item 31 is the durable fix for that one, in podpack.

**This is the backup schedule's decision, not a site-wide policy**, and two
counter-examples in the same repository say so. The five-minutely `/healthz`
cron drafted in `operations.md` §18 is a fenced block in prose that sources
`. ./.env` rather than exporting inline, and is not installed. The laptop's pull
schedule (HW-0006) is a suggested line in a script header with an absolute home
directory in it. Bringing those into line with this record is work nobody has
done.

## Alternatives considered

**Relying on the login shell's environment.** This is what produced the
incident: it works interactively and fails at 03:17, which is the worst
available combination.

**A wrapper script that sources the profile before calling `backup.sh`.**
Rejected: it moves the same problem one level down and out of sight, so the next
diagnosis starts one indirection further from the cause.

**Leaving the crontab as the operator's own artefact, edited with `crontab -e`.**
Rejected in favour of a tracked file, so the schedule is reviewable, diffable
and reproducible — at the cost of the re-install step, which is the one thing a
`crontab -e` workflow gets right for free.
