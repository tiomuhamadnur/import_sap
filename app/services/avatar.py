from __future__ import annotations

import base64
import binascii
import io
import re

from PIL import Image, ImageOps

# Accepted upload limit before compression.
MAX_SOURCE_BYTES = 1024 * 1024  # 1 MB
# Target size for the stored avatar (data URI payload).
MAX_OUTPUT_BYTES = 200 * 1024  # 200 KB
MAX_DIMENSION = 320
_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF"}

_DATA_URI_RE = re.compile(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.*)$", re.DOTALL)


def make_avatar_data_uri(raw: bytes) -> str:
    """Validate, downscale and compress an uploaded image into a data URI string.

    Raises ValueError with a user-facing message when the image cannot be used.
    """
    if not raw:
        raise ValueError("The uploaded file is empty.")
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Image is larger than 1 MB.")

    try:
        with Image.open(io.BytesIO(raw)) as source:
            source.load()
            image_format = source.format
            if image_format not in _ALLOWED_FORMATS:
                raise ValueError("Unsupported image format.")
            image = ImageOps.exif_transpose(source).convert("RGB")
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001 - PIL raises many error types
        raise ValueError("The file is not a valid image.") from exc

    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    buffer = io.BytesIO()
    for quality in (85, 75, 65, 55, 45, 35, 25, 15):
        buffer.seek(0)
        buffer.truncate()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        if buffer.tell() <= MAX_OUTPUT_BYTES:
            break

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def decode_avatar(data_uri: str | None) -> tuple[str, bytes] | None:
    """Return (mime_type, raw_bytes) for a stored data URI, else None."""
    if not data_uri:
        return None
    match = _DATA_URI_RE.match(data_uri.strip())
    if not match:
        return None
    mime, payload = match.group(1), match.group(2)
    try:
        return mime, base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return None
