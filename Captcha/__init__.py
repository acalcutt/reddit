"""Compatibility shim for the legacy `Captcha` package import used in tests.

Tries to import a real `captcha` package (lowercase). If found, expose a
`Base` class that wraps the modern API as a compatibility layer. Otherwise
provide a minimal no-op `Base` class so tests can import it.
"""
from __future__ import annotations

import importlib
from typing import Any


def _make_fallback_base():
    class Base:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def generate(self, *args: Any, **kwargs: Any) -> bytes:
            raise NotImplementedError("No captcha backend available")

    return Base


# Prefer modern `captcha` package if available
try:
    _captcha_mod = importlib.import_module("captcha")
except Exception:
    Base = _make_fallback_base()
else:
    # The `captcha` package doesn't expose a `Base` class; provide a thin
    # adapter that offers a `generate` method to resemble legacy behaviour.
    class Base:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._gen = None
            # try ImageCaptcha if available
            try:
                from captcha.image import ImageCaptcha

                self._gen = ImageCaptcha()
            except Exception:
                self._gen = None

        def generate(self, text: str) -> bytes:
            if self._gen is None:
                raise NotImplementedError("captcha.ImageCaptcha not available")
            buf = self._gen.generate(text)
            return buf.getvalue()

__all__ = ["Base"]
