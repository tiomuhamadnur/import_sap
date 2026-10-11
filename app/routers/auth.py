from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import CsrfDep, get_current_user, load_user_by_identifier
from app.models import AuditLog, User
from app.security import hash_password, password_error, verify_password
from app.templating import render

router = APIRouter(tags=["auth"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/login")
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html", error=None)


@router.post("/login")
def login(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = load_user_by_identifier(db, username)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        db.add(AuditLog(action="login.failed", result="failed", detail={"username": username}))
        db.commit()
        return render(
            request,
            "login.html",
            error="Invalid username or password.",
            status_code=401,
        )

    request.session["user_id"] = user.id
    db.add(AuditLog(user_id=user.id, action="login.success", result="success"))
    db.commit()
    if user.must_change_password:
        return RedirectResponse("/change-password", status_code=303)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request, db: DbDep, _csrf: CsrfDep):
    user_id = request.session.get("user_id")
    if user_id is not None:
        db.add(AuditLog(user_id=user_id, action="logout", result="success"))
        db.commit()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/change-password")
def change_password_page(request: Request, db: DbDep):
    current = get_current_user(request, db)
    if current is None:
        return RedirectResponse("/login", status_code=303)
    return render(request, "change_password.html", error=None, forced=current.must_change_password)


@router.post("/change-password")
def change_password(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    current_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    confirm_password: Annotated[str, Form()],
):
    current = get_current_user(request, db)
    if current is None:
        return RedirectResponse("/login", status_code=303)

    user = db.get(User, current.id)
    forced = bool(user.must_change_password)

    error = None
    if not verify_password(current_password, user.password_hash):
        error = "Current password is incorrect."
    elif new_password != confirm_password:
        error = "New password and confirmation do not match."
    else:
        error = password_error(new_password, user.username or user.email)

    if error:
        return render(
            request, "change_password.html", error=error, forced=forced, status_code=400
        )

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.add(AuditLog(user_id=user.id, action="user.change_password", result="success"))
    db.commit()
    return RedirectResponse("/", status_code=303)
