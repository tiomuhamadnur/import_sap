from datetime import datetime

from openpyxl import Workbook

from app.importing.reader import parse_date, parse_number, read_file, sanitize
from app.importing.specs import (
    DATASETS,
    NOTIFICATION,
    convert,
    validate_structure,
)


def test_parse_number_german_format():
    assert parse_number("269.819,00") == 269819.0
    assert parse_number("1,00") == 1.0
    assert parse_number("0,00") == 0.0
    assert parse_number("0,000") == 0.0
    assert parse_number("249.750") == 249750.0
    assert parse_number("12") == 12.0
    assert parse_number("") is None
    assert parse_number(None) is None


def test_parse_date_formats():
    assert parse_date("19/01/2026") == datetime(2026, 1, 19)
    assert parse_date("2026-01-19") == datetime(2026, 1, 19)
    assert parse_date("00:00:00") is None
    assert parse_date("") is None
    assert parse_date(None) is None


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8-sig")


def test_read_csv_with_duplicate_headers(tmp_path):
    p = tmp_path / "dup.csv"
    p.write_bytes(
        _csv_bytes("Notification;Description;Description;Value\n" "1001;Main;Secondary;3,5\n")
    )
    src = read_file(p)
    assert src.headers == ["Notification", "Description", "Description", "Value"]
    row = src.rows[0]
    assert row[("Notification", 0)] == "1001"
    assert row[("Description", 0)] == "Main"
    assert row[("Description", 1)] == "Secondary"
    assert row[("Value", 0)] == "3,5"


def test_notification_spec_conversion(tmp_path):
    p = tmp_path / "notif.csv"
    p.write_text(
        "Notifictn Type;Notif.Date;Notification;Description;Order;Equipment;Description;"
        "Functional Loc.;Description;Breakdown dur.;Priority\n"
        "SC;19/01/2026;50000000;Desc Main;50000000;20000508;Eq Desc;MRTJ-X;FL Desc;1,00;G0\n"
    )
    src = read_file(p)
    spec = NOTIFICATION
    assert validate_structure(spec, src.headers) == []
    values = convert(spec, src.rows[0])
    assert values["notification"] == "50000000"
    assert values["notif_date"] == datetime(2026, 1, 19)
    assert values["description"] == "Desc Main"
    assert values["equipment_desc"] == "Eq Desc"
    assert values["funcloc_desc"] == "FL Desc"
    assert values["breakdown_duration"] == 1.0
    assert values["priority"] == "G0"
    assert values["raw_data"]["Description (1)"] == "Desc Main"
    assert values["raw_data"]["Description (2)"] == "Eq Desc"
    assert values["raw_data"]["Description (3)"] == "FL Desc"


def test_validate_structure_missing_required():
    spec = NOTIFICATION
    missing = validate_structure(spec, ["Notifictn Type", "Description"])
    assert missing == ["Notification"]


def test_read_xlsx_with_duplicate_headers(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Equipment", "Description", "Description", "Valid From"])
    ws.append(["10000000", "Main", "Sub", "19/01/2026"])
    path = tmp_path / "eq.xlsx"
    wb.save(path)
    src = read_file(path)
    assert src.format == "xlsx"
    row = src.rows[0]
    assert row[("Description", 0)] == "Main"
    assert row[("Description", 1)] == "Sub"
    assert src.raw_mapping(1) == "Description"
    assert src.raw_mapping(2) == "Description (2)"


def test_datasets_registered():
    assert set(DATASETS) == {
        "notification",
        "work_order",
        "measuring_document",
        "measuring_point",
        "equipment",
        "functional_location",
    }


def test_every_dataset_requires_its_key_header():
    for data_type, spec in DATASETS.items():
        key_headers = {k.source for k in spec.keys}
        assert key_headers.issubset(set(spec.required_headers)), data_type
        # A file lacking the key header must be rejected as structurally invalid.
        headers_without_key = [h for h in spec.required_headers if h not in key_headers]
        missing = validate_structure(spec, headers_without_key)
        assert key_headers.issubset(set(missing)), data_type


def test_key_conversion_returns_none_when_key_absent():
    spec = NOTIFICATION
    values = convert(spec, {("Notifictn Type", 0): "SC"})
    assert values["notification"] is None


def test_sanitize_datetime():
    assert sanitize(datetime(2026, 1, 19, 10, 30, 0)) == "2026-01-19 10:30:00"
