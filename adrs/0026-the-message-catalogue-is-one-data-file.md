# HW-0026: The message catalogue is one data file and two generated views

**Status:** Accepted

**Date:** 2026-09-22

## Context

At three in the morning an operator has a message on a screen and no idea which
of six layers produced it: the ops scripts, podpack's scripts, the app at boot,
the substrate CLI, the container and PostgreSQL, or git, uv, podman and nginx.
There are 119 such messages.

A hand-written catalogue would have to be kept in two shapes at once: something
greppable on the host, where there is no browser, and something searchable in a
browser, where 119 entries are unreadable as a flat file.

## Decision

`ops/messages.json` is the single data file, one entry per line, and
`ops/build-messages.py` renders it two ways: `ops/MESSAGES.md` to grep on the
host, and `ops/messages.html` to search in a browser.

**Both outputs are committed**, so the knowledge base travels with the
repository and needs no toolchain on the host — which is the point, since the
host is where it is needed and the host has nothing installed.

Each generated file says in its first lines that it is generated and which file
to edit instead. The JSON keeps one entry per line deliberately, so a change to
one field shows as a change to one line.

## Consequences

**An operator greps one file on the host and gets the layer, the meaning and
the action.** No network, no toolchain, no browser.

**Generated files are committed, which is normally a smell**, and here is the
decision: the alternative is a build step on a host that has no build step, at
the moment somebody is least able to run one.

**The catalogue can go stale against the system it describes, and has.**
`build-git-not-found` still says the builder installs git and tells the operator
to make sure it still does — both false since HW-0020. Nothing checks a message
in the catalogue against the code that emits it, and a wrong entry is worse than
a missing one, because it is read at three in the morning and believed.

**A one-line-per-entry JSON is awkward to edit by hand** and is the price of
readable diffs. It is the right trade for a file whose changes are almost always
one field.

## Alternatives considered

**A hand-written Markdown catalogue.** Rejected: it would be maintained in two
shapes, and the two would diverge — the failure HW-0022 exists to prevent.

**Generate the browser view on demand and commit only the Markdown.** Rejected
for the host-toolchain reason above: a view that needs a build step is a view
that is not there when it is wanted.

**Put the messages in the code that emits them** — docstrings, error classes —
and generate the catalogue from those. The principled answer, and not available:
the messages come from six layers, four of which are other people's software.
