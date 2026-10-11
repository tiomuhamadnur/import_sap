from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from typing import Any

from app.importing.specs import DataTypeSpec, convert


@dataclass
class PreviewResult:
    rows_read: int = 0
    valid: int = 0
    invalid: int = 0
    new: int = 0
    update: int = 0
    extra_columns: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PreviewResult:
        if not data:
            return cls()
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def extra_columns(spec: DataTypeSpec, headers: Iterable[str]) -> list[str]:
    known = {k.source for k in spec.keys} | {f.source for f in spec.fields}
    seen: set[str] = set()
    out: list[str] = []
    for h in headers:
        name = "" if h is None else str(h)
        if name and name not in known and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def validate_row(spec: DataTypeSpec, values: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in spec.keys:
        if values.get(key.field) in (None, ""):
            errors.append(f'Missing key value for column "{key.source}".')
    return errors


def row_key(spec: DataTypeSpec, values: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(values.get(k.field, "")) for k in spec.keys)


def key_dict(spec: DataTypeSpec, values: dict[str, Any]) -> dict[str, Any]:
    return {k.field: values.get(k.field) for k in spec.keys}


def iter_records(
    spec: DataTypeSpec, rows: Iterable[dict[tuple[str, int], Any]]
) -> Iterator[tuple[int, dict[str, Any], list[str]]]:
    """Yield (row_number, converted_values, errors) for each file row."""
    for number, row in enumerate(rows, start=1):
        try:
            values = convert(spec, row)
        except Exception as exc:  # pragma: no cover - defensive
            yield number, {}, [f"Could not parse row: {exc}"]
            continue
        yield number, values, validate_row(spec, values)


def preview(
    spec: DataTypeSpec,
    rows: Iterable[dict[tuple[str, int], Any]],
    existing_keys: set[tuple[str, ...]],
    error_limit: int = 200,
) -> PreviewResult:
    result = PreviewResult()
    for number, values, errors in iter_records(spec, rows):
        result.rows_read += 1
        if errors:
            result.invalid += 1
            if len(result.errors) < error_limit:
                result.errors.append({"row": number, "messages": errors})
            continue
        result.valid += 1
        if row_key(spec, values) in existing_keys:
            result.update += 1
        else:
            result.new += 1
    return result
