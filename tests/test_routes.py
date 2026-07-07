def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Holden Web" in response.data


def test_missing_note_is_404(client):
    response = client.get("/note/does-not-exist")
    assert response.status_code == 404


def test_missing_page_is_404(client):
    response = client.get("/page/does-not-exist/")
    assert response.status_code == 404


def test_get_my_ip(client):
    response = client.get("/ip")
    assert response.status_code == 200
    assert "ip" in response.get_json()


def test_config_requires_auth(client):
    response = client.get("/config")
    assert response.status_code in (302, 401)


def test_qrcode_form_get(client):
    response = client.get("/qrcode/")
    assert response.status_code == 200


def test_pdf_blueprint_root(client):
    response = client.get("/pdf/")
    assert response.status_code == 200
