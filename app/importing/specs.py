from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from app.importing.reader import is_empty, parse_date, parse_number, sanitize
from app.models import (
    Equipment,
    FunctionalLocation,
    MeasuringDocument,
    MeasuringPoint,
    Notification,
    WorkOrder,
)


@dataclass(frozen=True)
class FieldSpec:
    field: str
    source: str
    occurrence: int = 0
    kind: str = "str"  # 'str' | 'date' | 'num'


@dataclass(frozen=True)
class KeySpec:
    field: str
    source: str
    occurrence: int = 0
    kind: str = "str"


@dataclass(frozen=True)
class DataTypeSpec:
    data_type: str
    title: str
    model: type
    keys: tuple[KeySpec, ...]
    fields: tuple[FieldSpec, ...]
    required_headers: tuple[str, ...]

    def source_for(self, field: str) -> KeySpec | FieldSpec | None:
        for k in self.keys:
            if k.field == field:
                return k
        for f in self.fields:
            if f.field == field:
                return f
        return None


def _col(field: str, source: str, occurrence: int = 0, kind: str = "str") -> FieldSpec:
    return FieldSpec(field, source, occurrence, kind)


def _key(field: str, source: str, occurrence: int = 0) -> KeySpec:
    return KeySpec(field, source, occurrence)


EQUIPMENT = DataTypeSpec(
    data_type="equipment",
    title="Equipment",
    model=Equipment,
    keys=(_key("equipment_number", "Equipment"),),
    required_headers=("Equipment",),
    fields=(
        _col("equipment_category", "EquipCategory"),
        _col("tech_id_no", "TechIdentNo."),
        _col("description", "Description"),
        _col("functional_location", "Functional Loc."),
        _col("maint_plant", "MaintPlant"),
        _col("cost_center", "Cost Center"),
        _col("planning_plant", "Planning Plant"),
        _col("planner_group", "Planner Group"),
        _col("main_work_center", "Main WorkCtr"),
        _col("material", "Material"),
        _col("system_status", "System status"),
        _col("asset", "Asset"),
        _col("manufacturer", "Manufacturer"),
        _col("serial_number", "Serial Number"),
        _col("object_number", "Object number"),
        _col("location", "Location"),
        _col("acquisition_date", "Acquistion date", kind="date"),
        _col("created_by", "Created By"),
        _col("created_on", "Created On", kind="date"),
        _col("changed_by", "Changed By"),
        _col("changed_on", "Changed On", kind="date"),
        _col("valid_from", "Valid From", kind="date"),
        _col("valid_to", "Valid To", kind="date"),
    ),
)

FUNCTIONAL_LOCATION = DataTypeSpec(
    data_type="functional_location",
    title="Functional Location",
    model=FunctionalLocation,
    keys=(_key("functional_location", "Functional Loc."),),
    required_headers=("Functional Loc.",),
    fields=(
        _col("funcloc_category", "FunctLocCat."),
        _col("description", "Description"),
        _col("sup_funcloc", "SupFunctLoc."),
        _col("maint_plant", "MaintPlant"),
        _col("cost_center", "Cost Center"),
        _col("planner_group", "Planner Group"),
        _col("main_work_center", "Main WorkCtr"),
        _col("str_indicator", "StrIndicator"),
        _col("equip_installed", "EquipInstall."),
    ),
)

MEASURING_DOCUMENT = DataTypeSpec(
    data_type="measuring_document",
    title="Measuring Document",
    model=MeasuringDocument,
    keys=(_key("meas_document", "MeasDocument"),),
    required_headers=("MeasDocument",),
    fields=(
        _col("measuring_point", "Measuring point"),
        _col("description", "Description"),
        _col("measurement_date", "Date", kind="date"),
        _col("measurement_value", "Meas/TotCtrRdg", kind="num"),
        _col("difference", "Difference", kind="num"),
        _col("charact_unit", "CharactUnit"),
        _col("measured_position", "MeasPosition"),
        _col("equipment", "Equipment"),
        _col("functional_location", "Functional Loc."),
        _col("notification", "Notification"),
        _col("order", "Order"),
        _col("counter_reading", "Counter reading", kind="num"),
        _col("target_value", "Target value", kind="num"),
        _col("upper_mr_limit", "UpMRLimit", kind="num"),
        _col("lower_mr_limit", "LoMRLimit", kind="num"),
        _col("created_by", "Created by"),
        _col("created_on", "Created on", kind="date"),
    ),
)

MEASURING_POINT = DataTypeSpec(
    data_type="measuring_point",
    title="Measuring Point",
    model=MeasuringPoint,
    keys=(_key("measuring_point", "Measuring point"),),
    required_headers=("Measuring point",),
    fields=(
        _col("description", "Description"),
        _col("equipment", "Equipment"),
        _col("functional_location", "Functional Loc."),
        _col("measured_position", "MeasPosition"),
        _col("characteristic", "Characteristic"),
        _col("charact_unit", "CharactUnit"),
        _col("reading_transfer", "Readg trans.fr."),
        _col("annual_estimate", "AnnualEstimate", kind="num"),
        _col("upper_mr_limit", "UpMRLimit", kind="num"),
        _col("lower_mr_limit", "LoMRLimit", kind="num"),
        _col("counter", "Counter"),
        _col("decimal_places", "Decimal places"),
        _col("float_point_exp", "FloatPointExp."),
        _col("internal_meas_unit", "Int. meas. unit"),
        _col("internal_char", "Internal char."),
        _col("language", "Language"),
        _col("meas_point_category", "MeasPtCategory"),
        _col("meas_range_unit", "MeasRangeUnit"),
        _col("measurement_object_number", "OBjNo.MeasPObj."),
        _col("client", "Client"),
        _col("supported", "Supported"),
        _col("transfer_mode", "Transfer mode"),
        _col("created_by", "Created by"),
        _col("created_on", "Created on", kind="date"),
        _col("changed_by", "Changed by"),
        _col("changed_on", "Changed on", kind="date"),
    ),
)

