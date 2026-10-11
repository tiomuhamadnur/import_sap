from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Equipment,
    FunctionalLocation,
    MeasuringDocument,
    MeasuringPoint,
    Notification,
    WorkOrder,
)


@dataclass(frozen=True)
class Column:
    field: str
    label: str
    kind: str = "text"  # 'text' | 'num' | 'date'
    filterable: bool = True
    searchable: bool = False


@dataclass(frozen=True)
class Relation:
    field: str
    target: type
    target_field: str
    slug: str
    label: str


@dataclass(frozen=True)
class EntityView:
    slug: str
    data_type: str
    title: str
    model: type
    key_fields: tuple[str, ...]
    columns: tuple[Column, ...]
    editable: tuple[str, ...]
    relations: tuple[Relation, ...] = field(default_factory=tuple)

    @property
    def key_field(self) -> str:
        return self.key_fields[0]

    @property
    def search_columns(self) -> list[str]:
        return [c.field for c in self.columns if c.searchable]

    @property
    def filter_columns(self) -> list[Column]:
        return [c for c in self.columns if c.filterable]


def _c(field_name, label, kind="text", **kw) -> Column:
    return Column(field_name, label, kind, **kw)


EQUIPMENT_VIEW = EntityView(
    slug="equipment",
    data_type="equipment",
    title="Equipment",
    model=Equipment,
    key_fields=("equipment_number",),
    columns=(
        _c("equipment_number", "Equipment", searchable=True),
        _c("description", "Description", searchable=True),
        _c("equipment_category", "Category"),
        _c("functional_location", "Functional Loc.", searchable=True),
        _c("maint_plant", "Maint. Plant"),
        _c("planner_group", "Planner Group"),
        _c("main_work_center", "Work Center"),
        _c("system_status", "System Status"),
        _c("manufacturer", "Manufacturer"),
        _c("serial_number", "Serial Number", searchable=True),
        _c("location", "Location", searchable=True),
        _c("acquisition_date", "Acquisition Date", kind="date"),
        _c("valid_from", "Valid From", kind="date"),
        _c("valid_to", "Valid To", kind="date"),
    ),
    editable=(
        "description",
        "equipment_category",
        "maint_plant",
        "planner_group",
        "main_work_center",
        "manufacturer",
        "serial_number",
        "location",
    ),
    relations=(
        Relation("functional_location", FunctionalLocation, "functional_location", "functional-location", "Functional Location"),
    ),
)

FUNCTIONAL_LOCATION_VIEW = EntityView(
    slug="functional-location",
    data_type="functional_location",
    title="Functional Location",
    model=FunctionalLocation,
    key_fields=("functional_location",),
    columns=(
        _c("functional_location", "Functional Loc.", searchable=True),
        _c("description", "Description", searchable=True),
        _c("funcloc_category", "Category"),
        _c("sup_funcloc", "Superior FunctLoc", searchable=True),
        _c("maint_plant", "Maint. Plant"),
        _c("planner_group", "Planner Group"),
        _c("main_work_center", "Work Center"),
        _c("cost_center", "Cost Center"),
        _c("str_indicator", "Structure Indicator"),
        _c("equip_installed", "Equip. Installed", searchable=True),
    ),
    editable=(
        "description",
        "funcloc_category",
        "maint_plant",
        "planner_group",
        "main_work_center",
        "cost_center",
    ),
    relations=(
        Relation("sup_funcloc", FunctionalLocation, "functional_location", "functional-location", "Superior Functional Location"),
    ),
)

