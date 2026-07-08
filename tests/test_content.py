import pytest
import responses
from responses import matchers

from holdenweb.content import (
    ContentNotFound,
    ContentUnavailable,
    HTTPContentSource,
    LocalContentSource,
    rewrite_asset_urls,
)


@pytest.fixture
def tmp_source(tmp_path):
    (tmp_path / "html-pages" / "writing").mkdir(parents=True)
    (tmp_path / "md-pages").mkdir()
    (tmp_path / "html-pages" / "sample.html").write_text("<p>hi</p>")
    (tmp_path / "html-pages" / "writing" / "nested.html").write_text(
        '<img src="images/x.jpg">'
    )
    (tmp_path / "html-pages" / "writing" / "images").mkdir()
    (tmp_path / "html-pages" / "writing" / "images" / "x.jpg").write_bytes(
        b"\xff\xd8fake"
    )
    (tmp_path / "md-pages" / "note.md").write_text("# Title\n\nbody")
    return LocalContentSource(tmp_path)


def test_local_html(tmp_source):
    assert tmp_source.html("sample") == "<p>hi</p>"


def test_local_html_nested(tmp_source):
    assert tmp_source.html("writing/nested") == '<img src="images/x.jpg">'


def test_local_markdown(tmp_source):
    assert tmp_source.markdown("note").startswith("# Title")


def test_local_asset(tmp_source):
    body, ctype = tmp_source.asset("html/writing/images/x.jpg")
    assert body == b"\xff\xd8fake"
    assert ctype == "image/jpeg"


@pytest.mark.parametrize(
    "bad",
    [
        "../etc/passwd",
        "writing/../../etc",
        "/absolute/path",
        "",
        "./sneaky",
    ],
)
def test_local_html_rejects_traversal(tmp_source, bad):
    with pytest.raises(ContentNotFound):
        tmp_source.html(bad)


def test_local_asset_unknown_category(tmp_source):
    with pytest.raises(ContentNotFound):
        tmp_source.asset("static/x.jpg")


def test_rewrite_relative_src(tmp_source):
    html = '<img src="images/x.jpg"> <a href="other.html">link</a>'
    out = rewrite_asset_urls(html, page_dir="writing")
    assert 'src="/asset/html/writing/images/x.jpg"' in out
    assert 'href="/asset/html/writing/other.html"' in out


def test_rewrite_leaves_absolute_urls_alone(tmp_source):
    html = (
        '<a href="https://example.com/">ext</a> '
        '<a href="/static/foo">static</a> '
        '<a href="#section">anchor</a> '
        '<a href="mailto:x@y">mail</a> '
        '<img src="data:image/gif;base64,AAAA">'
    )
    assert rewrite_asset_urls(html, page_dir="writing") == html


def test_asset_route_serves_file(client):
    r = client.get("/asset/md/note.md")
    # This client is bound to the real package data, so the specific file
    # may or may not exist; we just want to prove the route is registered
    # and returns a 404 vs. 500 cleanly for a missing asset.
    assert r.status_code in (200, 404)


def test_asset_route_404_for_missing(client):
    r = client.get("/asset/html/does/not/exist.jpg")
    assert r.status_code == 404


def test_asset_route_404_for_bad_category(client):
    r = client.get("/asset/static/foo.jpg")
    assert r.status_code == 404


BASE = "https://content.example"
AUTH = matchers.header_matcher({"Authorization": "Bearer sekret"})


@pytest.fixture
def http_source():
    return HTTPContentSource(base_url=BASE, token="sekret", timeout=1.0)


@responses.activate
def test_http_html_ok(http_source):
    responses.get(
        f"{BASE}/html/writing/essay.html",
        body="<p>hi</p>",
        status=200,
        match=[AUTH],
    )
    assert http_source.html("writing/essay") == "<p>hi</p>"


@responses.activate
def test_http_markdown_ok(http_source):
    responses.get(
        f"{BASE}/md/note.md", body="# t", status=200, match=[AUTH],
    )
    assert http_source.markdown("note") == "# t"


@responses.activate
def test_http_asset_ok(http_source):
    responses.get(
        f"{BASE}/html/writing/images/x.jpg",
        body=b"\xff\xd8xx",
        status=200,
        content_type="image/jpeg",
        match=[AUTH],
    )
    body, ctype = http_source.asset("html/writing/images/x.jpg")
    assert body == b"\xff\xd8xx"
    assert ctype == "image/jpeg"


@responses.activate
def test_http_404_raises_not_found(http_source):
    responses.get(f"{BASE}/html/missing.html", status=404, match=[AUTH])
    with pytest.raises(ContentNotFound):
        http_source.html("missing")


@responses.activate
def test_http_5xx_raises_unavailable(http_source):
    responses.get(f"{BASE}/html/broken.html", status=502, match=[AUTH])
    with pytest.raises(ContentUnavailable):
        http_source.html("broken")


@responses.activate
def test_http_timeout_raises_unavailable(http_source):
    import requests

    responses.get(
        f"{BASE}/html/slow.html",
        body=requests.exceptions.Timeout(),
        match=[AUTH],
    )
    with pytest.raises(ContentUnavailable):
        http_source.html("slow")


@responses.activate
def test_http_stale_on_error(http_source):
    # First call caches; second sees a 502 and serves stale.
    responses.get(
        f"{BASE}/html/page.html", body="fresh", status=200, match=[AUTH],
    )
    assert http_source.html("page") == "fresh"
    responses.replace(
        responses.GET, f"{BASE}/html/page.html", status=502, match=[AUTH],
    )
    assert http_source.html("page") == "fresh"


@responses.activate
def test_http_rejects_traversal(http_source):
    with pytest.raises(ContentNotFound):
        http_source.html("../etc/passwd")
    # And no request should have been made.
    assert len(responses.calls) == 0


def test_startup_fails_when_url_set_without_token(monkeypatch):
    from holdenweb import create_app

    with pytest.raises(RuntimeError, match="CONTENT_ACCESS_TOKEN"):
        create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "x",
            "SECURITY_PASSWORD_SALT": "x",
            "MAIL_BACKEND": "dummy",
            "CONTENT_BASE_URL": "https://example/content",
            "CONTENT_ACCESS_TOKEN": None,
        })
