from pathlib import Path

from sqlalchemy import text

from app.db import SessionLocal
from app.importing import DATASETS, convert, rows_iterator
from app.services.upsert import upsert_batch

BATCH = 1000

FILES = {
    "functional_location": Path("samples/functional_location/functional_location.xlsx"),
    "equipment": Path("samples/equipment/equipment.xlsx"),
    "measuring_document": Path("samples/measuring_document/measuring_document.xlsx"),
    "measuring_point": Path("samples/measuring_point/measuring_point.xlsx"),
    "notification": Path("samples/notification/notification.xlsx"),
    "work_order": Path("samples/work_order/work_order.xlsx"),
}


def main():
    db = SessionLocal()
    try:
        for data_type, path in FILES.items():
            spec = DATASETS[data_type]
            key_fields = [k.field for k in spec.keys]
            batch: list[dict] = []
            n = 0
            for row in rows_iterator(path):
                values = convert(spec, row)
                batch.append(values)
                if len(batch) >= BATCH:
                    upsert_batch(db, spec.model, key_fields, batch)
                    db.commit()
                    batch = []
                n += 1
            upsert_batch(db, spec.model, key_fields, batch)
            db.commit()
            table = spec.model.__tablename__
            total = db.scalar(text(f"SELECT count(*) FROM {table}"))
            print(f"[ok] {data_type}: processed={n} stored={total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
