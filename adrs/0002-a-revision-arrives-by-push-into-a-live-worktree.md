# HW-0002: A revision arrives by push into a live worktree, and the rebuild is a separate step

**Status:** Superseded by [HW-0034](0034-the-host-fetches-the-commit-it-is-told-to-run.md)

**Date:** 2026-09-22

## Context

podpack ADR-0017 makes the image carry the commit it was built from, so that
`/_status` can answer "is the container running the code I am looking at?"
exactly rather than by comparing timestamps. That only works if the host holds a
real git checkout at the deployed commit, because the stamp is taken *on the
host*, by `scripts/up.sh`, from whatever tree it is standing in:

```
if sha="$(git rev-parse --short HEAD 2>/dev/null)"; then
    git diff --quiet HEAD 2>/dev/null || sha="${sha}-dirty"
else
    sha="unknown"
fi
```

The `else` branch is where a tree that arrived by any other means lands. So the
transport was forced by the stamp: podpack decided that the image records its
commit, and that decides how the code has to travel.

The practice came before the tooling. `git push main main` followed by a manual
`up.sh` was already how this site was deployed; what `ops/deploy.sh` settled, on
2026-09-01, was making it one guarded command with the remote URL as the single
source of truth for host and path (HW-0001).

## Decision

`ops/deploy.sh <target>` pushes the commit into a live worktree and then, as a
separate command, rebuilds it there:

```
git push <target> HEAD:main
ssh <host> "cd ~/<path> && ./scripts/up.sh"
```

The receiving checkout is configured with `receive.denyCurrentBranch=updateInstead`,
so the working tree updates in place on the push. There is no bare repository
and no `post-receive` hook: the push delivers, and a human runs the rebuild
knowing they are about to.

## Consequences

**`/_status` reports a real short sha on every deployment**, and a `-dirty`
suffix means something rather than decorating everything.

**The operator is present for the health check.** Because the push does not
trigger the rebuild, the person who deployed is still at the keyboard when
`ops/poll-health.sh` reports (HW-0003). This is the property a `post-receive`
hook would have cost, and it is the reason this record does not have one — the
reasoning is written here rather than quoted, because `operations.md` records
only that the question was settled, not why.

**Work done on the host can block the next deploy**, which is the distinctive
cost of pushing into a live worktree, and `ops/MESSAGES.md` carries all three
diagnosed forms of it: `denyCurrentBranch` before the host is configured, a
non-fast-forward "common when a deploy host committed a config edit", and
`updateInstead` refusing "when the server worktree is dirty or a push would
overwrite untracked files ... Config edits made in-place on the deploy checkout
are the usual culprit."

**Rolling back is `git revert` and the same command — for a code-only
release.** `operations.md` is explicit that this does not extend to schema:
"alembic has the `downgrade` direction, but the site's revisions are not written
or tested for it. If a release includes a migration, the rollback plan is
*restore last night's dump*."

**The rebuild runs in a non-login ssh shell**, whose `PATH` need not include
`~/bin` where the compose provider lives. That is how a deploy could silently
resolve `podman-compose` instead and skip the ordering gates. `opal17` is
covered by a hand-written `containers.conf` pin; backlog item 31 is the durable
fix, in podpack rather than here.

The sibling layout of `data` and `logs` beside `site` — rather than inside it —
belongs to podpack, not to this decision: `scripts/prepare-host-dirs.sh` refuses
a `HOST_DATA_DIR` or `HOST_LOG_DIR` that resolves inside the checkout for any
non-local `PODPACK_ENVIRONMENT`. It is a constraint this site inherits, and a
welcome one given what a `git clean -fdx` in a live worktree would otherwise
reach.

## Alternatives considered

**rsync the tree.** Rejected explicitly, and the reason is mechanical rather
than aesthetic: "an rsync'd tree has no HEAD and stamps `unknown`", which
silently converts podpack ADR-0017's exact answer into no answer at all.

**A bare repository with a `post-receive` hook that rebuilds.** Recorded as
settled once the question was asked. It would make a push *be* a deployment,
which is attractive until the health check fails and the person who pushed has
already moved on. The two-step form keeps the operator in the loop for the one
moment that matters.

**Building on the laptop and shipping an image.** Never seriously on the table
here: it would need a registry, and the rebuild is six seconds on the host
against a warm layer cache (podpack ADR-0012, ADR-0017).
