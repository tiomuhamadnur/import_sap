import uuid

import pytest

import app.queue as app_queue
from app.models import DATA_TYPES
from app.queue import all_queue_names, get_redis, queue_name


def test_queue_names_are_per_datatype():
    names = [queue_name(dt) for dt in DATA_TYPES]
    assert len(set(names)) == len(DATA_TYPES)
    assert all(name.startswith("import:") for name in names)
    assert queue_name("equipment") == "import:equipment"
    assert all_queue_names() == names


def test_same_datatype_shares_a_queue():
    assert queue_name("work_order") == queue_name("work_order")
    assert queue_name("work_order") != queue_name("notification")


def _redis_or_skip():
    redis = get_redis()
    try:
        redis.ping()
    except Exception:  # pragma: no cover - depends on local Redis
        pytest.skip("Redis not available")
    return redis


def test_enqueue_import_targets_datatype_queue(monkeypatch):
    redis = _redis_or_skip()
    from rq import Queue

    isolate = f"import_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(app_queue, "queue_name", lambda _dt: isolate)

    job = app_queue.enqueue_import(999_999, "equipment")
    assert job.origin == isolate
    assert len(Queue(isolate, connection=redis)) >= 1

    Queue(isolate, connection=redis).empty()
    monkeypatch.undo()
