"""Startup shim to ensure `imghdr` is available in environments that lack the
standard-library `imghdr` module (some hosted runtimes). This file is executed
automatically on interpreter startup when present on sys.path.

It attempts to import the standard `imghdr` and, if missing, loads the local
`imghdr.py` file that ships with the repo.
"""
import importlib
import sys
import os

try:
    import imghdr as _std_imghdr  # type: ignore
except Exception:
    # If the stdlib imghdr is not found, add repo root to sys.path and import
    # the bundled `imghdr.py` (this repo provides a fallback shim).
    repo_root = os.path.dirname(__file__)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        _shim = importlib.import_module('imghdr')
        # Expose it as the stdlib name
        sys.modules['imghdr'] = _shim
    except Exception:
        # Give up silently; downstream imports will still raise if something
        # really needs imghdr and the shim fails. We avoid crashing startup.
        pass
