"""Minimal imghdr shim using Pillow.

Streamlit imports `imghdr` from the standard library; some hosted runtimes may
lack it. This module provides a small `what()` implementation that uses
Pillow when available and simple header checks as fallback.
"""
from __future__ import annotations
import io
from typing import Optional

try:
    from PIL import Image
except Exception:
    Image = None


def _header_checks(h: bytes) -> Optional[str]:
    if not h:
        return None
    if h.startswith(b"\xFF\xD8"):
        return "jpeg"
    if h.startswith(b"\x89PNG"):
        return "png"
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if h.startswith(b"BM"):
        return "bmp"
    if h.startswith(b"II") or h.startswith(b"MM"):
        return "tiff"
    return None


def what(file, h: bytes | None = None) -> Optional[str]:
    """Determine the image type.

    Accepts a filename or a file-like object. Returns a lowercase image type
    string (e.g., 'png', 'jpeg') or None.
    """
    data = h
    # if file-like, try to read a small header
    try:
        if data is None:
            if hasattr(file, "read"):
                pos = None
                try:
                    pos = file.tell()
                except Exception:
                    pos = None
                data = file.read(32)
                try:
                    if pos is not None:
                        file.seek(pos)
                except Exception:
                    pass
            else:
                with open(file, "rb") as f:
                    data = f.read(32)
    except Exception:
        data = None

    # Prefer Pillow if available
    if Image is not None:
        try:
            if hasattr(file, "read"):
                # read full content into memory
                content = file.read() if data is None else (data + file.read())
                buf = io.BytesIO(content)
                img = Image.open(buf)
            else:
                img = Image.open(file)
            fmt = getattr(img, "format", None)
            if fmt:
                return fmt.lower()
        except Exception:
            # Pillow couldn't identify; fall back to header checks
            pass

    # header checks fallback
    return _header_checks(data)
