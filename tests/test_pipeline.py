from app.importing.pipeline import (
    PreviewResult,
    extra_columns,
    key_dict,
    preview,
    row_key,
    validate_row,
)
from app.importing.specs import EQUIPMENT, NOTIFICATION
from app.models import ImportJob


def _row(**pairs):
    return {(k, 0): v for k, v in pairs.items()}


def test_extra_columns_detects_unknown():
    headers = ["Equipment", "Description", "Foo", "Bar", "Foo"]
    assert extra_columns(EQUIPMENT, headers) == ["Foo", "Bar"]


def test_validate_row_missing_key():
    values = {"equipment_number": None}
    assert validate_row(EQUIPMENT, values) == ['Missing key value for column "Equipment".']
    assert validate_row(EQUIPMENT, {"equipment_number": ""}) != []
    assert validate_row(EQUIPMENT, {"equipment_number": "1001"}) == []


def test_row_key_and_key_dict():
    values = {"equipment_number": "1001", "description": "X"}
    assert row_key(EQUIPMENT, values) == ("1001",)
    assert key_dict(EQUIPMENT, values) == {"equipment_number": "1001"}


def test_preview_counts_new_update_and_invalid():
    rows = [
        _row(Equipment="1001", Description="A"),
        _row(Equipment="1002", Description="B"),
        _row(Description="missing key"),
    ]
    result = preview(EQUIPMENT, rows, existing_keys={("1002",)}, error_limit=10)
    assert result.rows_read == 3
    assert result.valid == 2
    assert result.invalid == 1
    assert result.new == 1
    assert result.update == 1
    assert result.errors[0]["row"] == 3


def test_preview_error_limit():
    rows = [_row(Description="bad") for _ in range(5)]
    result = preview(EQUIPMENT, rows, existing_keys=set(), error_limit=2)
    assert result.invalid == 5
    assert len(result.errors) == 2


def test_preview_result_roundtrip():
    result = PreviewResult(rows_read=1, valid=1, new=1, extra_columns=["X"])
    assert PreviewResult.from_dict(result.to_dict()) == result
    assert PreviewResult.from_dict(None) == PreviewResult()


def test_notification_key_is_notification():
    assert row_key(NOTIFICATION, {"notification": "50000000"}) == ("50000000",)


def test_preview_page_shows_update_count(admin_client, db, accounts):
    job = ImportJob(
        user_id=accounts["admin"].id,
        data_type="equipment",
        status="preview",
        filename="eq.xlsx",
        preview={
            "rows_read": 3,
            "valid": 3,
            "invalid": 0,
            "new": 2,
            "update": 1,
            "extra_columns": ["Foo", "Bar"],
            "errors": [],
        },
    )
    db.add(job)
    db.commit()
    try:
        resp = admin_client.get(f"/import/{job.id}/preview")
        assert resp.status_code == 200
        assert "built-in method" not in resp.text
        assert ">1<" in resp.text
        assert "2 unrecognized columns will be ignored" in resp.text
    finally:
        db.delete(job)
        db.commit()
