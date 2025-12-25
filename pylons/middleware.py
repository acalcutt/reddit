"""Compatibility layer for `pylons.middleware`.

Prefer importing the real `pylons.middleware` from site-packages when
available. If not present, expose minimal fallback implementations used by
this codebase so migration to Pyramid can proceed incrementally.
"""
import importlib
import os
import sys


def _import_external(name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    saved = list(sys.path)
    try:
        # remove the local pylons package directory so importlib will find
        # an installed `pylons` package if present on sys.path
        sys.path = [p for p in sys.path if not p or os.path.abspath(p) != current_dir]
        return importlib.import_module(name)
    except Exception:
        return None
    finally:
        sys.path = saved


_external = _import_external('pylons.middleware')
if _external is not None:
    # re-export everything from the real package
    from pylons.middleware import *  # type: ignore
else:
    # Minimal fallbacks -------------------------------------------------
    from webob import Response


    def ErrorHandler(app, global_conf, **errorware):
        # No-op error handler for environments where WebError / EvalException
        # are not available yet. Simply return the wrapped app.
        return app


    class StatusCodeRedirect:
        def __init__(self, app, errors=(400, 401, 403, 404), path='/error/document'):
            self.app = app
            self.error_path = path

        def __call__(self, environ, start_response):
            return self.app(environ, start_response)


    def debugger_filter_factory(global_conf, **kwargs):
        def filter(app):
            return app

        return filter


    def debugger_filter_app_factory(app, global_conf, **kwargs):
        return app

    __all__ = ['ErrorHandler', 'StatusCodeRedirect', 'debugger_filter_factory', 'debugger_filter_app_factory']
