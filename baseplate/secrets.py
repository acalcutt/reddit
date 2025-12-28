"""Compatibility shim for baseplate.secrets used by older r2 code.

Provides `secrets_store_from_config` returning a simple noop secrets
store suitable for development and tests. If a real secrets implementation
is present under `baseplate.lib.secrets`, prefer that.
"""
import importlib


def _import_or_none(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


# Prefer a real implementation if available
_real = _import_or_none('baseplate.lib.secrets') or _import_or_none('baseplate.secrets')
if _real is not None and hasattr(_real, 'secrets_store_from_config'):
    secrets_store_from_config = _real.secrets_store_from_config
else:
    class _NoopSecretsStore:
        def get(self, key, default=None):
            return default

        def get_bytes(self, key, default=None):
            return default

        def put(self, key, value):
            return None

    def secrets_store_from_config(config=None):
        """Return a noop secrets store for development."""
        return _NoopSecretsStore()

__all__ = ['secrets_store_from_config']
