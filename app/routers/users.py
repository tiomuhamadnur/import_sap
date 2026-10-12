from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, or_, select

from app.dependencies import ROLE_ADMIN, ROLE_VIEWER, AdminDep, CsrfDep, DbDep
from app.models import AuditLog, User
from app.security import hash_password, password_error
from app.templating import get_csrf_token, render, templates

router = APIRouter(tags=["users"], prefix="/users")

_cells = templates.env.get_template("_cells.html").module

_USER_SORT = {
    "name": User.name,
    "email": User.email,
    "phone": User.phone,
    "role": User.role,
    "is_active": User.is_active,
    "must_change_password": User.must_change_password,
}


def _log(db, actor_id: int, action: str, target: User, result: str = "success", detail=None):
    db.add(
        AuditLog(
            user_id=actor_id,
            action=action,
            object_type="user",
            object_id=str(target.id),
            result=result,
            detail=detail or {"email": target.email or target.username or "", "name": target.name or ""},
        )
    )


def _list_users(db) -> list[User]:
    return list(db.scalars(select(User).order_by(User.name, User.email)).all())


@router.get("")
def list_users(request: Request, db: DbDep, current_user: AdminDep):
    return render(
        request,
        "users.html",
        active="Manage Users",
        current_user=current_user,
        users=_list_users(db),
        error=None,
    )

@router.get("/data")
def users_table(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    draw: int = 0,
    start: int = 0,
    length: int = 25,
    q: str | None = None,
    sort: str | None = None,
    dir: str = "asc",
):
    length = max(1, min(length, 500))
    start = max(0, start)
    direction = "desc" if dir == "desc" else "asc"

    stmt = select(User)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                User.name.ilike(needle),
                User.username.ilike(needle),
                User.email.ilike(needle),
                User.phone.ilike(needle),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    sort_col = _USER_SORT.get(sort or "", User.name)
    stmt = stmt.order_by(sort_col.desc() if direction == "desc" else sort_col.asc(), User.id.asc())
    users = list(db.scalars(stmt.offset(start).limit(length)).all())

    csrf = get_csrf_token(request)
    data = [
        {
            "identity": str(_cells.user_identity(u)),
            "email": str(_cells.user_email(u)),
            "phone": str(_cells.user_phone(u)),
            "role": str(_cells.user_role(u)),
            "status": str(_cells.user_status(u)),
            "password": str(_cells.user_password(u)),
            "actions": str(_cells.user_actions(u, csrf)),
        }
        for u in users
    ]
    return JSONResponse(
        {"draw": draw, "recordsTotal": total, "recordsFiltered": total, "data": data}
    )


@router.get("/new")
def new_user_page(request: Request, current_user: AdminDep):
    return render(
        request,
        "user_form.html",
        active="Manage Users",
        current_user=current_user,
        user=None,
        error=None,
        form=None,
    )

@router.post("/new")
def create_user(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    username: Annotated[str | None, Form()] = None,
    email: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    phone: Annotated[str | None, Form()] = None,
    password: Annotated[str, Form()] = "",
    role: Annotated[str, Form()] = ROLE_VIEWER,
) -> Response:
    username = (username or "").strip() or None
    email = (email or "").strip().lower()
    name = (name or "").strip()
    phone = (phone or "").strip() or None
    role = role if role in (ROLE_ADMIN, ROLE_VIEWER) else ROLE_VIEWER

    existing = None
    if email:
        existing = db.scalar(select(User).where(func.lower(User.email) == email))
    if existing is None and username:
        existing = db.scalar(select(User).where(User.username == username))
    error = None
    if not name:
        error = "Name is required."
    elif not email:
        error = "Email is required."
    elif "@" not in email:
        error = "Invalid email address."
    elif existing is not None:
        error = "Email or username already exists."
    else:
        error = password_error(password, username, email)

    if error:
        return render(
            request,
            "user_form.html",
            active="Manage Users",
            current_user=current_user,
            user=None,
            error=error,
            form={
                "username": username or "",
                "name": name,
                "email": email,
                "phone": phone or "",
                "role": role,
            },
            status_code=400,
        )

    user = User(
        username=username,
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    _log(db, current_user.id, "user.create", user, detail={"username": username, "role": role})
    db.commit()
    return RedirectResponse("/users", status_code=303)

@router.get("/{user_id}/edit")
def edit_user_page(request: Request, db: DbDep, current_user: AdminDep, user_id: int):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return render(
        request,
        "user_form.html",
        active="Manage Users",
        current_user=current_user,
        user=user,
        error=None,
        form=None,
    )

@router.post("/{user_id}")
def update_user(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    user_id: int,
    role: Annotated[str, Form()] = ROLE_VIEWER,
    is_active: Annotated[str | None, Form()] = None,
    name: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    username: Annotated[str | None, Form()] = None,
    phone: Annotated[str | None, Form()] = None,
) -> Response:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    name = (name or "").strip()
    email = (email or "").strip().lower() or None
    username = (username or "").strip() or None
    phone = (phone or "").strip() or None
    role = role if role in (ROLE_ADMIN, ROLE_VIEWER) else user.role
    active = is_active is not None

    error = None
    if user.id == current_user.id and (role != ROLE_ADMIN or not active):
        error = "You cannot remove your own admin access or deactivate yourself."
    if error is None and email:
        existing = db.scalar(
            select(User).where(func.lower(User.email) == email, User.id != user.id)
        )
        if existing:
            error = "Email already in use."
    if error is None and username:
        existing = db.scalar(select(User).where(User.username == username, User.id != user.id))
        if existing:
            error = "Username already in use."
    if error is None and not name:
        error = "Name is required."
    if error is None and not email:
        error = "Email is required."
    if error is None and email and "@" not in email:
        error = "Invalid email address."

    if error:
        return render(
            request,
            "user_form.html",
            active="Manage Users",
            current_user=current_user,
            user=user,
            error=error,
            form=None,
            status_code=400,
        )

    changes = {}
    if user.name != name:
        changes["name"] = f"{user.name} -> {name}"
        user.name = name
    if user.email != email:
        changes["email"] = f"{user.email} -> {email}"
        user.email = email
    if user.username != username:
        changes["username"] = f"{user.username} -> {username}"
        user.username = username
    if user.phone != phone:
        changes["phone"] = f"{user.phone} -> {phone}"
        user.phone = phone
    if user.role != role:
        changes["role"] = f"{user.role} -> {role}"
        user.role = role
    if user.is_active != active:
        changes["is_active"] = active
        user.is_active = active

    if changes:
        _log(db, current_user.id, "user.update", user, detail={"username": user.username, **changes})
        db.commit()
    return RedirectResponse("/users", status_code=303)

@router.post("/{user_id}/reset-password")
def reset_password(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    user_id: int,
    new_password: Annotated[str, Form()],
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    error = password_error(new_password, user.username, user.email)
    if error:
        return render(
            request,
            "users.html",
            active="Manage Users",
            current_user=current_user,
            users=_list_users(db),
            error=error,
            status_code=400,
        )

    user.password_hash = hash_password(new_password)
    user.must_change_password = True
    _log(db, current_user.id, "user.reset_password", user)
    db.commit()
    return RedirectResponse("/users", status_code=303)
