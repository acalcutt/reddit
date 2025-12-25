"""Compatibility layer for `pylons.wsgiapp`.

Provides a lightweight `PylonsApp` fallback that establishes the
minimal objects expected by `r2` middleware for migration to Pyramid.
"""
from types import SimpleNamespace


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
