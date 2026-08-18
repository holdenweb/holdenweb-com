"""Integration tests: a real browser against a running site.

Deliberately separate from `tests/`, which needs no server and runs in two
seconds. These need a site actually serving, so they need to know where it is
-- and on a deployed host they work that out for themselves:

    uv run pytest tests/integration

reads `WEB_HOST_PORT` and `WEB_BIND_ADDR` from the site's own `.env`, which is
the file that decided where the site listens in the first place. Nothing to
remember, nothing to keep in step, and it is right on every host by
construction.

Override it to test somewhere else:

    uv run pytest tests/integration --base-url https://staging.holdenweb.com
    SITE_URL=https://holdenweb.com uv run pytest tests/integration

Browsers are installed once per machine:

    uv run playwright install chromium
"""

import os
import re
from pathlib import Path

import pytest

SITE_ROOT = Path(__file__).parents[2]


def url_from_env_file() -> str | None:
    """Where this site listens, according to the file that decided it.

    `.env` is per-host and gitignored, so on the deployment being tested it
    holds that host's allocated port -- which is exactly what these tests need
    and exactly what nobody wants to retype.

    A bind address of 0.0.0.0 means "every interface", which is not an address
    you can connect to; localhost is what that means from here.
    """
    env = SITE_ROOT / ".env"
    if not env.is_file():
        return None
    values = {}
    for line in env.read_text().splitlines():
        match = re.match(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"').strip("'")
    port = values.get("WEB_HOST_PORT")
    if not port:
        return None
    host = values.get("WEB_BIND_ADDR") or "127.0.0.1"
    if host in ("0.0.0.0", "::", ""):
        host = "127.0.0.1"
    return f"http://{host}:{port}"


def resolve(config: pytest.Config) -> str | None:
    """--base-url, else $SITE_URL, else the site's own .env."""
    given = config.getoption("--base-url") or os.environ.get("SITE_URL")
    resolved = given or url_from_env_file()
    return resolved.rstrip("/") if resolved else None


def pytest_report_header(config: pytest.Config) -> str:
    """Say which site is being tested, in the header, where it cannot be
    missed.

    A print in a fixture is swallowed by pytest's capture unless somebody
    passes -s, which is how the first version of this managed to say nothing
    at all. These tests pass or fail against whatever they were pointed at, and
    a suite that does not say what it checked is one failed deployment away
    from being believed about the wrong machine.
    """
    target = resolve(config)
    return f"integration target: {target or 'none -- these tests will skip'}"


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """--base-url, else $SITE_URL, else the site's own .env.

    Overrides pytest-base-url's fixture so that the common case -- "check the
    site on this host" -- needs no argument at all. Skipping with a reason
    nobody sees is not a helpful default, and that is what this replaced.
    """
    resolved = resolve(request.config)
    if not resolved:
        pytest.skip(
            "no site to test: pass --base-url, set SITE_URL, or run from a "
            "site whose .env sets WEB_HOST_PORT",
            allow_module_level=True,
        )
    return resolved


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Ignore certificate errors, so a staging host with a self-signed
    certificate is testable without arguments nobody remembers."""
    return {**browser_context_args, "ignore_https_errors": True}
