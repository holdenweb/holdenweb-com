# HW-0024: One backlog for every repository, and filing upstream is a separate act

**Status:** Accepted

**Date:** 2026-09-22

## Context

Running this site turns up defects in the framework it is built on, and in the
apps it installs. Of the nine items open as at 2026-09-22, four belong to
podpack and one to podpack-notebooks; across the whole file the destinations are
four repositories, not one.

The finding happens *here*, in the middle of other work. Filing it upstream is a
different act: it publishes to a shared, public record, in somebody's name.

## Decision

All findings go into this site's single backlog whatever repository they belong
to, and each names its destination in a `Repo` column.

**Filing a GitHub issue is a separate, deliberate step**, because "creating
issues is a change to a shared, public record, and that is the account holder's
call rather than a side effect of writing a document." Sections are *shaped* as
issue titles and bodies, and one template `gh issue create` invocation in the
"Filing these" section shows the mechanics.

## Consequences

**Extraction for any destination is a filter on one column**, which is why no
per-repository holding directory was needed. That is an affordance rather than a
practice: the only extraction that exists filters on `**fixed**` and merely
carries the `Repo` value through.

**The site's own record carries other projects' work**, and an upstream fix
closes an item here in two distinguishable stages. Because the site installs
from PyPI (HW-0018), "fixed upstream" and "taken here" are different events, and
item 30 is the worked example: marked fixed on the strength of a podpack commit,
then actually adopted when 0.9.3 released and the floor moved — hours apart, but
two events.

**The upstream trackers say nothing about known defects.** Nothing has ever been
filed, on any repository, which is the standing cost of making filing
deliberate: the backlog is a private list of other people's bugs, and two of the
four destination repositories have not even had their Issues checked.

**Two rules in the file disagree, and nothing has tested which wins.** The
header says append-only, "never rewritten except to strike an item with its
evidence"; "Filing these" says to delete an item once its issue exists. Fixed
and struck items keep their evidence; a filed one would vanish. Since nothing
has been filed, the conflict is untried. **The header wins**: an item that has
been filed should be struck with its issue URL as the evidence, not deleted.

## Alternatives considered

**File each finding upstream as it is found.** Rejected: publishing to a shared
public record is the account holder's decision, not a side effect of writing a
document — and a finding made while doing something else is exactly when it is
least well understood.

**A holding directory per destination repository.** Rejected: "mark the
destination in the document, and let the filesystem follow later and cheaply."

**A backlog per repository, each in its own tree.** Not taken, and worth
revisiting if the upstream repositories ever grow their own. It would put each
finding where its fixer looks, at the cost of the single list that makes an
audit of "what is still open" possible at all.
