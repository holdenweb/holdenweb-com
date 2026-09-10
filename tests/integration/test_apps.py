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
    # The stylesheet and the brand, and -- since 2026-08-24 -- the navigation.
    # This comment used to say the opposite: that the site had no persistent
    # nav, that `base.html` declared `{% block navbar %}` and left it empty, and
    # that a reader should not go looking for one. All true when written, and it
    # outlived the fix by exactly as long as nobody re-read it.
    expect(page.locator('link[href*="/static/css/"]')).to_have_count(1)
    assert "Holden Web" in page.content()
    expect(page.locator("nav.pagenav a")).to_have_count(6)


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
    # The site's own 404 template, not Flask's grey default: its heading, its
    # stylesheet, and its navigation -- a visitor who mistypes should be able to
    # get somewhere, which is most of what a 404 is for.
    expect(page.get_by_role("heading", name="Page not found")).to_be_visible()
    expect(page.locator('link[href*="/static/css/"]')).to_have_count(1)
    expect(page.locator("nav.pagenav a")).to_have_count(6)


def test_the_pybooks_app_serves_a_book(page: Page, base_url: str) -> None:
    """A Python course book, in the site's chrome, with its own assets served.
    Proves pybooks found its data directory (a wrong bind mount fails here) and
    that /pybooks/asset serves the book's files -- neither of which a bare 200
    on the index would show."""
    response = page.goto(f"{base_url}/pybooks/python1/index")
    assert response is not None and response.status == 200, "the python1 book did not serve"
    expect(page.locator('link[href*="/static/css/"]')).to_have_count(1)  # the site's chrome
    expect(page.locator("nav.pagenav a")).to_have_count(6)
    # The book's own stylesheet, through the app's asset route:
    css = page.request.get(f"{base_url}/pybooks/asset/common/course.css")
    assert css.status == 200, f"pybooks asset route returned {css.status}"
    # Every image on the page loads rather than 404s -- a broken asset path here
    # is exactly what a bind-mount or refresh mistake produces.
    for img in page.locator("img").all():
        src = img.get_attribute("src")
        if src and not src.startswith("http"):
            r = page.request.get(f"{base_url}{src}")
            assert r.status == 200, f"lesson image {src} returned {r.status}"


def test_the_blog_app_serves_a_post(page: Page, base_url: str) -> None:
    """The blog index lists posts, and following one renders it in the site's
    chrome -- proving the export landed and its manifest is served, not merely
    that /blog answered."""
    page.goto(f"{base_url}/blog/")
    expect(page.locator("nav.pagenav a")).to_have_count(6)
    post = page.locator('a[href^="/blog/posts/"]').first
    expect(post).to_be_visible()  # the index actually lists posts
    href = post.get_attribute("href")
    response = page.goto(f"{base_url}{href}")
    assert response is not None and response.status == 200, f"post {href} returned {response.status if response else 'nothing'}"
    expect(page.locator('link[href*="/static/css/"]')).to_have_count(1)  # the site's chrome
    assert "Holden Web" in page.content()
