# Pylons controllers.util compatibility shim
# Provides abort() function using webob.exc

from webob import exc as webob_exc


def abort(status_code, detail=None, headers=None, comment=None):
    """Abort the request with an HTTP error.

    This is a compatibility shim for pylons.controllers.util.abort
    that uses webob.exc exceptions.
    """
    # Map status codes to webob exception classes
    exception_map = {
        301: webob_exc.HTTPMovedPermanently,
        302: webob_exc.HTTPFound,
        400: webob_exc.HTTPBadRequest,
        401: webob_exc.HTTPUnauthorized,
        403: webob_exc.HTTPForbidden,
        404: webob_exc.HTTPNotFound,
        405: webob_exc.HTTPMethodNotAllowed,
        406: webob_exc.HTTPNotAcceptable,
        409: webob_exc.HTTPConflict,
        410: webob_exc.HTTPGone,
        413: webob_exc.HTTPRequestEntityTooLarge,
        429: webob_exc.HTTPTooManyRequests,
        500: webob_exc.HTTPInternalServerError,
        502: webob_exc.HTTPBadGateway,
        503: webob_exc.HTTPServiceUnavailable,
    }

    exc_class = exception_map.get(status_code, webob_exc.HTTPException)

    kwargs = {}
    if detail:
        kwargs['detail'] = str(detail)
    if comment:
        kwargs['comment'] = comment

    exc = exc_class(**kwargs)

    if headers:
        for header in headers:
            if isinstance(header, tuple) and len(header) == 2:
                exc.headers.add(header[0], header[1])

    raise exc
