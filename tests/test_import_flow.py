from openpyxl import Workbook
from sqlalchemy import delete, select

from app.models import Equipment, ImportJob, ImportRecordResult
from app.services.importer import process_import
from app.services.rollback import rollback_job

HEADERS = ["Equipment", "Description", "MaintPlant"]


def _write_xlsx(path, rows) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)
    wb.save(path)


def _make_job(db, user_id, path, status="queued") -> int:
    job = ImportJob(
        user_id=user_id,
        data_type="equipment",
        status=status,
        filename=path.name,
        storage_path=str(path),
        options={"on_invalid": "valid_only"},
    )
    db.add(job)
    db.commit()
    return job.id


def _purge(db, job_ids, keys) -> None:
    db.execute(delete(ImportRecordResult).where(ImportRecordResult.job_id.in_(job_ids)))
    db.execute(delete(ImportJob).where(ImportJob.id.in_(job_ids)))
    db.execute(delete(Equipment).where(Equipment.equipment_number.in_(keys)))
    db.commit()


def _get_equipment(db, key):
    return db.scalar(select(Equipment).where(Equipment.equipment_number == key))


def test_partial_import_skips_invalid_and_rollback_conflict(db, accounts, tmp_path):
    existing_key = "ZZ-IMP-EQ1"
    new_key = "ZZ-IMP-EQ2"
    other_job_id = None
    job_id = None
    db.add(Equipment(equipment_number=existing_key, description="Old", raw_data={}))
    db.commit()
    try:
        path = tmp_path / "eq.xlsx"
        _write_xlsx(
            path,
            [[existing_key, "New value", "MRTJ"], [new_key, "Fresh", "MRTJ"], [None, "bad", "MRTJ"]],
        )
        job_id = _make_job(db, accounts["admin"].id, path)

        process_import(job_id)
        db.expire_all()
        job = db.get(ImportJob, job_id)
        assert job.status == "partial"
        assert (job.updated, job.inserted, job.skipped) == (1, 1, 1)

        other = ImportJob(
            user_id=accounts["admin"].id, data_type="equipment", status="completed"
        )
        db.add(other)
        db.commit()
        other_job_id = other.id
        record = _get_equipment(db, existing_key)
        record.import_job_id = other_job_id
        db.commit()

        outcome = rollback_job(job_id, actor_id=accounts["admin"].id)
        assert outcome == {"undone": 1, "conflicts": 1, "missing": 0}

        db.expire_all()
        kept = _get_equipment(db, existing_key)
        assert kept is not None and kept.description == "New value"
        assert _get_equipment(db, new_key) is None
    finally:
        _purge(db, [jid for jid in (job_id, other_job_id) if jid], [existing_key, new_key])


def test_update_rollback_restores_before_data(db, accounts, tmp_path):
    key = "ZZ-IMP-EQ3"
    job_id = None
    db.add(Equipment(equipment_number=key, description="Original", raw_data={}))
    db.commit()
    try:
        path = tmp_path / "eq3.xlsx"
        _write_xlsx(path, [[key, "Changed", "MRTJ"]])
        job_id = _make_job(db, accounts["admin"].id, path)

        process_import(job_id)
        db.expire_all()
        assert _get_equipment(db, key).description == "Changed"

        outcome = rollback_job(job_id, actor_id=accounts["admin"].id)
        assert outcome["undone"] == 1 and outcome["conflicts"] == 0

        db.expire_all()
        assert _get_equipment(db, key).description == "Original"
        rolled = db.get(ImportJob, job_id)
        assert rolled.status == "rolled_back"
    finally:
        _purge(db, [job_id] if job_id else [], [key])
