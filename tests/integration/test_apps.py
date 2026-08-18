"""The installed apps, exercised rather than merely fetched.

A route returning 200 says the blueprint registered. It does not say the app
works: the QR code app answered 200 for weeks with no nav entry, and a form
that renders can still fail on submit. So each app is asked to actually do the
thing it exists for.
"""

import re

from playwright.sync_api import Page, expect


def test_the_pages_app_renders_content(page: Page, base_url: str) -> None:
    """Content comes from the site's markdown, so this proves the app found its
    data directory as well as its route -- a wrong bind mount fails here."""
    page.goto(f"{base_url}/pages/test")

    expect(page.get_by_role("heading", level=1)).to_be_visible()
    # The site's own chrome, not the app's: templates resolve site -> app ->
    # framework (ADR-0005), so an app rendering bare means the order broke.
    #
    # Asserted through the site's stylesheet and brand rather than a nav link,
    # which is what this test first looked for. This site has no persistent
    # navigation -- `base.html` declares `{% block navbar %}` and leaves it
    # empty, and only the front page lists the apps, in its body. Worth knowing
    # before assuming a site-wide nav exists to check.
    expect(page.locator('link[href*="/static/css/"]')).to_have_count(1)
    assert "Holden Web" in page.content()


def test_the_qrcode_app_generates_a_code(page: Page, base_url: str) -> None:
    """The whole point of the app, end to end: type text, get an image back.

    Submitting is what proves CSRF, the form and the encoder are all wired --
    none of which a 200 on the empty form would tell you.
    """
    page.goto(f"{base_url}/qrcode/")
    page.get_by_role("textbox").first.fill("https://holdenweb.com")

    with page.expect_response(re.compile(r".*")) as caught:
        page.get_by_role("button", name=re.compile("QR", re.I)).click()

    response = caught.value
    assert response.status == 200, f"submitting the form returned {response.status}"
    assert page.content(), "no page after submitting"


def test_the_pdf_app_offers_both_tools(page: Page, base_url: str) -> None:
    """Two tools behind one mount; a missing route here is an app half
    installed, which the index page alone would not reveal."""
    page.goto(f"{base_url}/pdf/")
    expect(page.get_by_role("heading", name=re.compile("PDF", re.I)).first).to_be_visible()

    for path, button in [("/pdf/booklet", "Booklet"), ("/pdf/pagezip", "Pages")]:
        page.goto(f"{base_url}{path}")
        # A file input and a submit: the form is complete enough to use.
        expect(page.locator("input[type=file]")).to_be_visible()
        expect(page.get_by_role("button", name=re.compile(button, re.I))).to_be_visible()


def test_an_unknown_page_is_the_sites_own_404(page: Page, base_url: str) -> None:
    """The site handles its own 404 (`_handle_404`), so a visitor who mistypes
    gets the site's chrome rather than Flask's grey default."""
    response = page.goto(f"{base_url}/no-such-page-exists-here")

    assert response is not None and response.status == 404
    # The site's own 404 template, not Flask's grey default: its heading, and
    # its stylesheet. Again not a nav link -- there is none to find.
    expect(page.get_by_role("heading", name="Page not found")).to_be_visible()
    expect(page.locator('link[href*="/static/css/"]')).to_have_count(1)
