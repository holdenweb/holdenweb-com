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


def test_config_requires_auth(client):
    response = client.get("/config")
    assert response.status_code in (302, 401)


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
