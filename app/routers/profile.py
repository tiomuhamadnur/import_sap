from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select

from app.dependencies import CsrfDep, DbDep, RequireUserDep
from app.models import AuditLog, User
from app.services.avatar import MAX_SOURCE_BYTES, decode_avatar, make_avatar_data_uri
from app.templating import render

router = APIRouter(tags=["profile"])


def _profile_response(request: Request, db, current_user, user, *, error=None, status_code=200):
    return render(
        request,
        "profile.html",
        active=None,
        current_user=current_user,
        user=user,
        error=error,
        info=request.query_params.get("info"),
        status_code=status_code,
    )


@router.get("/profile")
def profile_page(request: Request, db: DbDep, current_user: RequireUserDep):
    user = db.get(User, current_user.id)
    return _profile_response(request, db, current_user, user)


@router.post("/profile")
def update_profile(
    request: Request,
    db: DbDep,
    current_user: RequireUserDep,
    _csrf: CsrfDep,
    name: Annotated[str, Form()] = "",
    username: Annotated[str | None, Form()] = None,
    phone: Annotated[str | None, Form()] = None,
):
    user = db.get(User, current_user.id)
    name = (name or "").strip()
    username = (username or "").strip() or None
    phone = (phone or "").strip() or None

    error = None
    if not name:
        error = "Name is required."
    if error is None and username:
        existing = db.scalar(select(User).where(User.username == username, User.id != user.id))
        if existing:
            error = "Username already in use."

    if error:
        return _profile_response(request, db, current_user, user, error=error, status_code=400)

    changes: dict[str, str] = {}
    if user.name != name:
        changes["name"] = f"{user.name} -> {name}"
        user.name = name
    if user.username != username:
        changes["username"] = f"{user.username} -> {username}"
        user.username = username
    if user.phone != phone:
        changes["phone"] = f"{user.phone} -> {phone}"
        user.phone = phone

    if changes:
        db.add(
            AuditLog(
                user_id=user.id,
                action="user.profile_update",
                object_type="user",
                object_id=str(user.id),
                result="success",
                detail=changes,
            )
        )
        db.commit()
    return RedirectResponse("/profile?info=Profile+updated", status_code=303)


@router.post("/profile/avatar")
async def update_avatar(
    request: Request,
    db: DbDep,
    current_user: RequireUserDep,
    _csrf: CsrfDep,
    file: Annotated[UploadFile, File()],
):
    user = db.get(User, current_user.id)
    raw = await file.read(MAX_SOURCE_BYTES + 1)
    try:
        avatar = make_avatar_data_uri(raw)
    except ValueError as exc:
        return _profile_response(request, db, current_user, user, error=str(exc), status_code=400)

    user.avatar = avatar
    db.add(
        AuditLog(
            user_id=user.id,
            action="user.avatar_update",
            object_type="user",
            object_id=str(user.id),
            result="success",
        )
    )
    db.commit()
    return RedirectResponse("/profile?info=Photo+updated", status_code=303)


@router.post("/profile/avatar/remove")
def remove_avatar(
    request: Request,
    db: DbDep,
    current_user: RequireUserDep,
    _csrf: CsrfDep,
):
    user = db.get(User, current_user.id)
    user.avatar = None
    db.add(
        AuditLog(
            user_id=user.id,
            action="user.avatar_remove",
            object_type="user",
            object_id=str(user.id),
            result="success",
        )
    )
    db.commit()
    return RedirectResponse("/profile?info=Photo+removed", status_code=303)


@router.get("/avatar/{user_id}")
def avatar_image(db: DbDep, current_user: RequireUserDep, user_id: int):
    user = db.get(User, user_id)
    decoded = decode_avatar(user.avatar) if user else None
    if not decoded:
        raise HTTPException(status_code=404, detail="No avatar")
    mime, data = decoded
    return Response(
        content=data,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=300"},
    )
