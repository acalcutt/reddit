"""Minimal Pylons compatibility shim for tests and progressive migration.

Provides simple LocalStack objects for `config`, `app_globals`, `tmpl_context`, and
`translator`, and a small url pushable object. This is intentionally lightweight
and intended to be replaced by Pyramid-specific code during migration.
"""
from typing import Any, List


class LocalStack:
    """A tiny stack-like holder that forwards attribute and item access to the
    currently pushed object.
    """

    def __init__(self):
        self._stack: List[Any] = []

    def _push_object(self, obj: Any) -> None:
        self._stack.append(obj)

    def _pop_object(self) -> Any:
        return self._stack.pop()

    def __getattr__(self, name: str) -> Any:
        if not self._stack:
            raise AttributeError(f"no object pushed to LocalStack (requested {name})")
        return getattr(self._stack[-1], name)

    def get(self, key, default=None):
        if not self._stack:
            return default
        top = self._stack[-1]
        try:
            return top.get(key, default)
        except Exception:
            return getattr(top, key, default)

    def __getitem__(self, key):
        if not self._stack:
            raise KeyError(key)
        return self._stack[-1][key]

    def __bool__(self):
        return bool(self._stack)


class UrlPushable:
    """Holds a pushed URL generator (e.g. routes.util.URLGenerator).

    Only minimal API is implemented (_push_object/_pop_object). If code calls
    `url_for` on this object it will attempt to call a known method on the
    underlying generator.
    """

    def __init__(self):
        self._stack: List[Any] = []

    def _push_object(self, obj: Any) -> None:
        self._stack.append(obj)

    def _pop_object(self) -> Any:
        return self._stack.pop()

    def _get_current(self):
        if not self._stack:
            return None
        return self._stack[-1]

    def url_for(self, *args, **kwargs):
        gen = self._get_current()
        if gen is None:
            raise RuntimeError("no URL generator pushed")
        # routes.util.URLGenerator exposes a ``generate`` method; accept either
        # a callable or a generate attribute
        if hasattr(gen, 'generate'):
            return gen.generate(*args, **kwargs)
        if callable(gen):
            return gen(*args, **kwargs)
        raise RuntimeError("pushed URL generator is not callable/generate")


# Module-level instances expected by code/tests
config = LocalStack()
app_globals = LocalStack()
tmpl_context = LocalStack()
translator = LocalStack()
url = UrlPushable()


# Backwards-compatible aliases (sometimes code imports ``from pylons import g``)
g = app_globals
c = tmpl_context


__all__ = [
    'config', 'app_globals', 'tmpl_context', 'translator', 'url', 'g', 'c',
    'LocalStack', 'UrlPushable',
]
