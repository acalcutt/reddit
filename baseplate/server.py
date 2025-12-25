"""Compatibility wrapper for `baseplate.server`.

Expose `einhorn` from newer baseplate if available.
"""
import importlib

_mod = None
try:
	_mod = importlib.import_module('baseplate.server')
except Exception:
	_mod = None

if _mod is not None and hasattr(_mod, 'einhorn'):
	einhorn = _mod.einhorn
else:
	einhorn = None
