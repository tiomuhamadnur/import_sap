import secrets
from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.templating import CSRF_SESSION_KEY

DbDep = Annotated[Session, Depends(get_db)]

ROLE_ADMIN = "admin"
ROLE_VIEWER = "viewer"


class CurrentUser:
    def __init__(self, user: User):
        self._user = user

    @property
    def username(self) -> str:
        return self._user.username or self._user.email or ""

    @property
    def name(self) -> str | None:
        return self._user.name

    @property
    def email(self) -> str | None:
        return self._user.email

    @property
    def phone(self) -> str | None:
        return self._user.phone

    @property
    def avatar(self) -> str | None:
        return self._user.avatar

    @property
    def has_avatar(self) -> bool:
        return bool(self._user.avatar)

    @property
    def display_name(self) -> str:
        return self._user.name or self._user.username or self._user.email or "User"

    @property
    def initials(self) -> str:
        base = self._user.name or self._user.username or self._user.email or "?"
        parts = base.split()
        if len(parts) >= 2:
            return (parts[0][:1] + parts[1][:1]).upper()
        return base[:2].upper() if base else "?"
    @property
    def role(self) -> str:
        return self._user.role

    @property
    def is_admin(self) -> bool:
        return self._user.role == ROLE_ADMIN

    @property
    def id(self) -> int:
        return self._user.id

    @property
    def must_change_password(self) -> bool:
        return self._user.must_change_password

    def __getattr__(self, item):
        return getattr(self._user, item)




def get_current_user(request: Request, db: DbDep) -> CurrentUser | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return CurrentUser(user)


CurrentUserDep = Annotated[CurrentUser | None, Depends(get_current_user)]


def require_user(
    request: Request,
    current_user: CurrentUserDep,
) -> CurrentUser:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )
    if current_user.must_change_password and request.url.path != "/change-password":
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/change-password"}
        )
    return current_user


RequireUserDep = Annotated[CurrentUser, Depends(require_user)]


def admin_required(current_user: RequireUserDep) -> CurrentUser:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


AdminDep = Annotated[CurrentUser, Depends(admin_required)]


def verify_csrf(
    request: Request,
    csrf_token: Annotated[str, Form()] = "",
) -> None:
    expected = request.session.get(CSRF_SESSION_KEY)
    if not expected or not csrf_token or not secrets.compare_digest(csrf_token, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


CsrfDep = Annotated[None, Depends(verify_csrf)]


def load_user_by_username(db: Session, username: str) -> User | None:
    ident = (username or "").strip()
    if not ident:
        return None
    stmt = select(User).where(
        or_(User.username == ident, func.lower(User.email) == ident.lower())
    )
    return db.scalar(stmt)


# alias for clarity
load_user_by_identifier = load_user_by_username


