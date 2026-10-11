import sys

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.security import hash_password


def ensure_admin(db) -> User | None:
    """Create the bootstrap admin when there are no users yet."""
    existing = db.scalar(select(User).limit(1))
    if existing is not None:
        return None
        admin = User(
            username=settings.bootstrap_admin_username,
            name="Administrator",
            email=settings.bootstrap_admin_email or "admin@mrtjakarta.co.id",
            password_hash=hash_password(settings.bootstrap_admin_password),
            role="admin",
            is_active=True,
            must_change_password=True,
        )
    db.add(admin)
    db.commit()
    return admin


def bootstrap_admin() -> None:
    db = SessionLocal()
    try:
        created = ensure_admin(db)
        if created:
            print(f"[bootstrap] admin user '{created.username}' created")
    finally:
        db.close()


def _reset_password(username: str, password: str) -> int:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            print(f"user '{username}' not found")
            return 1
        user.password_hash = hash_password(password)
        user.must_change_password = True
        db.commit()
        print(f"[ok] password reset for '{username}' (must change on next login)")
        return 0
    finally:
        db.close()


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "reset-password":
        if len(argv) != 3:
            print("usage: python -m app.seed reset-password <username> <password>")
            return 2
        return _reset_password(argv[1], argv[2])
    print("usage: python -m app.seed reset-password <username> <password>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
