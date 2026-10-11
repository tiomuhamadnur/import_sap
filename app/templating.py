import secrets
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import TERMINAL_JOB_STATUSES

templates = Jinja2Templates(directory="app/templates")

CSRF_SESSION_KEY = "csrf_token"


def get_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


def to_wib(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d %H:%M:%S")


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return to_wib(value)
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def format_count(value: Any) -> str:
    """Group an integer with '.' as the thousands separator (e.g. 65212 -> 65.212)."""
    if value is None or value == "":
        return "0"
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value)


templates.env.filters["wib"] = to_wib
templates.env.filters["fmt"] = format_value
templates.env.filters["num"] = format_count
templates.env.globals["terminal_statuses"] = TERMINAL_JOB_STATUSES
templates.env.globals["max_upload_mb"] = settings.max_upload_size_mb


def render(
    request: Request,
    name: str,
    status_code: int = 200,
    **context: Any,
) -> HTMLResponse:
    context.setdefault("csrf_token", get_csrf_token(request))
    return templates.TemplateResponse(request, name, context, status_code=status_code)
