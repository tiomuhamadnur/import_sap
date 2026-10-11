from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from app.db import engine

router = APIRouter(tags=["system"])


@router.get("/health", response_class=JSONResponse)
def health():
    db_ok = True
    try:
        with engine.connect():
            pass
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "error"}


@router.get("/healthz")
def healthz():
    return HTMLResponse("ok")
