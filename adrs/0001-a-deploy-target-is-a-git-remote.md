# HW-0001: A deploy target is a git remote

**Status:** Accepted

**Date:** 2026-09-22

## Context

Three tools on the laptop need to know where `staging` is. `ops/deploy.sh`
pushes code to it, `ops/push-content.sh` pushes content to it, and `.justfile`
dispatches to whichever of the two applies. The host (`opal17`) and the site
path (`apps/os/site`) had to be written down somewhere they could all read.

podpack leaves this entirely open. Its substrate ships seven scripts and none of
them is a deploy script: everything podpack provides runs *on* the host, and how
a laptop addresses its deployments is ground nobody else occupies.

The address had also already proved able to go stale. The site's first remote,
`main`, pointed at `opal17:apps/third-alma/holdenweb-com` and, in the words of
the commit that replaced it, "never resolved". The receiving directory had been
renamed — `bbbf773`, "Name the directory after the project, and stop the usage
naming one host", which chose `holdenweb-com` over a role-based name so that the
directory and the compose project it owns would agree, after "two silent renames
between the directory and the containers ... produced 'service web is not
running' about a container that was." That incident is not evidence against
storing the address in a remote; a remote is exactly where it was. It is the
reason for deciding deliberately where the address lives and for making a
missing one say so loudly.

## Decision

A deploy target is a git remote, and its scp-style URL is the whole of its
definition. Each tool reads it with `git remote get-url <target>` and splits it
on the colon into host and path; the same eight lines appear in `ops/deploy.sh`
and `ops/push-content.sh`, and `.justfile` reaches both through them. A target
with no remote is an error that prints the `git remote add` line needed to fix
it, not a default that guesses:

```
no git remote named 'production'. Add it (see ops/DEPLOY.md):
  git remote add production opal17:apps/<app>/site
```

The same remote serves as the content target, so code and content address one
place by one name.

## Consequences

`git remote -v` on the laptop is the deployment inventory, and adding production
is `git remote add production opal17:apps/hw/site` with no change to any script
— `ops/DEPLOY.md` writes that out.

**The inventory is per-clone and untracked.** A fresh clone of this repository
can deploy nothing until its remotes are added by hand, and `ops/DEPLOY.md` is
the only record of what they should be. That is the price of using git's own
namespace rather than a file in the tree, and it is worth naming because a
clone that cannot deploy looks like a broken tool rather than an unconfigured
one.

**The rule covers the push direction only.** `ops/pull-backups.sh` needs the
same two facts and does not ask the remote for them: it carries
`SITE_NAME="${SITE_NAME:-os-holdenweb-com}"` and `HOST="${BACKUP_HOST:-opal17}"`
— guessed defaults, precisely the shape this record rejects. The pull direction
was never converted. Stated here as a known limit rather than left to be found,
because a rule contradicted by its own sibling script is believed once.

**What the URL does not carry has to be written twice.** The public health URL
is not derivable from `opal17:apps/os/site`, so it lives in a hardcoded `case`
statement in `deploy.sh` *and* as a default in `ops/poll-health.sh`. This is
not an inconsistency so much as a consequence of a decision recorded elsewhere:
podpack ADR-0037 puts `PUBLIC_URL` in the *host's* `.env`, and the laptop cannot
read the host's `.env`, so laptop-side tooling has no choice but to keep its own
copy.

**Ports are still hand-allocated.** podpack ADR-0001 gives each deployment its
own compose project and image through `SITE_NAME`, "but ports are not covered
and must still be chosen by hand per deployment." Two deployments on `opal17`
therefore need distinct `WEB_HOST_PORT`s, and nothing in this arrangement
checks it. The first symptom would be a container that fails to start.

## Alternatives considered

**A config file or env block listing host and path per target**, read by each
script. Rejected: it is a second copy of something git already holds, and every
one of these scripts requires git anyway to do the push itself. Two records of
one address is the condition under which they disagree.

**Hardcoding host and path in each script.** Rejected for the same reason, with
the additional cost that adding production would then be an edit to three files
rather than one command.

**Deriving the target from `PODPACK_ENVIRONMENT`** or another name the host
already knows. Rejected because that variable lives on the host (podpack
ADR-0037), and the laptop is the machine that has to resolve the target before
it can reach the host at all.
