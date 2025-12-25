"""Compatibility layer for `pylons.wsgiapp`.

This module attempts to import the real `pylons.wsgiapp` when available. If
not, it provides a lightweight `PylonsApp` fallback that establishes the
minimal objects expected by `r2` middleware (so migration can proceed
without requiring the full Pylons runtime immediately).
"""
import importlib
import os
import sys
from types import SimpleNamespace


def _import_external(name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    saved = list(sys.path)
    try:
        sys.path = [p for p in sys.path if not p or os.path.abspath(p) != current_dir]
        return importlib.import_module(name)
    except Exception:
        return None
    finally:
        sys.path = saved


_external = _import_external('pylons.wsgiapp')
if _external is not None:
    from pylons.wsgiapp import *  # type: ignore
else:
    class PylonsApp:
        """A very small PylonsApp polyfill.

        It intentionally implements only the bits `r2` expects: construction
        with a `config` mapping and a `setup_app_env` hook that places a
        minimal `pylons.pylons` object into the WSGI `environ`.
        """

        def __init__(self, config=None, **kwargs):
            self.config = config or {}
            self.package_name = self.config.get('pylons.package')
            self.helpers = self.config.get('pylons.h')
            self.globals = self.config.get('pylons.app_globals')
            self.environ_config = self.config.get('pylons.environ_config', {})
            self.request_options = self.config.get('pylons.request_options', {})
            self.response_options = self.config.get('pylons.response_options', {})
            self.controller_classes = {}

        def setup_app_env(self, environ, start_response):
            # Provide a minimal pylons.pylons-style object expected by code
            pylons_obj = SimpleNamespace()
            pylons_obj.config = self.config
            pylons_obj.request = SimpleNamespace()
            pylons_obj.response = SimpleNamespace()
            pylons_obj.app_globals = self.globals
            pylons_obj.h = self.helpers
            pylons_obj.tmpl_context = SimpleNamespace()
            pylons_obj.translator = SimpleNamespace()

            environ['pylons.pylons'] = pylons_obj
            environ['pylons.environ_config'] = self.environ_config

        def __call__(self, environ, start_response):
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']

    __all__ = ['PylonsApp']
