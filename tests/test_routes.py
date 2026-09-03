import pytest


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Holden Web" in response.data


def test_nav_is_contributed_by_the_installed_apps(client):
    body = client.get("/").get_data(as_text=True)
    assert 'href="/"' in body          # Home
    assert 'href="/python/"' in body   # Python


def test_get_my_ip(client):
    response = client.get("/ip")
    assert response.status_code == 200
    assert "ip" in response.get_json()


def test_config_is_not_public(client):
    """It serialises the whole Flask config -- SECRET_KEY, the database URI and
    MAIL_PASSWORD among it -- so it answers only an operator and 404s to
    everyone else, exactly as /_status does."""
    assert client.get("/config").status_code == 404


def test_config_is_readable_by_an_operator(operator_app):
    report = operator_app.test_client().get("/config").get_json()
    assert report["config"], "the operator's config report is empty"


def test_config_redacts_secret_values(operator_app):
    """An operator sees which settings exist, never their secret values --
    defence in depth, so a slip in the /config guard cannot leak them."""
    cfg = operator_app.test_client().get("/config").get_json()["config"]
    for key in ("SECRET_KEY", "SECURITY_PASSWORD_SALT", "SQLALCHEMY_DATABASE_URI"):
        assert str(operator_app.config[key]) not in cfg[key], f"{key} leaked its value"
        assert "redacted" in cfg[key].lower()
    # A non-secret setting still shows, so this redacts rather than blanks it:
    assert cfg["APPLICATION_ROOT"] == "/"


def test_status_is_not_public(client):
    """It names the database, the role it connects as, and every host path."""
    assert client.get("/_status").status_code == 404


def test_status_reports_all_four_apps_to_an_operator(operator_app):
    apps = operator_app.test_client().get("/_status").get_json()["apps"]
    assert set(apps) == {"main", "pages", "qrcode", "pp_pdf"}


# The installed apps, wearing this site's chrome.

def test_pages_app_serves_seeded_content(client):
    response = client.get("/pages/test")
    assert response.status_code == 200
    assert b"Holden Web" in response.data  # the site's own chrome around it


def test_missing_page_is_404(client):
    assert client.get("/pages/does-not-exist").status_code == 404


def test_qrcode_form_get(client):
    assert client.get("/qrcode/").status_code == 200


def test_pdf_blueprint_root(client):
    assert client.get("/pdf/").status_code == 200


def test_pdf_tools_render_in_site_chrome(client):
    for path in ("/pdf/booklet", "/pdf/pagezip"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"Holden Web" in response.data  # the site's chrome, not standalone


# Legacy content addresses redirect permanently to the unified space.

def test_old_note_url_redirects(client):
    response = client.get("/note/test")
    assert response.status_code == 301
    assert response.headers["Location"] == "/pages/test"


def test_old_page_url_redirects(client):
    response = client.get("/page/parts_demo/")
    assert response.status_code == 301
    assert response.headers["Location"] == "/pages/parts_demo"


def test_old_asset_url_redirects_dropping_the_tree(client):
    response = client.get("/asset/html/writing/images/x.png")
    assert response.status_code == 301
    assert response.headers["Location"] == "/pages/asset/writing/images/x.png"


def test_parts_demo_redirects_to_pages(client):
    response = client.get("/parts/demo")
    assert response.status_code == 302
    assert response.headers["Location"] == "/pages/parts_demo"


def test_old_python_url_redirects_to_pages(client):
    """/python retired its experimental static tree; it now permanently
    redirects to the pages app's python-classes content, and every old
    sub-path collapses onto that one page."""
    response = client.get("/python/")
    assert response.status_code == 301
    assert response.headers["Location"] == "/pages/python-classes"

    deep = client.get("/python/tutorial/index.html")
    assert deep.status_code == 301
    assert deep.headers["Location"] == "/pages/python-classes"


NAV_BEARING = [
    ("/", "the front page"),
    ("/qrcode/", "an installed app"),
    ("/pdf/booklet", "a page deep inside an app"),
    ("/login", "flask-security's own chrome"),
    ("/no-such-page-exists-here", "the site's 404"),
]


@pytest.mark.parametrize("path, what", NAV_BEARING, ids=[p for p, _ in NAV_BEARING])
def test_every_page_carries_the_site_navigation(client, path, what):
    """The nav belongs to the site, not to the front page.

    It was on `/` alone for as long as anybody had looked: `base.html` declared
    `{% block navbar %}` and left it empty, and `index.html` -- which replaces
    `block body` outright -- carried the only copy of the markup. So installing
    an app added it to one page's menu rather than to the site.

    `/login` is here deliberately. `templates/security/base.html` is a
    copy-paste fork of `base.html` rather than a child of it, so anything done
    to one misses the other unless somebody remembers; this is what remembers.
    """
    body = client.get(path).get_data(as_text=True)
    assert 'class="pagenav"' in body, f"{what} has no navigation"
    for label in ("Home", "QR codes", "PDF tools"):
        assert f">{label}</a>" in body, f"{what} omits {label!r}"
