"""RQ jobs for import processing.

The worker is started with all per-datatype queues:
    rq worker --url <redis url> import:notification import:work_order \
        import:measuring_document import:measuring_point import:equipment \
        import:functional_location

Per-datatype queues guarantee that imports of the same data type run one at a
time, while imports of different data types may run concurrently.
"""

from app.services.importer import process_import

__all__ = ["process_import"]
