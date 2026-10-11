import io
import re
import uuid

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.models import AuditLog, User
from app.security import hash_password
from app.services.avatar import decode_avatar

PASSWORD = "testpass123"


def _csrf(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _make_user(db, *, name="Profile User", username=None, email=None, avatar=None):
    user = User(
        username=username or f"prof_{uuid.uuid4().hex[:8]}",
        name=name,
        email=email or f"prof_{uuid.uuid4().hex[:8]}@example.com",
        avatar=avatar,
        password_hash=hash_password(PASSWORD),
        role="viewer",
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    return user


def _login_client(user) -> TestClient:
    client = TestClient(app, follow_redirects=False)
    token = _csrf(client.get("/login").text)
    resp = client.post(
        "/login",
        data={"username": user.email, "password": PASSWORD, "csrf_token": token},
    )
    assert resp.status_code == 303, resp.text
    return client


def _image_bytes(size=(64, 64), fmt="JPEG"):
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 90, 200)).save(buf, fmt)
    return buf.getvalue()


def _drop(db, *users):
    for user in users:
        db.query(AuditLog).filter(AuditLog.user_id == user.id).delete()
        db.delete(user)
    db.commit()


def test_profile_requires_login():
    with TestClient(app, follow_redirects=False) as client:
        resp = client.get("/profile")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_profile_update(db):
    user = _make_user(db)
    client = _login_client(user)
    try:
        new_email = user.email
        token = _csrf(client.get("/profile").text)
        resp = client.post(
            "/profile",
            data={
                "csrf_token": token,
                "name": "Renamed Person",
                "username": "renamed_user",
                "phone": "08123456789",
            },
        )
        assert resp.status_code == 303
        db.refresh(user)
        assert user.name == "Renamed Person"
        assert user.username == "renamed_user"
        assert user.phone == "08123456789"
        assert user.email == new_email
        log = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user.id, AuditLog.action == "user.profile_update")
            .one()
        )
        assert "name" in log.detail
    finally:
        client.close()
        _drop(db, user)


def test_profile_update_requires_name(db):
    user = _make_user(db)
    client = _login_client(user)
    try:
        token = _csrf(client.get("/profile").text)
        resp = client.post("/profile", data={"csrf_token": token, "name": ""})
        assert resp.status_code == 400
        assert "Name is required" in resp.text
    finally:
        client.close()
        _drop(db, user)


def test_profile_update_rejects_duplicate_username(db):
    other = _make_user(db, username="taken_name")
    user = _make_user(db)
    client = _login_client(user)
    try:
        token = _csrf(client.get("/profile").text)
        resp = client.post(
            "/profile",
            data={"csrf_token": token, "name": "N", "username": "taken_name"},
        )
        assert resp.status_code == 400
        assert "already in use" in resp.text
    finally:
        client.close()
        _drop(db, user, other)


def test_avatar_upload_and_serve(db):
    user = _make_user(db)
    client = _login_client(user)
    try:
        token = _csrf(client.get("/profile").text)
        resp = client.post(
            "/profile/avatar",
            data={"csrf_token": token},
            files={"file": ("a.jpg", _image_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 303
        db.refresh(user)
        assert user.avatar and user.avatar.startswith("data:image/jpeg;base64,")
        assert decode_avatar(user.avatar) is not None

        img = client.get(f"/avatar/{user.id}")
        assert img.status_code == 200
        assert img.headers["content-type"] == "image/jpeg"
        assert img.content
    finally:
        client.close()
        _drop(db, user)


def test_avatar_rejects_oversize(db):
    user = _make_user(db)
    client = _login_client(user)
    try:
        token = _csrf(client.get("/profile").text)
        resp = client.post(
            "/profile/avatar",
            data={"csrf_token": token},
            files={"file": ("big.jpg", b"\x00" * (1024 * 1024 + 10), "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "larger than 1 MB" in resp.text
    finally:
        client.close()
        _drop(db, user)


def test_avatar_remove(db):
    user = _make_user(db, avatar="data:image/jpeg;base64,AAAA")
    client = _login_client(user)
    try:
        token = _csrf(client.get("/profile").text)
        resp = client.post("/profile/avatar/remove", data={"csrf_token": token})
        assert resp.status_code == 303
        db.refresh(user)
        assert user.avatar is None
    finally:
        client.close()
        _drop(db, user)


def test_avatar_service_404_when_absent(db):
    user = _make_user(db)
    client = _login_client(user)
    try:
        resp = client.get(f"/avatar/{user.id}")
        assert resp.status_code == 404
    finally:
        client.close()
        _drop(db, user)
