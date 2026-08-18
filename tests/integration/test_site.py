"""The site itself: its chrome, its guards, and the endpoints an operator uses.

Everything here is asserted through a browser against a running deployment, so
a pass means the thing that is serving works -- not that the code that built it
would have.
"""

import pytest
from playwright.sync_api import Page, expect

# Every route the site is expected to answer, and what it is. Table-driven
# because "is it up?" is the first question after any deploy, and one failure
# should name the route rather than stopping the run.
PAGES = [
    ("/", "the front page"),
    ("/pages/test", "a page from the pages app"),
    ("/qrcode/", "the QR code form"),
    ("/pdf/", "the PDF tools index"),
    ("/pdf/booklet", "the booklet form"),
    ("/pdf/pagezip", "the page-split form"),
    ("/login", "the login form"),
]


@pytest.mark.parametrize("path, what", PAGES, ids=[p for p, _ in PAGES])
def test_every_page_is_served(page: Page, base_url: str, path: str, what: str) -> None:
    response = page.goto(f"{base_url}{path}")
    assert response is not None, f"no response for {what}"
    assert response.status == 200, f"{what} returned {response.status}"


def test_the_nav_offers_every_installed_app(page: Page, base_url: str) -> None:
    """Nav is contributed by the apps and addressed by endpoint (ADR-0022), so
    this is really asking whether the app list took effect -- and it is how a
    missing `nav=` on a SiteApp shows up, which is a fault the site cannot
    detect for itself.
    """
    page.goto(base_url)
    for label, href in [
        ("Home", "/"),
        ("Python", "/python/"),
        ("QR codes", "/qrcode/"),
        ("PDF tools", "/pdf/"),
    ]:
        expect(page.get_by_role("link", name=label, exact=True).first).to_have_attribute(
            "href", href
        )


def test_healthz_reports_the_database(page: Page, base_url: str) -> None:
    """What the container healthcheck gates on, so it is worth checking from
    outside as well: a site can serve pages while its database is gone."""
    response = page.request.get(f"{base_url}/healthz")

    assert response.status == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_status_is_refused_to_anonymous_visitors(page: Page, base_url: str) -> None:
    """404 and not 403, deliberately: that a site is a podpack site at all is
    not worth publishing. This asserts the guard rather than the report --
    seeing the report needs an operator's session, which is the next test.
    """
    assert page.request.get(f"{base_url}/_status").status == 404


def test_the_login_form_is_usable(page: Page, base_url: str) -> None:
    """Not a login -- that needs a credential this suite must not carry. Just
    that flask-security's form rendered with the fields it needs, which is what
    a broken template or a missing extension would take away."""
    page.goto(f"{base_url}/login")

    expect(page.get_by_role("textbox", name="Email Address")).to_be_visible()
    expect(page.get_by_label("Password", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Login")).to_be_visible()