MEASURING_DOCUMENT_VIEW = EntityView(
    slug="measuring-document",
    data_type="measuring_document",
    title="Measuring Document",
    model=MeasuringDocument,
    key_fields=("meas_document",),
    columns=(
        _c("meas_document", "MeasDocument", searchable=True),
        _c("measuring_point", "Measuring Point", searchable=True),
        _c("description", "Description", searchable=True),
        _c("measurement_date", "Date", kind="date"),
        _c("measurement_value", "Measurement", kind="num"),
        _c("difference", "Difference", kind="num"),
        _c("charact_unit", "Unit"),
        _c("measured_position", "Position"),
        _c("equipment", "Equipment", searchable=True),
        _c("functional_location", "Functional Loc.", searchable=True),
        _c("notification", "Notification", searchable=True),
        _c("order", "Order", searchable=True),
        _c("counter_reading", "Counter Reading", kind="num"),
        _c("created_on", "Created On", kind="date"),
    ),
    editable=("description", "charact_unit", "measured_position"),
    relations=(
        Relation("equipment", Equipment, "equipment_number", "equipment", "Equipment"),
        Relation("functional_location", FunctionalLocation, "functional_location", "functional-location", "Functional Location"),
        Relation("notification", Notification, "notification", "notification", "Notification"),
        Relation("order", WorkOrder, "order", "work-order", "Work Order"),
    ),
)

MEASURING_POINT_VIEW = EntityView(
    slug="measuring-point",
    data_type="measuring_point",
    title="Measuring Point",
    model=MeasuringPoint,
    key_fields=("measuring_point",),
    columns=(
        _c("measuring_point", "Measuring Point", searchable=True),
        _c("description", "Description", searchable=True),
        _c("equipment", "Equipment", searchable=True),
        _c("functional_location", "Functional Loc.", searchable=True),
        _c("measured_position", "Position", searchable=True),
        _c("characteristic", "Characteristic", searchable=True),
        _c("charact_unit", "Unit"),
        _c("reading_transfer", "Reading Transfer"),
        _c("annual_estimate", "Annual Estimate", kind="num"),
        _c("upper_mr_limit", "Upper MR Limit", kind="num"),
        _c("lower_mr_limit", "Lower MR Limit", kind="num"),
        _c("counter", "Counter"),
        _c("meas_point_category", "Category"),
        _c("meas_range_unit", "Range Unit"),
        _c("created_on", "Created On", kind="date"),
        _c("changed_on", "Changed On", kind="date"),
    ),
    editable=(
        "description",
        "measured_position",
        "characteristic",
        "charact_unit",
        "reading_transfer",
        "meas_point_category",
    ),
    relations=(
        Relation("equipment", Equipment, "equipment_number", "equipment", "Equipment"),
        Relation(
            "functional_location",
            FunctionalLocation,
            "functional_location",
            "functional-location",
            "Functional Location",
        ),
    ),
)

NOTIFICATION_VIEW = EntityView(
    slug="notification",
    data_type="notification",
    title="Notification",
    model=Notification,
    key_fields=("notification",),
    columns=(
        _c("notification", "Notification", searchable=True),
        _c("notif_type", "Type"),
        _c("notif_date", "Notif. Date", kind="date"),
        _c("description", "Description", searchable=True),
        _c("system_status", "System Status"),
        _c("order", "Order", searchable=True),
        _c("equipment", "Equipment", searchable=True),
        _c("functional_location", "Functional Loc.", searchable=True),
        _c("priority", "Priority"),
        _c("reported_by", "Reported By", searchable=True),
        _c("breakdown", "Breakdown"),
        _c("breakdown_duration", "Breakdown Dur.", kind="num"),
        _c("malfunction_start", "Malfunct. Start", kind="date"),
        _c("completion_date", "Completion Date", kind="date"),
    ),
    editable=(
        "description",
        "notif_type",
        "planner_group",
        "main_work_center",
        "maint_plant",
        "priority",
        "reported_by",
    ),
    relations=(
        Relation("order", WorkOrder, "order", "work-order", "Work Order"),
        Relation("equipment", Equipment, "equipment_number", "equipment", "Equipment"),
        Relation("functional_location", FunctionalLocation, "functional_location", "functional-location", "Functional Location"),
    ),
)

