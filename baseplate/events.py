"""Compatibility wrapper for `baseplate.events`.

Prefer `baseplate.lib.events.EventQueue` when available; otherwise provide
a simple placeholder so tests/bootstrapping can assign `EventQueue`.
"""
import importlib

_mod = None
try:
	_mod = importlib.import_module('baseplate.lib.events')
except Exception:
	try:
		_mod = importlib.import_module('baseplate.events')
	except Exception:
		_mod = None

if _mod is not None and hasattr(_mod, 'EventQueue'):
	EventQueue = _mod.EventQueue
else:
	EventQueue = None
