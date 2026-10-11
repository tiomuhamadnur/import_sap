from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


def _columns_for(model: type, rows: list[dict[str, Any]]) -> list[str]:
    table = model.__table__
    columns = set(table.columns.keys())
    return [c for c in rows[0].keys() if c in columns]


def upsert_batch(
    db: Session,
    model: type,
    key_fields: list[str],
    rows: list[dict[str, Any]],
) -> None:
    """Upsert rows keyed by natural key columns (idempotent re-import)."""
    if not rows:
        return
    cols = _columns_for(model, rows)
    update_cols = [c for c in cols if c not in ("id", "created_at")]

    stmt = insert(model).values(rows)
    set_ = {c: stmt.excluded[c] for c in update_cols}
    set_["updated_at"] = func.now()
    stmt = stmt.on_conflict_do_update(index_elements=key_fields, set_=set_)
    db.execute(stmt)


def upsert_batch_returning(
    db: Session,
    model: type,
    key_fields: list[str],
    rows: list[dict[str, Any]],
) -> list[Any]:
    """Upsert and return (id, *key_fields) for each processed row."""
    if not rows:
        return []
    cols = _columns_for(model, rows)
    update_cols = [c for c in cols if c not in ("id", "created_at")]

    stmt = insert(model).values(rows)
    set_ = {c: stmt.excluded[c] for c in update_cols}
    set_["updated_at"] = func.now()
    stmt = stmt.on_conflict_do_update(index_elements=key_fields, set_=set_)
    returning = [model.id, *[getattr(model, kf) for kf in key_fields]]
    return list(db.execute(stmt.returning(*returning)).fetchall())
