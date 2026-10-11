import re
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.models import User
from app.security import hash_password

PASSWORD = "testpass123"


def _csrf(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _make_user(db, *, name="Temp User", email=None, username=None, password=PASSWORD):
    email = email or f"temp_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        username=username,
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="viewer",
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    return user


def _drop(db, user):
    db.delete(user)
    db.commit()


def test_create_user_without_username(admin_client, db):
    email = f"new_{uuid.uuid4().hex[:8]}@example.com"
    token = _csrf(admin_client.get("/users/new").text)
    resp = admin_client.post(
        "/users/new",
        data={
            "csrf_token": token,
            "name": "New Person",
            "email": email,
            "username": "",
            "phone": "",
            "password": PASSWORD,
            "role": "viewer",
        },
    )
    assert resp.status_code == 303
    user = db.query(User).filter(User.email == email).one()
    try:
        assert user.username is None
        assert user.name == "New Person"
        assert user.email == email
        assert user.must_change_password is True
    finally:
        _drop(db, user)


def test_create_user_requires_name_and_email(admin_client):
    token = _csrf(admin_client.get("/users/new").text)
    resp = admin_client.post(
        "/users/new",
        data={
            "csrf_token": token,
            "name": "",
            "email": "",
            "password": PASSWORD,
            "role": "viewer",
        },
    )
    assert resp.status_code == 400
    assert "Name is required" in resp.text


def test_create_user_rejects_duplicate_email(admin_client, db):
    existing = _make_user(db)
    try:
        token = _csrf(admin_client.get("/users/new").text)
        resp = admin_client.post(
            "/users/new",
            data={
                "csrf_token": token,
                "name": "Dupe",
                "email": existing.email,
                "password": PASSWORD,
                "role": "viewer",
            },
        )
        assert resp.status_code == 400
        assert "already exists" in resp.text
    finally:
        _drop(db, existing)


def test_login_by_email(db):
    user = _make_user(db)
    client = TestClient(app, follow_redirects=False)
    try:
        token = _csrf(client.get("/login").text)
        resp = client.post(
            "/login",
            data={"username": user.email, "password": PASSWORD, "csrf_token": token},
        )
        assert resp.status_code == 303
    finally:
        client.close()
        _drop(db, user)
