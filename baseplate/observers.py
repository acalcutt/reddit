"""Compatibility shim for `baseplate.observers`.

This module tries to import the real `baseplate.observers`. If it's
available, re-export the symbols. Otherwise provide minimal no-op
classes matching the expected API so the application can import them
during bootstrap and tests.
"""
from __future__ import annotations

import importlib
from typing import Any


try:
    _mod = importlib.import_module("baseplate.observers")
    BaseplateObserver = getattr(_mod, "BaseplateObserver")
    ServerSpanObserver = getattr(_mod, "ServerSpanObserver")
    SpanObserver = getattr(_mod, "SpanObserver")
    __all__ = ["BaseplateObserver", "ServerSpanObserver", "SpanObserver"]
except Exception:
    class BaseplateObserver:
        """Minimal fallback observer base class (no-op)."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class ServerSpanObserver(BaseplateObserver):
        """Fallback server-span observer (no-op)."""
        def bind_server_span(self, *args: Any, **kwargs: Any) -> None:
            return None

    class SpanObserver(BaseplateObserver):
        """Fallback span observer (no-op)."""
        def bind_span(self, *args: Any, **kwargs: Any) -> None:
            return None

    __all__ = ["BaseplateObserver", "ServerSpanObserver", "SpanObserver"]