NOTIFICATION = DataTypeSpec(
    data_type="notification",
    title="Notification",
    model=Notification,
    keys=(_key("notification", "Notification"),),
    required_headers=("Notification",),
    fields=(
        _col("notif_type", "Notifictn Type"),
        _col("notif_date", "Notif.Date", kind="date"),
        _col("description", "Description"),
        _col("system_status", "System status"),
        _col("order", "Order"),
        _col("equipment", "Equipment"),
        _col("equipment_desc", "Description", occurrence=1),
        _col("functional_location", "Functional Loc."),
        _col("funcloc_desc", "Description", occurrence=2),
        _col("breakdown_duration", "Breakdown dur.", kind="num"),
        _col("malfunction_start", "Malfunct. Start", kind="date"),
        _col("malfunction_end", "Malfunct. End", kind="date"),
        _col("reported_by", "Reported By"),
        _col("planner_group", "Planner Group"),
        _col("main_work_center", "Main WorkCtr"),
        _col("maint_plant", "MaintPlant"),
        _col("priority", "Priority"),
        _col("breakdown", "Breakdown"),
        _col("created_by", "Created By"),
        _col("created_on", "Created On", kind="date"),
        _col("completion_date", "Completn date", kind="date"),
    ),
)

WORK_ORDER = DataTypeSpec(
    data_type="work_order",
    title="Work Order",
    model=WorkOrder,
    keys=(_key("order", "Order"),),
    required_headers=("Order",),
    fields=(
        _col("notification", "Notification"),
        _col("order_type", "Order Type"),
        _col("system_status", "System status"),
        _col("description", "Description"),
        _col("user_status", "User status"),
        _col("maint_plant", "MaintPlant"),
        _col("equipment", "Equipment"),
        _col("equipment_desc", "Description", occurrence=1),
        _col("functional_location", "Functional Loc."),
        _col("funcloc_desc", "Description", occurrence=2),
        _col("bas_start_date", "Bas. start date", kind="date"),
        _col("bas_finish_date", "Basic fin. date", kind="date"),
        _col("actual_start", "Actual start", kind="date"),
        _col("actual_finish", "Actual Finish", kind="date"),
        _col("actual_release", "Actual release", kind="date"),
        _col("planner_group", "Planner Group"),
        _col("main_work_center", "Main WorkCtr"),
        _col("cost_center", "Cost Center"),
        _col("total_act_costs", "Total act.costs", kind="num"),
        _col("total_planned_costs", "TotalPlnndCosts", kind="num"),
        _col("priority", "Priority"),
        _col("work_center", "Work Center"),
        _col("created_by", "Entered By"),
        _col("created_on", "Created On", kind="date"),
        _col("changed_by", "Changed By"),
        _col("changed_on", "Changed On", kind="date"),
        _col("completion_date", "Compl. Date", kind="date"),
    ),
)


DATASETS: dict[str, DataTypeSpec] = {
    spec.data_type: spec
    for spec in (
        EQUIPMENT,
        FUNCTIONAL_LOCATION,
        MEASURING_DOCUMENT,
        MEASURING_POINT,
        NOTIFICATION,
        WORK_ORDER,
    )
}


def convert(spec: DataTypeSpec, row: dict[tuple[str, int], Any]) -> dict[str, Any]:
    """Convert a raw (header, occ)->value row into curated db-field values + raw_data."""
    raw: dict[str, str | None] = {}
    used = set()
    values: dict[str, Any] = {}

    for key, value in row.items():
        (name, occ) = key
        if any((f.source, f.occurrence) == key for f in (*spec.keys, *spec.fields)):
            used.add(key)
        raw[raw_key(name, occ, row, key)] = sanitize(value)

    def get(source, occurrence=0):
        return row.get((source, occurrence))

    for key_spec in spec.keys:
        val = get(key_spec.source, key_spec.occurrence)
        values[key_spec.field] = _convert_value(key_spec.kind, val)
    for f in spec.fields:
        val = get(f.source, f.occurrence)
        values[f.field] = _convert_value(f.kind, val)

    values["raw_data"] = raw
    return values


def raw_key(name: str, occ: int, row: dict[tuple[str, int], Any], key: tuple[str, int]) -> str:
    """Build a human-readable raw_data key, disambiguating duplicate headers."""
    same = 0
    for n, _o in row:
        if n == name:
            same += 1
    return name if same == 1 else f"{name} ({occ + 1})"


def _convert_value(kind: str, value: Any):
    if kind == "date":
        return parse_date(value)
    if kind == "num":
        return parse_number(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    s = str(value).strip()
    if is_empty(s):
        return None
    return s


def validate_structure(spec: DataTypeSpec, headers: list[str]) -> list[str]:
    """Return a list of missing required headers (empty = structurally valid)."""
    missing = []
    for req in spec.required_headers:
        if req not in headers:
            missing.append(req)
    return missing
