from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# preview -> queued -> running -> completed | partial | failed
# terminal alternatives: cancelled, rolled_back
IMPORT_JOB_STATUSES = (
    "preview",
    "queued",
    "running",
    "completed",
    "partial",
    "failed",
    "rolled_back",
    "cancelled",
)
TERMINAL_JOB_STATUSES = ("completed", "partial", "failed", "rolled_back", "cancelled")

RECORD_STATUSES = ("inserted", "updated", "skipped", "failed")

DATA_TYPES = (
    "notification",
    "work_order",
    "measuring_document",
    "measuring_point",
    "equipment",
    "functional_location",
)


class ImportJob(Base):
    __tablename__ = "import_job"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    data_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), default="preview", index=True)
    filename: Mapped[str | None] = mapped_column(String(255))
    storage_path: Mapped[str | None] = mapped_column(String(512))
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    preview: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class ImportRecordResult(Base):
    __tablename__ = "import_record_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("import_job.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), index=True)
    key: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    message: Mapped[str | None] = mapped_column(String(1000))
    raw_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
