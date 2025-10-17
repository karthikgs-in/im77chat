"""Local installable imghdr shim package.

This duplicates the repo shim but packages it for pip installation inside the
hosted venv during dependency processing.
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
    data = h
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

    if Image is not None:
        try:
            if hasattr(file, "read"):
                content = file.read() if data is None else (data + file.read())
                buf = io.BytesIO(content)
                img = Image.open(buf)
            else:
                img = Image.open(file)
            fmt = getattr(img, "format", None)
            if fmt:
                return fmt.lower()
        except Exception:
            pass

    return _header_checks(data)
