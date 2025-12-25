"""Compatibility shim for projects that import ``simplejson``.

This module delegates to the stdlib ``json`` module when the external
``simplejson`` package is not installed. It avoids importing ``simplejson``
directly to prevent circular imports when this module is placed on sys.path
alongside the project (which previously caused an AttributeError during
import).
"""

import importlib
import importlib.util

# Try to import the external `simplejson` package if it is available; if not,
# fall back to the stdlib `json` module. Using importlib.util.find_spec avoids
# directly importing `simplejson` and prevents circular import issues when
# this project contains a top-level `simplejson.py` (this file).
_spec = importlib.util.find_spec("simplejson")
if _spec is not None:
    _backend = importlib.import_module("simplejson")
else:
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
