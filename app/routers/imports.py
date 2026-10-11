from __future__ import annotations

import os
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.config import settings
from app.dependencies import AdminDep, CsrfDep, DbDep, RequireUserDep
from app.importing import (
    DATASETS,
    extra_columns,
    preview,
    read_headers,
    rows_iterator,
    validate_structure,
)
from app.models import IMPORT_JOB_STATUSES, AuditLog, ImportJob, ImportRecordResult, User
from app.services.importer import existing_keys
from app.services.rollback import rollback_job
from app.templating import render

router = APIRouter(tags=["import"])

IMPORT_OPTIONS = ("valid_only", "abort")
ALLOWED_SUFFIXES = (".xlsx", ".xlsm", ".csv")


def _dataset_list() -> list[dict[str, str]]:
    return [
        {"value": key, "label": spec.title} for key, spec in DATASETS.items()
    ]


def _get_job(db, job_id: int) -> ImportJob:
    job = db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


def _user_map(db, jobs) -> dict[int, User]:
    ids = {job.user_id for job in jobs if job.user_id}
    if not ids:
        return {}
    users = db.scalars(select(User).where(User.id.in_(ids))).all()
    return {user.id: user for user in users}


def _remove_file(job: ImportJob) -> None:
    if job.storage_path:
        Path(job.storage_path).unlink(missing_ok=True)


def _validate_content(path: Path, suffix: str) -> None:
    """Reject files whose content does not match their declared extension."""
    with open(path, "rb") as fh:
        head = fh.read(4096)

    if suffix in (".xlsx", ".xlsm"):
        if head[:4] != b"PK\x03\x04":
            raise ValueError("The file is not a valid Excel (.xlsx) file.")
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
        except zipfile.BadZipFile as exc:
            raise ValueError("The Excel file is corrupted or unreadable.") from exc
        if not any(name.startswith("xl/") for name in names):
            raise ValueError("The file is not a valid Excel workbook.")

    if suffix == ".csv":
        if b"\x00" in head:
            raise ValueError("The CSV file contains binary data.")
        if not head.strip():
            raise ValueError("The file is empty.")


async def _save_upload(upload: UploadFile, dest: Path, limit_bytes: int) -> int:
    size = 0
    with open(dest, "wb") as fh:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > limit_bytes:
                fh.close()
                dest.unlink(missing_ok=True)
                raise ValueError(
                    f"File exceeds the maximum size of {settings.max_upload_size_mb} MB."
                )
            fh.write(chunk)
    return size


@router.get("/")
def import_page(request: Request, db: DbDep, current_user: RequireUserDep):
    if not current_user.is_admin:
        return RedirectResponse("/notification", status_code=303)
    recent = list(
        db.scalars(select(ImportJob).order_by(ImportJob.created_at.desc()).limit(5)).all()
    )
    return render(
        request,
        "import.html",
        active="Import",
        current_user=current_user,
        datasets=_dataset_list(),
        recent=recent,
        user_map=_user_map(db, recent),
        selected_type=None,
        error=None,
    )


@router.post("/import/upload")
async def import_upload(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    data_type: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
):
    def fail(message: str, warnings: list[str] | None = None):
        return render(
            request,
            "import.html",
            active="Import",
            current_user=current_user,
            datasets=_dataset_list(),
            recent=[],
            user_map={},
            selected_type=data_type if data_type in DATASETS else None,
            error=message,
            warnings=warnings or [],
            status_code=400,
        )

    if data_type not in DATASETS:
        return fail("Please choose a valid data type.")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return fail("Unsupported file type. Upload an Excel (.xlsx) or CSV (.csv) file.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    dest = Path(settings.upload_dir) / f"{uuid.uuid4().hex}{suffix}"
    limit_bytes = settings.max_upload_size_mb * 1024 * 1024
    try:
        await _save_upload(file, dest, limit_bytes)
        _validate_content(dest, suffix)
    except ValueError as exc:
        dest.unlink(missing_ok=True)
        return fail(str(exc))

    spec = DATASETS[data_type]
    try:
        headers = read_headers(dest)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        return fail(f"Could not read the file: {exc}")

    missing = validate_structure(spec, headers)
    if missing:
        dest.unlink(missing_ok=True)
        return fail(
            "The file structure is invalid. Missing required column(s): "
            + ", ".join(f'"{m}"' for m in missing)
            + ". Import was rejected."
        )

    extras = extra_columns(spec, headers)
    existing = existing_keys(db, spec.model, [k.field for k in spec.keys])
    result = preview(spec, rows_iterator(dest), existing, settings.preview_error_sample)

    job = ImportJob(
        user_id=current_user.id,
        data_type=data_type,
        status="preview",
        filename=file.filename,
        storage_path=str(dest),
        options={"on_invalid": "valid_only"},
    )
    preview_payload = result.to_dict()
    preview_payload["extra_columns"] = extras
    job.preview = preview_payload
    db.add(job)
    db.commit()
    return RedirectResponse(f"/import/{job.id}/preview", status_code=303)


@router.get("/import/{job_id}/preview")
def import_preview(request: Request, db: DbDep, current_user: AdminDep, job_id: int):
    job = _get_job(db, job_id)
    if job.status != "preview":
        return RedirectResponse(f"/import/{job.id}", status_code=303)
    return render(
        request,
        "import_preview.html",
        active="Import",
        current_user=current_user,
        job=job,
        spec=DATASETS[job.data_type],
        preview=job.preview or {},
        options=IMPORT_OPTIONS,
        error=None,
    )


@router.post("/import/{job_id}/confirm")
def import_confirm(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    job_id: int,
    on_invalid: Annotated[str, Form()] = "valid_only",
):
    from app.queue import enqueue_import

    job = _get_job(db, job_id)
    if job.status != "preview":
        return RedirectResponse(f"/import/{job.id}", status_code=303)

    on_invalid = on_invalid if on_invalid in IMPORT_OPTIONS else "valid_only"
    job.options = {**(job.options or {}), "on_invalid": on_invalid}
    job.status = "queued"
    job.queued_at = datetime.now(UTC)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="import.start",
            object_type="import_job",
            object_id=str(job.id),
            result="success",
            detail={"data_type": job.data_type, "filename": job.filename, "on_invalid": on_invalid},
        )
    )
    db.commit()
    try:
        enqueue_import(job.id, job.data_type)
    except Exception:
        job.status = "failed"
        job.error_summary = {"error": "Could not enqueue the job (queue unavailable)."}
        db.commit()
    return RedirectResponse(f"/import/{job.id}", status_code=303)


