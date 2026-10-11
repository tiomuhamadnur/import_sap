import re
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import AuditLog, Equipment


def _csrf(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _first_equipment(db):
    row = db.query(Equipment).first()
    if row is None:
        pytest.skip("no equipment rows to test against")
    return row


def test_security_headers_present():
    resp = TestClient(app).get("/login")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"


def test_viewer_can_read_list(viewer_client):
    assert viewer_client.get("/equipment").status_code == 200
    assert viewer_client.get("/notification").status_code == 200


def test_viewer_cannot_access_admin_pages(viewer_client):
    assert viewer_client.get("/users").status_code == 403
    resp = viewer_client.get("/")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/notification"


def test_viewer_cannot_edit_or_delete(viewer_client, db):
    record = _first_equipment(db)
    assert viewer_client.get(f"/equipment/{record.public_id}/edit").status_code == 403

    token = _csrf(viewer_client.get("/equipment").text)
    resp = viewer_client.post(
        f"/equipment/{record.public_id}/delete", data={"csrf_token": token}
    )
    assert resp.status_code == 403

    resp = viewer_client.post(
        "/equipment/bulk-delete", data={"csrf_token": token, "ids": [record.id]}
    )
    assert resp.status_code == 403


def test_viewer_cannot_upload(viewer_client):
    token = _csrf(viewer_client.get("/equipment").text)
    resp = viewer_client.post(
        "/import/upload",
        data={"csrf_token": token, "data_type": "notification"},
        files={"file": ("n.csv", b"Notification\n1\n", "text/csv")},
    )
    assert resp.status_code == 403


def test_upload_rejects_unsupported_extension(admin_client):
    token = _csrf(admin_client.get("/").text)
    resp = admin_client.post(
        "/import/upload",
        data={"csrf_token": token, "data_type": "notification"},
        files={"file": ("payload.exe", b"PK\x03\x04fake", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.text


def test_upload_rejects_fake_xlsx(admin_client):
    token = _csrf(admin_client.get("/").text)
    resp = admin_client.post(
        "/import/upload",
        data={"csrf_token": token, "data_type": "notification"},
        files={"file": ("fake.xlsx", b"this is not a zip", "application/vnd.ms-excel")},
    )
    assert resp.status_code == 400
    assert "not a valid Excel" in resp.text


def test_upload_rejects_binary_csv(admin_client):
    token = _csrf(admin_client.get("/").text)
    resp = admin_client.post(
        "/import/upload",
        data={"csrf_token": token, "data_type": "notification"},
        files={"file": ("binary.csv", b"Notification\x00\x01\x02", "text/csv")},
    )
    assert resp.status_code == 400
    assert "binary data" in resp.text


def test_delete_writes_audit_log(admin_client, db):
    key = f"ZZ-AUDIT-{uuid.uuid4().hex[:8]}"
    record = Equipment(equipment_number=key, description="audit", raw_data={})
    db.add(record)
    db.commit()
    record_id = record.id
    public_id = record.public_id

    before = db.query(AuditLog).count()
    token = _csrf(admin_client.get("/equipment").text)
    resp = admin_client.post(
        f"/equipment/{public_id}/delete", data={"csrf_token": token}
    )
    assert resp.status_code == 303
    db.expire_all()
    assert db.get(Equipment, record_id) is None
    assert db.query(AuditLog).count() == before + 1

    entry = (
        db.query(AuditLog)
        .filter(AuditLog.action == "equipment.delete")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert entry is not None and entry.object_id == str(public_id)

