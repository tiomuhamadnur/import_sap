import re
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import User
from app.security import hash_password

PASSWORD = "testpass123"


def csrf_token(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def new_client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def login(client: TestClient, username: str, password: str) -> None:
    token = csrf_token(client.get("/login").text)
    resp = client.post(
        "/login", data={"username": username, "password": password, "csrf_token": token}
    )
    assert resp.status_code == 303, resp.text


@pytest.fixture(scope="session")
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session")
def accounts(db):
    suffix = uuid.uuid4().hex[:8]
    made = {}
    for role, prefix in (("admin", "t_admin"), ("viewer", "t_viewer")):
        user = User(
            username=f"{prefix}_{suffix}",
            name=f"Test {role.title()}",
            email=f"{prefix}_{suffix}@example.com",
            password_hash=hash_password(PASSWORD),
            role=role,
            is_active=True,
            must_change_password=False,
        )
        db.add(user)
        made[role] = user
    db.commit()
    yield made
    for user in made.values():
        db.delete(user)
    db.commit()


@pytest.fixture
def admin_client(accounts):
    client = new_client()
    login(client, accounts["admin"].username, PASSWORD)
    yield client
    client.close()


@pytest.fixture
def viewer_client(accounts):
    client = new_client()
    login(client, accounts["viewer"].username, PASSWORD)
    yield client
    client.close()
