"""Compatibility shim for `baseplate.crypto` used by legacy r2 services.

This module prefers an implementation under `baseplate.lib.crypto` when
available; otherwise it provides a minimal `SignatureError` and a
`validate_signature` no-op suitable for development and testing.
"""
import importlib


def _import_or_none(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


_real = _import_or_none('baseplate.lib.crypto') or _import_or_none('baseplate.crypto')
if _real is not None and hasattr(_real, 'validate_signature'):
    validate_signature = _real.validate_signature
    SignatureError = getattr(_real, 'SignatureError', Exception)
else:
    class SignatureError(Exception):
        pass


    def validate_signature(secret, payload):
        """No-op signature validation for development.

        In production this should validate payload signatures and raise
        `SignatureError` on failure. For local development we accept all
        payloads.
        """
        return True


__all__ = ['validate_signature', 'SignatureError']
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
