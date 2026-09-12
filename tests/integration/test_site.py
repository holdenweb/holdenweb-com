"""The site itself: its chrome, its guards, and the endpoints an operator uses.

Everything here is asserted through a browser against a running deployment, so
a pass means the thing that is serving works -- not that the code that built it
would have.
"""

import os

import pytest
from playwright.sync_api import Page, expect

# Every route the site is expected to answer, and what it is. Table-driven
# because "is it up?" is the first question after any deploy, and one failure
# should name the route rather than stopping the run.
PAGES = [
    ("/", "the front page"),
    ("/pages/test", "a page from the pages app"),
    ("/notebooks/", "the notebooks index"),
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
        ("Python", "/pybooks/"),
        ("Blog", "/blog/"),
        ("Notebooks", "/notebooks/"),
        ("QR codes", "/qrcode/"),
        ("PDF tools", "/pdf/"),
    ]:
        expect(page.get_by_role("link", name=label, exact=True).first).to_have_attribute(
            "href", href
        )


def test_healthz_reports_the_database(page: Page, base_url: str) -> None:
    """What the container healthcheck gates on, so it is worth checking from
    outside as well: a site can serve pages while its database is gone.

    Apps may contribute their own health under `apps` (ADR-0030) -- the blog
    reports whether its export loaded -- and a non-fatal app is deliberately not
    allowed to take the top-level status down. So this asserts the contract the
    healthcheck actually gates on, `status` and `database`, rather than the exact
    shape of the body, which grows an `apps` entry per app that reports.
    """
    response = page.request.get(f"{base_url}/healthz")

    assert response.status == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


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


# An account that exists, so a submit reaches the validation code rather than
# short-circuiting on "no such user". Its email is not a secret; override per
# target with SMOKE_LOGIN_EMAIL. No password is carried -- the point is to fail.
SMOKE_LOGIN_EMAIL = os.environ.get("SMOKE_LOGIN_EMAIL", "steve@holdenweb.com")


def test_submitting_the_login_form_does_not_error(page: Page, base_url: str) -> None:
    """Submit the login form and assert it *rejects* cleanly, not 500s.

    The sibling test above only GETs the form, which is why two separate
    breakages reached production unseen: a migration that never built the `user`
    table (500 on the lookup), and two flask_security packages colliding so the
    login form called `is_locked` on a User that lacked it (500 in validation).
    Both showed only on POST, and only for an account that exists -- so this
    submits a real account's email with a deliberately wrong password, carrying
    no credential, purely to drive that path and confirm it ends in a civil
    "wrong password", never an Internal Server Error.
    """
    page.goto(f"{base_url}/login")
    page.get_by_role("textbox", name="Email Address").fill(SMOKE_LOGIN_EMAIL)
    page.get_by_label("Password", exact=True).fill("deliberately-wrong-password")

    with page.expect_response(
        lambda r: r.request.method == "POST" and r.url.rstrip("/").endswith("/login")
    ) as posted:
        page.get_by_role("button", name="Login").click()

    assert posted.value.status < 500, (
        f"POST /login returned {posted.value.status} -- the login path is broken "
        "on the deployment (a missing table, a bad dependency, a dead mail path)"
    )
    # And it must have *handled* the bad login, not merely avoided a 500: the
    # form comes back for another try. A crash page would not carry it.
    expect(page.get_by_role("button", name="Login")).to_be_visible()


# --- second-level nav, reading column, and code theme --------------------
# Three chrome features that shipped together and are each invisible to a 200:
# the section subnav, the reading column, and the site's own code theme. Each
# has a silent-regression twin -- a page that must *not* get the treatment --
# so both halves are asserted, because a blanket rule that caught the front
# page or a lost opt-out would still leave every 200 green.

# App/article pages render their body in a reading column: base.html carries a
# `reading` modifier on .maincol, because the content apps fill
# `{% block content %}` without the default .prose wrapper, so the column -- not
# the wrapper -- is where the measure has to be enforced.
READING_COLUMN_PAGES = [
    ("/pages/test", "a pages markdown page"),
    ("/pybooks/python1/index", "a pybooks lesson"),
    ("/notebooks/", "the notebooks index"),
    ("/blog/", "the blog index"),
]


@pytest.mark.parametrize(
    "path, what", READING_COLUMN_PAGES, ids=[p for p, _ in READING_COLUMN_PAGES]
)
def test_app_pages_render_in_the_reading_column(
    page: Page, base_url: str, path: str, what: str
) -> None:
    page.goto(f"{base_url}{path}")
    expect(page.locator("main.page .maincol.reading")).to_have_count(1)


def test_the_front_page_opts_out_of_the_reading_column(page: Page, base_url: str) -> None:
    """The one full-width page: its featured grid needs the width, so index.html
    clears the modifier. The column is still there -- just not constrained -- so
    this asserts the modifier is gone, not the column."""
    page.goto(base_url)
    expect(page.locator("main.page .maincol")).to_have_count(1)
    expect(page.locator("main.page .maincol.reading")).to_have_count(0)


def test_the_section_rail_appears_only_where_an_app_asks(page: Page, base_url: str) -> None:
    """The blog contributes a year archive as its section nav (ADR-0022's second
    level) and the chrome renders it as a left rail; pybooks deliberately
    supplies none -- it keeps orpy's own in-page course nav -- so the rail must
    be absent there. The opt-out is the half that regresses unseen: a stray
    `subnav = true` would light a rail up on every app and nothing else would
    notice."""
    page.goto(f"{base_url}/blog/")
    rail = page.locator("aside.subnav")
    expect(rail).to_have_count(1)
    expect(rail).to_contain_text("Archive")  # the year-archive heading

    page.goto(f"{base_url}/pybooks/python1/index")
    expect(page.locator("aside.subnav")).to_have_count(0)


def test_the_site_themes_markdown_code(page: Page, base_url: str) -> None:
    """Markdown fenced code is marked up by podpack-pages (Pygments classes on a
    `.codehilite` block) but coloured by the SITE: holdenweb ships
    templates/podpack_pages/codehilite.css and the loader resolves it ahead of
    the app's shipped default (site -> app -> framework, ADR-0005). So this is
    really "is the override in force on the deployed host?" -- which a page that
    merely served would not reveal. /pages/test carries a Python block."""
    page.goto(f"{base_url}/pages/test")
    block = page.locator(".codehilite").first
    expect(block).to_be_visible()  # the page actually carries a fenced block
    # The panel background is the override's #fbfbfe, not the shipped #f8f8f8 --
    # true whatever tokens the code contains, so it is the load-bearing check.
    expect(block).to_have_css("background-color", "rgb(251, 251, 254)")
    # And a keyword is the site's deep blue (--deep, #0d2a8f), not Pygments'
    # default green (#008000): the tokens are themed, not merely the box.
    expect(page.locator(".codehilite .k").first).to_have_css("color", "rgb(13, 42, 143)")
