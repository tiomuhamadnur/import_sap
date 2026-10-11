from datetime import date, datetime
from decimal import Decimal

import pytest

from app.routers.data import _cell
from app.services.dataviews import SIDEBAR_ORDER, VIEWS, editable_columns, get_view


def test_views_cover_sidebar_order():
    assert tuple(VIEWS.keys()) == SIDEBAR_ORDER


def test_get_view():
    assert get_view("equipment").title == "Equipment"
    assert get_view("does-not-exist") is None


@pytest.mark.parametrize("slug", list(VIEWS))
def test_view_config_is_consistent(slug):
    view = VIEWS[slug]
    fields = {c.field for c in view.columns}
    model_columns = {c.name for c in view.model.__table__.columns}

    for key in view.key_fields:
        assert key in model_columns, f"{slug}: key field {key} not a column"
    for field_name in view.editable:
        assert field_name in model_columns, f"{slug}: editable {field_name} not a column"
    assert view.key_field in fields

    editable = {c.field for c in editable_columns(view)}
    assert editable == set(view.editable)

    for relation in view.relations:
        assert relation.field in fields, f"{slug}: relation {relation.field} not displayed"
        assert relation.slug in VIEWS, f"{slug}: relation target slug {relation.slug} unknown"
        target_columns = {c.name for c in relation.target.__table__.columns}
        assert relation.target_field in target_columns


def test_cell_formats_values():
    assert _cell(None) == ""
    assert _cell(datetime(2026, 1, 19, 3, 30, 0)) == "2026-01-19 03:30:00"
    assert _cell(date(2026, 1, 19)) == "2026-01-19"
    assert _cell(Decimal("12.50")) == "12.50"
    assert _cell("text") == "text"
