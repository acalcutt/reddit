"""Lightweight shim for Baseplate used in tests.

This provides minimal classes and attributes required by r2 during test
collection/bootstrap so tests can run without the full baseplate package.
"""
from types import SimpleNamespace


class BaseplateObserver:
    pass


class ServerSpanObserver(BaseplateObserver):
    pass


class SpanObserver(BaseplateObserver):
    def __init__(self, name=None):
        self.name = name


class Baseplate:
    def __init__(self, *args, **kwargs):
        self.tracer = None

    def register(self, observer):
        return None

    def add_to_context(self, key, value):
        return None

    def configure_logging(self):
        return None

    def configure_context(self):
        return None

    def configure_tracing(self, *args, **kwargs):
        return None

    def configure_tracer(self, *args, **kwargs):
        return None


# Minimal config helpers referenced by r2
class _Optional:
    def __init__(self, inner=None):
        self.inner = inner


class _Endpoint:
    pass


config = SimpleNamespace(Optional=_Optional, Endpoint=_Endpoint)


__all__ = [
    'Baseplate', 'BaseplateObserver', 'ServerSpanObserver', 'SpanObserver',
    'config',
]
