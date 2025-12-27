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
	class _EinhornShim:
		"""Minimal Einhorn shim used when real einhorn isn't available.

		Methods mirror the subset used by r2: `is_worker`, `ack_startup`,
		and `get_socket`. `is_worker` returns False so startup ack is skipped.
		"""
		def is_worker(self) -> bool:
			return False

		def ack_startup(self) -> None:
			return None

		def get_socket(self):
			raise RuntimeError("Einhorn socket not available in this process")

	einhorn = _EinhornShim()
