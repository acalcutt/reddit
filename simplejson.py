"""Compatibility shim for projects that import ``simplejson``.

This module delegates to the stdlib ``json`` module when the external
``simplejson`` package is not installed. It avoids importing ``simplejson``
directly to prevent circular imports when this module is placed on sys.path
alongside the project (which previously caused an AttributeError during
import).
"""

import importlib
import importlib.util
import sys
import os

# Try to import the external `simplejson` package if it is available; if not,
# fall back to the stdlib `json` module.
#
# We must avoid importing the local `simplejson.py` (this file) which would
# lead to a circular import (the module would be partially-initialized and
# missing attributes). To do that we first try a normal import and check the
# imported module's `__file__`; if it points to this file we treat it as not
# found. If that doesn't work, we temporarily remove this file's directory
# from `sys.path` and try again so that an installed `simplejson` package in
# site-packages can be imported.

def _import_external_simplejson():
    try:
        # First attempt: regular import
        _ext = importlib.import_module("simplejson")
        # If the imported module is this file, pretend it doesn't exist
        if getattr(_ext, "__file__", None) and os.path.abspath(_ext.__file__) == os.path.abspath(__file__):
            raise ImportError
        return _ext
    except Exception:
        # Second attempt: remove current directory from sys.path and import
        current_dir = os.path.dirname(os.path.abspath(__file__))
        saved_path = list(sys.path)
        try:
            sys.path = [p for p in sys.path if not p or os.path.abspath(p) != current_dir]
            return importlib.import_module("simplejson")
        except Exception:
            return None
        finally:
            sys.path = saved_path


_backend = _import_external_simplejson()
if _backend is None:
    import json as _backend

# Re-export common attributes expected by code that imports `simplejson`.
loads = getattr(_backend, "loads")
load = getattr(_backend, "load", None)
dumps = getattr(_backend, "dumps")
dump = getattr(_backend, "dump", None)
JSONEncoder = getattr(_backend, "JSONEncoder", None)
JSONDecoder = getattr(_backend, "JSONDecoder", None)

# Provide a simple version attribute if missing
__version__ = getattr(_backend, "__version__", "stdlib-json")

# Expose the module-level API
__all__ = [
    "loads", "load", "dumps", "dump", "JSONEncoder", "JSONDecoder", "__version__"
]
