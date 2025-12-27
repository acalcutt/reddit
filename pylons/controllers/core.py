# Pylons controllers.core compatibility shim
# Provides WSGIController base class for Pyramid migration

from webob import Response
from webob.exc import HTTPException
import pylons


class WSGIController:
    """A WSGI Controller base class.

    This is a compatibility shim that mimics the behavior of the original
    Pylons WSGIController. It:
    1. Calls __before__() before the action
    2. Dispatches to the action method based on environ['pylons.routes_dict']['action']
    3. Calls __after__() after the action
    4. Returns a WSGI response
    """

    def __before__(self):
        """Called before the action method. Override in subclasses."""
        pass

    def __after__(self):
        """Called after the action method. Override in subclasses."""
        pass

    def __call__(self, environ, start_response):
        """WSGI interface - dispatch to the appropriate action."""
        try:
            # Call __before__ hook
            self.__before__()

            # Get the action from the routes dict
            routes_dict = environ.get('pylons.routes_dict', {})
            action_name = routes_dict.get('action')

            if not action_name:
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [b'Action not found']

            # Get the action method
            action = getattr(self, action_name, None)
            if action is None:
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [f'Action {action_name} not found'.encode('utf-8')]

            # Call the action
            result = action()

            # Call __after__ hook
            self.__after__()

            # Handle the response
            response = pylons.response._current_obj()

            # If action returned something, use it as body
            if result is not None:
                if isinstance(result, bytes):
                    response.body = result
                elif isinstance(result, str):
                    response.text = result

            # Return the WSGI response
            return response(environ, start_response)

        except HTTPException as e:
            # HTTP exceptions are valid responses (redirects, errors, etc.)
            return e(environ, start_response)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [f'Controller error: {e}\n\n{tb}'.encode('utf-8')]


__all__ = ['WSGIController']
