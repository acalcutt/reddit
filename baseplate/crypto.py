"""Compatibility wrapper for crypto primitives.

Prefer `baseplate.lib.crypto.MessageSigner` when available.
"""
import importlib

_mod = None
try:
    _mod = importlib.import_module('baseplate.lib.crypto')
except Exception:
    try:
        _mod = importlib.import_module('baseplate.crypto')
    except Exception:
        _mod = None

if _mod is not None and hasattr(_mod, 'MessageSigner'):
    MessageSigner = _mod.MessageSigner
else:
    class MessageSigner:
        def __init__(self, *args, **kwargs):
            pass
