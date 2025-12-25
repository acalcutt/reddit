"""Compatibility shim for projects that import ``simplejson``.

This module delegates to the stdlib ``json`` module when the external
``simplejson`` package is not installed. It provides the commonly used
functions and types so existing code (and templates) that import
``simplejson`` continue to work without adding an external dependency.
"""

try:
    # Prefer the real simplejson if installed
    import simplejson as _simplejson  # type: ignore
except Exception:
    import json as _simplejson

# Re-export common attributes
loads = _simplejson.loads
load = getattr(_simplejson, 'load', None)
dumps = _simplejson.dumps
dump = getattr(_simplejson, 'dump', None)
JSONEncoder = getattr(_simplejson, 'JSONEncoder', None)
JSONDecoder = getattr(_simplejson, 'JSONDecoder', None)
loads = _simplejson.loads

# Provide a simple version attribute if missing
__version__ = getattr(_simplejson, '__version__', 'stdlib-json')

# Expose the module-level API
__all__ = [
    'loads', 'load', 'dumps', 'dump', 'JSONEncoder', 'JSONDecoder', '__version__'
]
