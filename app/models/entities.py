from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, server_default=func.gen_random_uuid(), unique=True, index=True
    )
    equipment_number: Mapped[str] = mapped_column(String(64), unique=True)
    equipment_category: Mapped[str | None] = mapped_column(String(32))
    tech_id_no: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(500))
    functional_location: Mapped[str | None] = mapped_column(String(64), index=True)
    maint_plant: Mapped[str | None] = mapped_column(String(32), index=True)
    cost_center: Mapped[str | None] = mapped_column(String(64))
    planning_plant: Mapped[str | None] = mapped_column(String(32))
    planner_group: Mapped[str | None] = mapped_column(String(32), index=True)
    main_work_center: Mapped[str | None] = mapped_column(String(32))
    material: Mapped[str | None] = mapped_column(String(64))
    system_status: Mapped[str | None] = mapped_column(String(255))
    asset: Mapped[str | None] = mapped_column(String(64))
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    serial_number: Mapped[str | None] = mapped_column(String(255))
    object_number: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(255))
    acquisition_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_by: Mapped[str | None] = mapped_column(String(64))
    changed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_job.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FunctionalLocation(Base):
    __tablename__ = "functional_location"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, server_default=func.gen_random_uuid(), unique=True, index=True
    )
    functional_location: Mapped[str] = mapped_column(String(64), unique=True)
    funcloc_category: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(String(500))
    sup_funcloc: Mapped[str | None] = mapped_column(String(64), index=True)
    maint_plant: Mapped[str | None] = mapped_column(String(32), index=True)
    cost_center: Mapped[str | None] = mapped_column(String(64))
    planner_group: Mapped[str | None] = mapped_column(String(32), index=True)
    main_work_center: Mapped[str | None] = mapped_column(String(32))
    str_indicator: Mapped[str | None] = mapped_column(String(32))
    equip_installed: Mapped[str | None] = mapped_column(String(32))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_job.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MeasuringDocument(Base):
    __tablename__ = "measuring_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, server_default=func.gen_random_uuid(), unique=True, index=True
    )
    meas_document: Mapped[str] = mapped_column(String(64), unique=True)
    measuring_point: Mapped[str | None] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    measurement_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    measurement_value: Mapped[float | None] = mapped_column(Numeric(18, 6))
    difference: Mapped[float | None] = mapped_column(Numeric(18, 6))
    charact_unit: Mapped[str | None] = mapped_column(String(32))
    measured_position: Mapped[str | None] = mapped_column(String(128))
    equipment: Mapped[str | None] = mapped_column(String(64), index=True)
    functional_location: Mapped[str | None] = mapped_column(String(64), index=True)
    notification: Mapped[str | None] = mapped_column(String(64), index=True)
    order: Mapped[str | None] = mapped_column(String(64), index=True)
    counter_reading: Mapped[float | None] = mapped_column(Numeric(18, 6))
    target_value: Mapped[float | None] = mapped_column(Numeric(18, 6))
    upper_mr_limit: Mapped[float | None] = mapped_column(Numeric(18, 6))
    lower_mr_limit: Mapped[float | None] = mapped_column(Numeric(18, 6))
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_job.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MeasuringPoint(Base):
    __tablename__ = "measuring_point"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, server_default=func.gen_random_uuid(), unique=True, index=True
    )
    measuring_point: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    equipment: Mapped[str | None] = mapped_column(String(64), index=True)
    functional_location: Mapped[str | None] = mapped_column(String(64), index=True)
    measured_position: Mapped[str | None] = mapped_column(String(128))
    characteristic: Mapped[str | None] = mapped_column(String(128))
    charact_unit: Mapped[str | None] = mapped_column(String(32))
    reading_transfer: Mapped[str | None] = mapped_column(String(32))
    annual_estimate: Mapped[float | None] = mapped_column(Numeric(18, 6))
    upper_mr_limit: Mapped[float | None] = mapped_column(Numeric(18, 6))
    lower_mr_limit: Mapped[float | None] = mapped_column(Numeric(18, 6))
    counter: Mapped[str | None] = mapped_column(String(32))
    decimal_places: Mapped[str | None] = mapped_column(String(8))
    float_point_exp: Mapped[str | None] = mapped_column(String(8))
    internal_meas_unit: Mapped[str | None] = mapped_column(String(32))
    internal_char: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str | None] = mapped_column(String(8))
    meas_point_category: Mapped[str | None] = mapped_column(String(8))
    meas_range_unit: Mapped[str | None] = mapped_column(String(32))
    measurement_object_number: Mapped[str | None] = mapped_column(String(64))
    client: Mapped[str | None] = mapped_column(String(16))
    supported: Mapped[str | None] = mapped_column(String(8))
    transfer_mode: Mapped[str | None] = mapped_column(String(32))
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_by: Mapped[str | None] = mapped_column(String(64))
    changed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_job.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, server_default=func.gen_random_uuid(), unique=True, index=True
    )
    notification: Mapped[str] = mapped_column(String(64), unique=True)
    notif_type: Mapped[str | None] = mapped_column(String(32), index=True)
    notif_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    description: Mapped[str | None] = mapped_column(String(1000))
    system_status: Mapped[str | None] = mapped_column(String(255))
    order: Mapped[str | None] = mapped_column(String(64), index=True)
    equipment: Mapped[str | None] = mapped_column(String(64), index=True)
    equipment_desc: Mapped[str | None] = mapped_column(String(500))
    functional_location: Mapped[str | None] = mapped_column(String(64), index=True)
    funcloc_desc: Mapped[str | None] = mapped_column(String(500))
    breakdown_duration: Mapped[float | None] = mapped_column(Numeric(10, 2))
    malfunction_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    malfunction_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reported_by: Mapped[str | None] = mapped_column(String(64))
    planner_group: Mapped[str | None] = mapped_column(String(32), index=True)
    main_work_center: Mapped[str | None] = mapped_column(String(32))
    maint_plant: Mapped[str | None] = mapped_column(String(32), index=True)
    priority: Mapped[str | None] = mapped_column(String(32))
    breakdown: Mapped[str | None] = mapped_column(String(8))
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_job.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WorkOrder(Base):
    __tablename__ = "work_order"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, server_default=func.gen_random_uuid(), unique=True, index=True
    )
    order: Mapped[str] = mapped_column(String(64), unique=True)
    notification: Mapped[str | None] = mapped_column(String(64), index=True)
    order_type: Mapped[str | None] = mapped_column(String(32), index=True)
    system_status: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000))
    user_status: Mapped[str | None] = mapped_column(String(255))
    maint_plant: Mapped[str | None] = mapped_column(String(32), index=True)
    equipment: Mapped[str | None] = mapped_column(String(64), index=True)
    equipment_desc: Mapped[str | None] = mapped_column(String(500))
    functional_location: Mapped[str | None] = mapped_column(String(64), index=True)
    funcloc_desc: Mapped[str | None] = mapped_column(String(500))
    bas_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bas_finish_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_finish: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_release: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planner_group: Mapped[str | None] = mapped_column(String(32), index=True)
    main_work_center: Mapped[str | None] = mapped_column(String(32))
    cost_center: Mapped[str | None] = mapped_column(String(64))
    total_act_costs: Mapped[float | None] = mapped_column(Numeric(18, 2))
    total_planned_costs: Mapped[float | None] = mapped_column(Numeric(18, 2))
    priority: Mapped[str | None] = mapped_column(String(32))
    work_center: Mapped[str | None] = mapped_column(String(32))
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_by: Mapped[str | None] = mapped_column(String(64))
    changed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_job.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
