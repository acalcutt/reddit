"""Compatibility wrapper for thrift client factory.

Prefer `baseplate.clients.thrift.ThriftContextFactory` when available.
"""
import importlib

_mod = None
try:
    _mod = importlib.import_module('baseplate.clients.thrift')
except Exception:
    try:
        _mod = importlib.import_module('baseplate.integration.thrift')
    except Exception:
        _mod = None

if _mod is not None and hasattr(_mod, 'ThriftContextFactory'):
    ThriftContextFactory = _mod.ThriftContextFactory
else:
    class ThriftContextFactory:
        def __init__(self, *args, **kwargs):
            pass
