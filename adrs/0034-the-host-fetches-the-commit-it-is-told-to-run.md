# HW-0034: The host fetches the commit it is told to run

**Status:** Accepted

**Date:** 2026-09-23

**Supersedes:** [HW-0002](0002-a-revision-arrives-by-push-into-a-live-worktree.md)

## Context

HW-0002 had the laptop push into a live worktree on the host, with
`receive.denyCurrentBranch=updateInstead` making the push update the working
tree. It worked, and its reasoning about the commit stamp was sound. Two things
were wrong with it.

**It had a hole, and the hole reported success.** `updateInstead` only updates
the tree when the pushed ref is the *checked-out branch*. With HEAD detached on
the host, the push is accepted as an ordinary ref update, the working tree is
never touched, `scripts/up.sh` rebuilds the **old** commit, and
`ops/poll-health.sh` passes — because it asserts `"status":"ok"` and never asks
which commit is running. A green deploy that deployed nothing. This is not
hypothetical: `scripts/restore.sh` tells an operator to run `git checkout
<commit>` on the host, which is exactly how HEAD becomes detached.

**Its cost was three failure modes, all from one cause.** The message catalogue
carried `git-denycurrentbranch`, `git-updateinstead-dirty` and
`git-non-fast-forward` — every one of them a consequence of the host being a git
working tree that *receives pushes* and can acquire commits of its own.

Two facts made the alternative cheap. `up.sh` derives its stamp with
`git rev-parse --short HEAD`, which does not care whether HEAD is attached — so
HW-0002's stated reason for the transport (podpack ADR-0017's stamp) never
required a *branch*, only a real checkout at the deployed commit. And
`ops/rebuild.sh` already clones from GitHub **on the host** during disaster
recovery, so fetching there is a proven path rather than a new dependency.

## Decision

The host fetches the commit it is told to run.

`ops/deploy.sh <target>` publishes the commit to a per-target deploy ref and
then, in one ssh, has the host fetch it, check it out and rebuild:

```
git push --force-with-lease origin HEAD:refs/heads/deploy/<target>
ssh <host> "cd ~/<path> && git fetch --prune origin \
            && git checkout --detach <full-sha> && ./scripts/up.sh"
```

**The checkout is detached, and that is now the normal state of a deploy
checkout.** Every script that reads git here (`up.sh`, `backup.sh`,
`restore.sh`, `verify-backup.sh`) uses `rev-parse HEAD` or equivalent; none
reads a branch name.

**`checkout --detach`, not `checkout -f` or `reset --hard`.** It *refuses* when
host edits or untracked files would be overwritten. HW-0003's principle survives
the change of transport: the failure mode moves from a refusing push to a
refusing checkout.

**The deploy ref is not `main`**, which is what keeps unpublished work
deployable. A commit reaches staging without being merged; it is merely
published, on a ref nothing else reads.

**After the health check, the deploy asks the container which commit it is
running** — `podman compose exec -T web printenv PODPACK_BUILD_COMMIT` — and
fails unless it is the commit just deployed.

`receive.denyCurrentBranch` becomes inert and is unset when a host is migrated.
The target remains a git remote and nothing is pushed to it: HW-0001 stands, and
narrows to what it always really was, an address book that `ops/push-content.sh`
also reads. The GitHub URL is deliberately not added to the laptop's side — the
host fetches from its own `origin`, set once when its checkout is created, so
that fact keeps one home (HW-0022).

## Consequences

**A deploy that changes nothing can no longer report success.** That is the
point, and it is worth more than the transport change: the assertion would have
caught the old hole too, and it catches every future variant of "the rebuild did
not take".

**Three catalogue entries retire and three replace them.**
`git-denycurrentbranch` and `git-updateinstead-dirty` describe a push that no
longer happens. In their place: a host-side fetch that cannot authenticate, a
checkout refusing on a dirty host tree, and the build-commit assertion failing.

**The host now needs to reach GitHub, with a credential at rest.** A
passphraseless, read-only deploy key scoped to this repository — passphraseless
because `deploy.sh`'s fetch runs over ssh with no tty and no agent, read-only and
per-repository so that a compromised host cannot push anywhere, and in
particular cannot push an `r*` tag to an app repository and thereby publish to
PyPI. Agent forwarding was rejected for the same reason: it would lend the
laptop's agent, which holds the account key, to the host on every deploy.

**Deployment now depends on GitHub being up.** Previously a deploy needed only
the laptop and the host. This is a real reduction in independence, accepted
because the alternative was a transport with a silent failure mode, and because
the disaster-recovery path already depended on GitHub anyway.

**The two host checkouts stop differing.** A disaster-recovered host is a clone
with an `origin`; the deploy host was a `git init` with none. They are now the
same thing, which is one fewer way for a rehearsal to diverge from the real
arrangement.

**CI now sees every deployed commit, and is still not a gate.** `deploy/**` was
added to the workflow's branches, because a deploy ref with no open pull request
would otherwise never be tested at all. It runs alongside the deploy, not before
it, so HW-0029's decision stands and only its supporting argument moves: the
commit is published *first* now, but publication and testing remain
asynchronous.

**HW-0029's account of the remotes is now false.** "Revisions reach the host by
`git push staging`, not by `git push origin`" was true when written; it is
recorded here rather than edited there.

**So is one sentence of HW-0003.** "A commit `origin` has never seen may be
about to [reach the host]" cannot happen now — `deploy.sh` publishes it as part
of deploying it. What survives is the thing that sentence was protecting: the
commit still need not be on `main`, so the warning is still a warning and
staging is still where unmerged work goes.

**Rollback gains a step.** `git revert` then deploy still works, but the revert
must be pushed to the deploy ref before the host can fetch it — `deploy.sh` does
that, so it is one command as before, doing more. The schema caveat is
unchanged: a release with a migration rolls back by restoring a dump (HW-0028).

## Alternatives considered

**Keep pushing into the live worktree and just fix the hole** — by having
`deploy.sh` assert the running commit and leaving the transport alone. This was
genuinely tempting, and the assertion is worth having either way, which is why
it is in this decision. Rejected because it leaves three failure modes in place
to protect a property (no GitHub dependency) that the disaster-recovery path had
already given up.

**A bare repository on the host with a `post-receive` hook**, rejected again for
HW-0002's reason: it would make a push *be* a deployment, and the operator would
not be present for the health check.

**Have the host track a branch and `pull --ff-only`** rather than checking out a
detached sha. Rejected: a deploy ref that rewinds when you deploy an earlier
commit is not fast-forwardable, and a detached sha says exactly what is running
with no ambiguity about which branch the host thinks it is on.

**Build the image elsewhere and have the host pull it from a registry.** The
better end state, and not affordable yet: it needs a registry and credentials,
the host still needs a tree for the bind-mounted `config/`, and the host is
x86_64 while the laptop is arm64, so the build would have to move to CI.
Revisit when there is a second host or a second operator.
