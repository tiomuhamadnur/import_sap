from __future__ import annotations

from redis import Redis
from rq import Queue

from app.config import settings
from app.models import DATA_TYPES

QUEUE_PREFIX = "import"
JOB_TIMEOUT = 3600


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url)


def queue_name(data_type: str) -> str:
    return f"{QUEUE_PREFIX}:{data_type}"


def all_queue_names() -> list[str]:
    return [queue_name(data_type) for data_type in DATA_TYPES]


def enqueue_import(job_id: int, data_type: str):
    from app.tasks import process_import

    queue = Queue(queue_name(data_type), connection=get_redis())
    return queue.enqueue(process_import, job_id, job_timeout=JOB_TIMEOUT)
