"""Compatibility wrapper for `baseplate.lib.thrift_pool`.

Prefer the real implementation when available.
"""
import importlib

_mod = None
try:
    _mod = importlib.import_module('baseplate.lib.thrift_pool')
except Exception:
    _mod = None

if _mod is not None and hasattr(_mod, 'ThriftConnectionPool'):
    ThriftConnectionPool = _mod.ThriftConnectionPool
else:
    class ThriftConnectionPool:
        def __init__(self, *args, **kwargs):
            pass
