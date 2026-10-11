import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.logging import configure_logging
from app.routers.auth import router as auth_router
from app.routers.data import router as data_router
from app.routers.imports import router as imports_router
from app.routers.profile import router as profile_router
from app.routers.system import router as system_router
from app.routers.users import router as users_router
from app.seed import bootstrap_admin

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    try:
        bootstrap_admin()
    except Exception:  # pragma: no cover - startup resilience
        logger.exception("bootstrap admin failed")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age,
    same_site="lax",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(users_router)
app.include_router(imports_router)
app.include_router(data_router)
