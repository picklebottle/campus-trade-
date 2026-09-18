"""
Small helpers shared across routers.
"""
import base64
import os
import re
import uuid

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATA_URI_RE = re.compile(r"^data:image/(?P<ext>\w+);base64,(?P<data>.+)$")


def save_image(source: str) -> str:
    """
    Accepts either:
      - a base64 data URI (e.g. from a browser <input type=file> + FileReader), or
      - an already-hosted http(s) URL, which is passed through unchanged.
    Returns a URL path the frontend can load directly (e.g. "/uploads/abc123.jpg").
    """
    if source.startswith("http://") or source.startswith("https://"):
        return source

    match = DATA_URI_RE.match(source)
    if not match:
        raise ValueError("Unsupported image format — expected a data URI or http(s) URL.")

    ext = match.group("ext").lower()
    if ext not in {"jpeg", "jpg", "png", "webp", "gif"}:
        ext = "jpg"

    raw = base64.b64decode(match.group("data"))
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(raw)

    return f"/uploads/{filename}"
