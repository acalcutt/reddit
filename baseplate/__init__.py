"""Compatibility layer for Baseplate.

This module attempts to adapt old import paths used in r2 to the newer
`baseplate` package layout. When the real `baseplate` package is installed
this module will re-export the relevant symbols from the proper
`baseplate.lib`/`baseplate.observers` modules. When not available, it
provides lightweight fallbacks so tests and bootstrap can proceed.
"""
import importlib
import types


def _import_or_none(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


# Try to re-export observers from new location
_observers = _import_or_none('baseplate.observers')
if _observers is not None:
    BaseplateObserver = getattr(_observers, 'BaseplateObserver', type('BaseplateObserver', (), {}))
    ServerSpanObserver = getattr(_observers, 'ServerSpanObserver', type('ServerSpanObserver', (), {}))
    SpanObserver = getattr(_observers, 'SpanObserver', type('SpanObserver', (), {}))
else:
    class BaseplateObserver:  # fallback
        pass

    class ServerSpanObserver(BaseplateObserver):
        pass

    class SpanObserver(BaseplateObserver):
        def __init__(self, name=None):
            self.name = name


# Export a Baseplate class (best-effort). Newer baseplate exposes a Baseplate
# class at top-level; if present, use it, otherwise provide a small shim.
_baseplate_mod = _import_or_none('baseplate')
if _baseplate_mod is not None and hasattr(_baseplate_mod, 'Baseplate'):
    Baseplate = _baseplate_mod.Baseplate
else:
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


# Config helpers: prefer baseplate.lib.config
_config_mod = _import_or_none('baseplate.lib.config') or _import_or_none('baseplate.config')
if _config_mod is not None:
    config = _config_mod
else:
    class _LocalConfigModule(types.SimpleNamespace):
        def Optional(self, inner=None):
            def parser(v):
                if v is None or v == '':
                    return None
                if callable(inner):
                    return inner(v)
                return v

            return parser

        def Endpoint(self, v):
            return str(v)

    config = _LocalConfigModule()


__all__ = ['Baseplate', 'BaseplateObserver', 'ServerSpanObserver', 'SpanObserver', 'config']


# Metrics compatibility: prefer the real metrics factory under
# `baseplate.lib.metrics.metrics_client_from_config` when available.
# Otherwise expose a no-op metrics client for development/testing.
_metrics_mod = _import_or_none('baseplate.lib.metrics') or _import_or_none('baseplate.metrics')
if _metrics_mod is not None and hasattr(_metrics_mod, 'metrics_client_from_config'):
    metrics_client_from_config = _metrics_mod.metrics_client_from_config
else:
    class _NoopMetricsClient:
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return None

            return _noop


    def metrics_client_from_config(config=None):
        """Return a noop metrics client when baseplate.lib.metrics isn't
        available in the runtime environment.
        """
        return _NoopMetricsClient()


__all__.append('metrics_client_from_config')