WORK_ORDER_VIEW = EntityView(
    slug="work-order",
    data_type="work_order",
    title="Work Order",
    model=WorkOrder,
    key_fields=("order",),
    columns=(
        _c("order", "Order", searchable=True),
        _c("order_type", "Order Type"),
        _c("system_status", "System Status"),
        _c("description", "Description", searchable=True),
        _c("notification", "Notification", searchable=True),
        _c("equipment", "Equipment", searchable=True),
        _c("functional_location", "Functional Loc.", searchable=True),
        _c("priority", "Priority"),
        _c("planner_group", "Planner Group"),
        _c("maint_plant", "Maint. Plant"),
        _c("total_act_costs", "Actual Costs", kind="num"),
        _c("total_planned_costs", "Planned Costs", kind="num"),
        _c("bas_start_date", "Basic Start", kind="date"),
        _c("actual_finish", "Actual Finish", kind="date"),
        _c("completion_date", "Completion Date", kind="date"),
    ),
    editable=(
        "description",
        "order_type",
        "planner_group",
        "main_work_center",
        "maint_plant",
        "priority",
        "cost_center",
    ),
    relations=(
        Relation("notification", Notification, "notification", "notification", "Notification"),
        Relation("equipment", Equipment, "equipment_number", "equipment", "Equipment"),
        Relation("functional_location", FunctionalLocation, "functional_location", "functional-location", "Functional Location"),
    ),
)


VIEWS: dict[str, EntityView] = {
    v.slug: v
    for v in (
        NOTIFICATION_VIEW,
        WORK_ORDER_VIEW,
        MEASURING_DOCUMENT_VIEW,
        MEASURING_POINT_VIEW,
        EQUIPMENT_VIEW,
        FUNCTIONAL_LOCATION_VIEW,
    )
}

SIDEBAR_ORDER = (
    "notification",
    "work-order",
    "measuring-document",
    "measuring-point",
    "equipment",
    "functional-location",
)


def get_view(slug: str) -> EntityView | None:
    return VIEWS.get(slug)


def column(view: EntityView, field_name: str) -> Column | None:
    for col in view.columns:
        if col.field == field_name:
            return col
    return None


def editable_columns(view: EntityView) -> list[Column]:
    by_field = {c.field: c for c in view.columns}
    out: list[Column] = []
    for field_name in view.editable:
        out.append(by_field.get(field_name) or Column(field_name, field_name.replace("_", " ").title()))
    return out


def build_query(
    view: EntityView,
    filters: dict[str, str] | None = None,
    q: str | None = None,
    sort: str | None = None,
    direction: str = "asc",
) -> Select:
    stmt = select(view.model)
    model = view.model
    known = {c.field for c in view.columns}

    for field_name, value in (filters or {}).items():
        value = (value or "").strip()
        if not value or field_name not in known:
            continue
        stmt = stmt.where(cast(getattr(model, field_name), String).ilike(f"%{value}%"))

    if q:
        q = q.strip()
        search_fields = view.search_columns
        if q and search_fields:
            stmt = stmt.where(
                or_(*[cast(getattr(model, f), String).ilike(f"%{q}%") for f in search_fields])
            )

    sort_field = sort if sort in known else view.key_field
    order_col = getattr(model, sort_field)
    stmt = stmt.order_by(order_col.desc() if direction == "desc" else order_col.asc())
    return stmt


def count_query(db: Session, stmt: Select) -> int:
    return db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0


def existing_values(
    db: Session, relation: Relation, values: set[str]
) -> set[str]:
    values = {v for v in values if v}
    if not values:
        return set()
    col = getattr(relation.target, relation.target_field)
    rows = db.execute(select(col).where(col.in_(values))).scalars().all()
    return {str(v) for v in rows}


def row_values(instance, view: EntityView) -> dict:
    return {c.field: getattr(instance, c.field) for c in view.columns}
