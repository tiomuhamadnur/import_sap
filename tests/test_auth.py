import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
no_redirect = TestClient(app, follow_redirects=False)


def _csrf(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_login_page_has_csrf_token():
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "csrf_token" in resp.text


def test_login_rejects_missing_csrf():
    client.get("/login")
    resp = no_redirect.post(
        "/login", data={"username": "admin", "password": "admin123", "csrf_token": "bad"}
    )
    assert resp.status_code == 403


def test_protected_page_redirects_to_login():
    resp = no_redirect.get("/")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_users_redirects_to_login_when_anonymous():
    resp = no_redirect.get("/users")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_data_page_redirects_to_login_when_anonymous():
    resp = no_redirect.get("/equipment")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"
