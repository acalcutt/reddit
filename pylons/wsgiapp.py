"""Compatibility layer for `pylons.wsgiapp`.

Provides a lightweight `PylonsApp` fallback that establishes the
minimal objects expected by `r2` middleware for migration to Pyramid.
"""
import traceback
from types import SimpleNamespace
from importlib import import_module
from webob import Request as WebObRequest, Response as WebObResponse
import pylons


class _DefaultTranslator:
    """Minimal translator that returns strings unchanged."""
    def gettext(self, s):
        return s

    def ngettext(self, s, p, n):
        return s if n == 1 else p

    def __call__(self, s):
        return s


class _DefaultTmplContext(SimpleNamespace):
    """Default template context with common attributes."""
    def __init__(self):
        super().__init__()
        self.have_sent_bucketing_event = False
        self.subdomain = None
        self.user = None


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
        pylons_obj.app_globals = self.globals
        pylons_obj.h = self.helpers
        pylons_obj.tmpl_context = _DefaultTmplContext()
        pylons_obj.translator = _DefaultTranslator()

        # Create real WebOb request/response objects and push them onto
        # pylons' LocalStack objects so controllers and helpers can use
        # `from pylons import request, response` as expected.
        request_obj = WebObRequest(environ)
        response_obj = WebObResponse()

        pylons.request._push_object(request_obj)
        pylons.response._push_object(response_obj)
        pylons.tmpl_context._push_object(pylons_obj.tmpl_context)
        pylons.translator._push_object(pylons_obj.translator)

        environ['pylons.pylons'] = pylons_obj
        environ['pylons.environ_config'] = self.environ_config

    def __call__(self, environ, start_response):
        # Ensure environment is prepared (push request/response, tmpl context)
        try:
            self.setup_app_env(environ, start_response)
        except Exception:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b'Internal Server Error']

        # RoutesMiddleware (or other routing) places routing args here.
        routing = environ.get('wsgiorg.routing_args')
        if routing:
            environ['pylons.routes_dict'] = routing[1]

        routes_dict = environ.get('pylons.routes_dict', {})
        controller_name = routes_dict.get('controller')

        if not controller_name:
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']

        # Try to resolve the controller class and call it as a WSGI app.
        controller_cls = None
        # Prefer a find_controller hook if the app implements it (RedditApp)
        find_fn = getattr(self, 'find_controller', None)
        if callable(find_fn):
            try:
                controller_cls = find_fn(controller_name)
            except Exception:
                controller_cls = None

        if controller_cls is None:
            try:
                controllers_mod = import_module(self.package_name + '.controllers')
                controller_cls = controllers_mod.get_controller(controller_name)
            except Exception:
                controller_cls = None

        if controller_cls is None:
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']

        try:
            # Instantiate and call the controller (WSGIController subclass).
            controller = controller_cls()
            resp_iter = controller(environ, start_response)

            # Ensure pushed pylons locals are popped when the response is
            # finished or the iterator is closed.
            def closing_iterator(it):
                try:
                    for chunk in it:
                        yield chunk
                finally:
                    try:
                        pylons.request._pop_object()
                    except Exception:
                        pass
                    try:
                        pylons.response._pop_object()
                    except Exception:
                        pass
                    try:
                        pylons.tmpl_context._pop_object()
                    except Exception:
                        pass
                    try:
                        pylons.translator._pop_object()
                    except Exception:
                        pass

            return closing_iterator(resp_iter)
        except Exception as e:
            tb = traceback.format_exc()
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [f"Error: {e}\n\n{tb}".encode('utf-8')]


__all__ = ['PylonsApp']
