# Build the site from the podpack distribution rather than from a loose
# directory of source: the image then contains exactly what `uv sync --frozen`
# resolves from the committed lockfile, which is the same thing a developer
# gets locally and the same thing a deployment gets.
#
# Two stages, because three things are needed to *build* the venv and none of
# them to run it: git, uv, and uv's download cache. Together they are half the
# image -- 398MB single-stage against 203MB here -- so the runtime stage takes
# the finished venv and leaves the toolchain behind.

FROM docker.io/library/python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# uv is copied from its own pinned image rather than pip-installed, so the
# build has one fewer network fetch to go wrong and one fewer version to drift.
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv

# No `git` in this stage, which is a measured choice and not an oversight.
#
# It was needed for as long as four of this site's dependencies resolved from
# GitHub: uv shells out to a real `git` for anything locked to a git source, and
# the slim base has none, so the build failed with "Git executable not found" --
# a message naming neither this file nor the dependency that wanted it. All five
# apps publish to PyPI now and [tool.uv.sources] names no git source, so nothing
# `uv sync --frozen` does below reaches for it.
#
# Measured on 2026-09-22 by building this file both ways:
#
#     builder stage     505.2 MB      ->  401.6 MB        103.6 MB saved
#     what ships        262,750,539 B ->  262,750,539 B   identical
#
# Those are the two builds of the same tree, an hour apart; the absolute figure
# drifts with the tree itself, since README.md is copied in and travels into the
# installed wheel. It is the difference between the pair that is the measurement.
#
# The shipped image is the same to the byte, because the second stage below was
# already keeping git out of it -- confirmed by running `command -v git` in both
# images, which finds nothing in either. What the layer actually cost was those
# 103.6 MB of builder layers, kept wherever the build runs, which for this site
# is the host that serves it; and about twelve seconds whenever the base image
# moves and the layer has to be built again.
#
# Put it back if a git source ever returns to uv.lock -- an app pinned to a
# repository, or a fork being tried before it is released. Removing it later in
# a single-stage build would not have worked, incidentally: the layer above
# still carries the files and a deletion only adds another layer on top. Not
# installing it is what this two-stage arrangement is for.
#
#     RUN apt-get update \
#      && apt-get install --yes --no-install-recommends git \
#      && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first, in their own layer keyed on the lockfile, so that editing
# the source does not reinstall the world on every rebuild.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/
COPY README.md ./
RUN uv sync --frozen --no-dev


FROM docker.io/library/python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# The same WORKDIR as the builder, and not by coincidence. The venv's
# console-script shebangs carry an absolute interpreter path, so a venv built
# under one directory and copied to another leaves every entry point -- gunicorn,
# alembic -- failing to spawn with a bare "no such file or directory". It is the
# same trap as renaming the project directory on the host.
WORKDIR /app

COPY --from=builder /app/.venv ./.venv

# The project is installed into that venv as an editable pointing at ./src, so
# the source has to come too -- the venv alone is not a complete installation.
COPY src/ ./src/

# The migration environment ships in the image because the `migrate` service
# runs from it: the schema a build expects and the code that expects it then
# travel together and cannot be deployed out of step.
COPY alembic.ini ./
COPY alembic/ ./alembic/

# The container healthcheck runs this. It is a file rather than a `python -c`
# one-liner because podman splits ["CMD", ...] arguments on whitespace; see the
# module docstring.
COPY container/healthcheck.py ./healthcheck.py

ENV PATH="/app/.venv/bin:${PATH}"

# Which commit this image was built from, reported by /_status. It arrives as a
# build argument because the image cannot work it out for itself: `.git` is
# excluded from the build context, and the runtime stage has no git anyway.
# `unknown` when built by hand rather than through scripts/up.sh.
ARG GIT_SHA=unknown
ENV PODPACK_BUILD_COMMIT=${GIT_SHA}

# Run unprivileged. The uid/gid are fixed so the compose init-storage service
# knows who to hand the bind-mounted host directories to.
#
# The home directory is not decoration: gunicorn's control server puts its
# socket under $HOME and refuses to start quietly if it cannot write there.
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app
ENV HOME=/home/app
USER 10001:10001

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --access-logfile - 'holdenweb:create_app()'"]
