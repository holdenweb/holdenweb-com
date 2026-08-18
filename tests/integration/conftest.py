"""Integration tests: a real browser against a running site.

Deliberately separate from `tests/`, which needs no server and runs in two
seconds. These need a site actually serving, so they are **skipped unless you
say where it is**:

    uv run pytest tests/integration --base-url http://localhost:8461
    uv run pytest tests/integration --base-url https://staging.holdenweb.com

That makes `uv run pytest` safe to run at any time -- it collects these,
skips them, and stays fast -- while the same suite verifies the lab, staging
and production without a line changing. Which is the point: a deployment is
only verified if the thing you check is the thing you deployed.

Browsers are installed once per machine:

    uv run playwright install chromium
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def require_a_site(base_url: str | None) -> str:
    """Skip the whole directory rather than fail it when no site is named.

    A failure would mean "the site is broken"; the truth is "you did not say
    which site", and those deserve different colours.
    """
    if not base_url:
        pytest.skip(
            "no site to test -- pass --base-url, e.g. "
            "--base-url http://localhost:8461",
            allow_module_level=True,
        )
    return base_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Ignore certificate errors, so a staging host with a self-signed
    certificate is testable without arguments nobody remembers."""
    return {**browser_context_args, "ignore_https_errors": True}
