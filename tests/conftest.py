import pytest

from holdenweb import create_app, db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SERVER_NAME": None,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
        "SECURITY_PASSWORD_SALT": "test-password-salt",
        "WTF_CSRF_ENABLED": False,
        "MAIL_BACKEND": "dummy",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
