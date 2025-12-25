"""Compatibility layer for `baseplate.lib`.

This module attempts to import the real `baseplate.lib.*` modules when
available. If not present, it falls back to the in-repo compatibility
modules (`baseplate.config`, `baseplate.crypto`, etc.).
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Optional


def _try_import(primary: str, fallback: Optional[str] = None) -> Optional[ModuleType]:
    try:
        return importlib.import_module(primary)
    except Exception:
        if fallback:
            try:
                return importlib.import_module(fallback)
            except Exception:
                return None
        return None


# Expose `config` module as `baseplate.lib.config` when possible.
# Prefer the installed `baseplate.lib.config`; fall back to `baseplate.config`.
config = _try_import("baseplate.lib.config", "baseplate.config")

# Crypto helpers
crypto = _try_import("baseplate.lib.crypto", "baseplate.crypto")

# Events package
events = _try_import("baseplate.lib.events", "baseplate.events")

# Thrift / connection pool helpers
thrift_pool = _try_import("baseplate.lib.thrift_pool", "baseplate.lib.thrift_pool")

# Provide a friendly __all__ for downstream `from baseplate.lib import config` style imports
__all__ = ["config", "crypto", "events", "thrift_pool"]
