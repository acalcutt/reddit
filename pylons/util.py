"""Pylons util compatibility shim.

Provides minimal implementations of ContextObj, AttribSafeContextObj, and
PylonsContext for code that imports from pylons.util.
"""
from types import SimpleNamespace


class ContextObj(SimpleNamespace):
    """A simple namespace object that acts as a context container.

    This is a minimal shim for the original Pylons ContextObj.
    """
    pass


class AttribSafeContextObj(ContextObj):
    """A ContextObj that returns None for missing attributes instead of raising.

    This is useful for template contexts where missing attributes should
    gracefully return None.
    """

    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None


class PylonsContext:
    """Minimal shim for PylonsContext.

    In original Pylons, this held references to the request, response,
    tmpl_context, etc. This shim provides a simple container.
    """

    def __init__(self):
        self.request = None
        self.response = None
        self.tmpl_context = None
        self.app_globals = None
        self.config = None
        self.translator = None
        self.url = None

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None


__all__ = ['ContextObj', 'AttribSafeContextObj', 'PylonsContext']
