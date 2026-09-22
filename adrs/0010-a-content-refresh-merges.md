# HW-0010: A content refresh merges, and removal must be asked for

**Status:** Accepted

**Date:** 2026-09-22

## Context

Content is not in git (HW-0008), so a content mistake cannot be undone by
reverting a commit. The served tree is the live copy, and for the prose `pages`
area it is the only copy anywhere. That changes what a refresh is allowed to do
by default.

The estate had already learned the other half of this the hard way, one layer
down. `scripts/restore.sh` carries the lesson in its header, and
`refresh-content.sh` cites it: "an unpack that only ever adds leaves files
deleted on purpose sitting beside the new ones, producing a state that never
existed anywhere." So neither behaviour is safe in general — an additive refresh
produces a tree nobody built, and a replacing refresh from an incomplete source
deletes a visitor's content. One of those is recoverable.

## Decision

**A refresh merges.** Files are added and overwritten; anything already on the
host that the source does not have is left alone. `--mirror` removes the
destination first, and must be asked for by name.

**A mirror is confirmed by typing the word**, in both scripts, whenever a
terminal is there to answer: `Type 'mirror' to go on`.

**The confirmation is gated on a tty; the removal is not.** `push-content.sh`
drives `refresh-content.sh` over ssh with no pty, so an ungated `read` gets EOF
and aborts a mirror that was already confirmed on the laptop.

**`--dry-run` prints the plan and changes nothing.** In `refresh-content.sh` it
prints the file counts at both ends and then the exact commands it would run,
stopping at the line where writing would begin.

## Consequences

**The default is the safe one, and the dangerous one costs a word.** That is
the whole shape of the decision.

**A mirror has a window in which the tree does not exist.** It is `rm -rf`
followed by `mkdir -p` and `cp -R`, not an `rsync --delete`, so for the duration
of the copy the app serves 404 for everything in that tree — 721 files' worth
for the blog. Nobody has been bitten by it; it is recorded because it is the
kind of thing a reader would assume had been handled.

**The tty gate is exactly the right size, and was not obvious.** Putting
`&& [ -t 0 ]` on the outer `if` is the tidier-looking edit and is wrong: it
would skip the removal too, so `--mirror` would quietly behave as a merge and
leave behind precisely the state `restore.sh`'s header warns about — and it
would look like success. The comment in the script says so, because the next
person to read it will have the same idea.

**The preview is not symmetric.** `refresh-content.sh --dry-run` prints counts
and a plan; `push-content.sh --dry-run` echoes the three commands it would run
and exits before it contacts the host, so it shows no counts. `just <area>
staging --dry-run` therefore gets the plan without the numbers.

**It took three weeks to find the gate.** The prompt shipped with the script on
2026-08-30 with no tty test, and every non-interactive mirror aborted until
2026-09-22. The symptom was a mirror that had been confirmed on the laptop
failing silently on the host, which reads as an ssh problem rather than a
`read`.

## Alternatives considered

**Making `--mirror` the default, so the host always matches the build.**
Rejected: "an incomplete source with `--mirror` deletes a visitor's content."
The failure mode of the merge default is a stale file; the failure mode of the
mirror default is a deletion with no undo.

**Gating the whole `--mirror` branch on a tty** — the obvious tidy-up. Rejected
as above: it converts a requested mirror into a silent merge.

**Dropping the confirmation entirely**, on the grounds that `--mirror` is
already explicit. Rejected because the flag is typed once and the consequence is
per-tree: the operator asking for a mirror of `pybooks` does not necessarily
know that the staged directory is half-built.

**`rsync --delete` on the host instead of `rm -rf` plus `cp -R`**, which would
remove the 404 window. Not chosen, and not for a recorded reason — the copy runs
inside `podman unshare`, where the tools available are whatever the host has.
Worth revisiting if the window ever matters.
