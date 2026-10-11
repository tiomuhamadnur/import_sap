from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import insert, select, tuple_
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.importing import (
    DATASETS,
    iter_records,
    key_dict,
    row_key,
    rows_iterator,
)
from app.models import TERMINAL_JOB_STATUSES, ImportJob, ImportRecordResult
from app.services.upsert import upsert_batch_returning

logger = logging.getLogger(__name__)

SNAPSHOT_EXCLUDED = ("id", "public_id", "created_at", "updated_at")


def jsonable(value: Any) -> Any:
    """Serialize a DB value for JSONB storage."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def snapshot_columns(model: type) -> list[str]:
    return [c for c in model.__table__.columns.keys() if c not in SNAPSHOT_EXCLUDED]


def snapshot(instance: Any, columns: list[str]) -> dict[str, Any]:
    return {c: jsonable(getattr(instance, c)) for c in columns}


def restore_value(model: type, column: str, value: Any) -> Any:
    """Convert a JSON-stored snapshot value back to the column's python type."""
    if value is None:
        return None
    col_type = model.__table__.columns[column].type
    type_name = type(col_type).__name__
    if type_name in ("DateTime", "TIMESTAMP") and isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    if type_name in ("Integer", "BigInteger") and isinstance(value, str):
        return int(value)
    if type_name.startswith("Numeric") and isinstance(value, str | int | float):
        return Decimal(str(value))
    return value


def existing_keys(db: Session, model: type, key_fields: list[str]) -> set[tuple[str, ...]]:
    """Return the set of composite keys currently stored for a data type."""
    cols = [getattr(model, kf) for kf in key_fields]
    rows = db.execute(select(*cols)).all()
    return {tuple(str(v) for v in row) for row in rows}


def _fetch_existing(
    db: Session, model: type, key_fields: list[str], keys: list[tuple[Any, ...]]
) -> dict[tuple[str, ...], Any]:
    if not keys:
        return {}
    cols = [getattr(model, kf) for kf in key_fields]
    rows = db.execute(select(model).where(tuple_(*cols).in_(keys))).scalars().all()
    out: dict[tuple[str, ...], Any] = {}
    for obj in rows:
        out[tuple(str(getattr(obj, kf)) for kf in key_fields)] = obj
    return out


def process_import(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(ImportJob, job_id)
        if job is None:
            logger.warning("import job %s not found", job_id)
            return
        if job.status in ("cancelled", "rolled_back"):
            return

        spec = DATASETS[job.data_type]
        key_fields = [k.field for k in spec.keys]
        on_invalid = (job.options or {}).get("on_invalid", "valid_only")
        snap_cols = snapshot_columns(spec.model)

        job.status = "running"
        job.started_at = datetime.now(UTC)
        db.commit()

        batch_size = max(1, settings.batch_size)
        batch: list[tuple[int, dict[str, Any]]] = []

        for number, values, errors in iter_records(spec, rows_iterator(job.storage_path)):
            job.processed += 1
            if errors:
                if on_invalid == "abort":
                    _append_results(
                        db,
                        job.id,
                        [
                            _result_row(
                                number, "skipped", key=None, message="; ".join(errors)
                            )
                        ],
                    )
                    job.skipped += 1
                    _finish(db, job, status="failed", summary={"aborted_on_row": number})
                    return
                _append_results(
                    db,
                    job.id,
                    [_result_row(number, "skipped", key=None, message="; ".join(errors))],
                )
                job.skipped += 1
                continue

            job.total_rows += 1
            batch.append((number, values))
            if len(batch) >= batch_size:
                _flush_batch(db, job, spec, key_fields, snap_cols, batch)
                batch = []

        if batch:
            _flush_batch(db, job, spec, key_fields, snap_cols, batch)

        success = job.inserted + job.updated
        problems = job.skipped + job.failed
        if problems == 0:
            status = "completed"
        elif success > 0:
            status = "partial"
        else:
            status = "failed"
        _finish(db, job, status=status)
    except Exception as exc:  # pragma: no cover - worker safety
        logger.exception("import job %s failed", job_id)
        try:
            job = db.get(ImportJob, job_id)
            if job is not None:
                _finish(db, job, status="failed", summary={"error": str(exc)})
        except Exception:
            db.rollback()
    finally:
        _discard_source(db, job_id)
        db.close()


def _discard_source(db: Session, job_id: int) -> None:
    """Delete the temporary source file once the job has reached a terminal state."""
    try:
        job = db.get(ImportJob, job_id)
        if job is not None and job.storage_path and job.status in TERMINAL_JOB_STATUSES:
            Path(job.storage_path).unlink(missing_ok=True)
            job.storage_path = None
            db.commit()
    except Exception:  # pragma: no cover - cleanup best effort
        db.rollback()


def _flush_batch(
    db: Session,
    job: ImportJob,
    spec: Any,
    key_fields: list[str],
    snap_cols: list[str],
    batch: list[tuple[int, dict[str, Any]]],
) -> None:
    keys = [row_key(spec, values) for _, values in batch]
    existing = _fetch_existing(db, spec.model, key_fields, keys)

    rows = []
    for _, values in batch:
        payload = dict(values)
        payload["import_job_id"] = job.id
        rows.append(payload)

    returned = upsert_batch_returning(db, spec.model, key_fields, rows)
    id_map = {
        tuple(str(r[i + 1]) for i in range(len(key_fields))): r[0] for r in returned
    }

    results = []
    for number, values in batch:
        key = row_key(spec, values)
        entity_id = id_map.get(key)
        if key in existing:
            before = snapshot(existing[key], snap_cols)
            results.append(
                _result_row(number, "updated", key_dict(spec, values), entity_id, before)
            )
            job.updated += 1
        else:
            results.append(
                _result_row(number, "inserted", key_dict(spec, values), entity_id)
            )
            job.inserted += 1

    _append_results(db, job.id, results)
    db.commit()


def _result_row(
    row_number: int,
    status: str,
    key: dict[str, Any] | None,
    entity_id: int | None = None,
    before_data: dict[str, Any] | None = None,
    message: str | None = None,
    raw_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "job_id": None,
        "row_number": row_number,
        "status": status,
        "key": key,
        "entity_id": entity_id,
        "before_data": before_data,
        "message": message,
        "raw_values": raw_values,
    }


def _append_results(db: Session, job_id: int, results: list[dict[str, Any]]) -> None:
    if not results:
        return
    for r in results:
        r["job_id"] = job_id
    db.execute(insert(ImportRecordResult), results)


def _finish(
    db: Session,
    job: ImportJob,
    status: str,
    summary: dict[str, Any] | None = None,
) -> None:
    job.status = status
    job.finished_at = datetime.now(UTC)
    if summary:
        merged = dict(job.error_summary or {})
        merged.update(summary)
        job.error_summary = merged
    db.commit()
