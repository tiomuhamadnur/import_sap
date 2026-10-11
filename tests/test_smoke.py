from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.text == "ok"


def test_login_page():
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "Sign in" in resp.text


def test_home_serves_login_when_unauthenticated():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Sign in" in resp.text


def test_unknown_page_returns_404():
    resp = client.get("/nope")
    assert resp.status_code == 404
