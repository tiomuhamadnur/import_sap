from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.db import SessionLocal
from app.importing import DATASETS
from app.models import AuditLog, ImportJob, ImportRecordResult
from app.services.importer import restore_value

logger = logging.getLogger(__name__)


def rollback_job(job_id: int, actor_id: int | None = None) -> dict[str, int]:
    """Undo the changes of a single import session, skipping records changed later."""
    db = SessionLocal()
    try:
        job = db.get(ImportJob, job_id)
        if job is None:
            raise ValueError("Import job not found")
        if job.status not in ("completed", "partial", "failed"):
            raise ValueError(f"Cannot roll back a job with status '{job.status}'")

        spec = DATASETS[job.data_type]
        model = spec.model
        restorable = [
            c
            for c in model.__table__.columns.keys()
            if c not in ("id", "created_at", "updated_at")
        ]

        undone = 0
        conflicts = 0
        missing = 0

        results = db.scalars(
            select(ImportRecordResult)
            .where(
                ImportRecordResult.job_id == job_id,
                ImportRecordResult.status.in_(("inserted", "updated")),
            )
            .order_by(ImportRecordResult.id)
            .execution_options(yield_per=1000)
        )
        for result in results:
            if result.entity_id is None:
                missing += 1
                continue
            entity = db.get(model, result.entity_id)
            if entity is None:
                missing += 1
                continue
            if getattr(entity, "import_job_id", None) != job_id:
                conflicts += 1
                continue

            if result.status == "inserted":
                db.delete(entity)
            else:
                before = result.before_data or {}
                for column in restorable:
                    if column in before:
                        setattr(entity, column, restore_value(model, column, before[column]))
            undone += 1
            if undone % 1000 == 0:
                db.flush()

        job.status = "rolled_back"
        job.rolled_back_at = datetime.now(UTC)
        summary = dict(job.error_summary or {})
        summary["rollback"] = {
            "undone": undone,
            "conflicts": conflicts,
            "missing": missing,
        }
        job.error_summary = summary
        db.add(
            AuditLog(
                user_id=actor_id,
                action="import.rollback",
                object_type="import_job",
                object_id=str(job.id),
                result="success",
                detail={"data_type": job.data_type, "undone": undone, "conflicts": conflicts},
            )
        )
        db.commit()
        return {"undone": undone, "conflicts": conflicts, "missing": missing}
    finally:
        db.close()