@router.post("/import/{job_id}/cancel")
def import_cancel(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    job_id: int,
):
    job = _get_job(db, job_id)
    if job.status == "preview":
        _remove_file(job)
        db.delete(job)
        db.commit()
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/import/{job.id}", status_code=303)


@router.get("/import-history")
def import_history(
    request: Request,
    db: DbDep,
    current_user: RequireUserDep,
    data_type: str | None = None,
    status: str | None = None,
    page: int = 1,
):
    page = max(1, page)
    per_page = 20
    stmt = select(ImportJob).order_by(ImportJob.created_at.desc())
    if data_type in DATASETS:
        stmt = stmt.where(ImportJob.data_type == data_type)
    if status in IMPORT_JOB_STATUSES:
        stmt = stmt.where(ImportJob.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    jobs = list(db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all())
    return render(
        request,
        "import_history.html",
        active="Import History",
        current_user=current_user,
        jobs=jobs,
        user_map=_user_map(db, jobs),
        datasets=_dataset_list(),
        data_type=data_type if data_type in DATASETS else None,
        status=status if status in IMPORT_JOB_STATUSES else None,
        statuses=IMPORT_JOB_STATUSES,
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/import/{job_id}")
def import_detail(request: Request, db: DbDep, current_user: RequireUserDep, job_id: int):
    job = _get_job(db, job_id)
    actor = db.get(User, job.user_id) if job.user_id else None
    return render(
        request,
        "import_job.html",
        active="Import History",
        current_user=current_user,
        job=job,
        actor=actor,
        spec=DATASETS.get(job.data_type),
        error=request.query_params.get("error"),
    )


@router.get("/import/{job_id}/status")
def import_status(request: Request, db: DbDep, current_user: RequireUserDep, job_id: int):
    job = _get_job(db, job_id)
    return render(
        request,
        "_import_status.html",
        job=job,
        statuses=IMPORT_JOB_STATUSES,
    )


@router.get("/import/{job_id}/errors")
def import_errors(
    request: Request,
    db: DbDep,
    current_user: RequireUserDep,
    job_id: int,
    page: int = 1,
):
    job = _get_job(db, job_id)
    page = max(1, page)
    per_page = 50
    stmt = (
        select(ImportRecordResult)
        .where(
            ImportRecordResult.job_id == job_id,
            ImportRecordResult.status.in_(("skipped", "failed")),
        )
        .order_by(ImportRecordResult.row_number)
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    results = list(db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all())
    return render(
        request,
        "_import_errors.html",
        job=job,
        results=results,
        page=page,
        per_page=per_page,
        total=total,
    )


@router.post("/import/{job_id}/rollback")
def import_rollback(
    request: Request,
    db: DbDep,
    current_user: AdminDep,
    _csrf: CsrfDep,
    job_id: int,
):
    job = _get_job(db, job_id)
    if job.status not in ("completed", "partial", "failed"):
        return RedirectResponse(f"/import/{job.id}?error=Cannot+rollback", status_code=303)
    try:
        rollback_job(job.id, actor_id=current_user.id)
    except Exception:
        db.rollback()
        return RedirectResponse(
            f"/import/{job.id}?error=Rollback+failed", status_code=303
        )
    return RedirectResponse(f"/import/{job.id}", status_code=303)
