"""Compatibility layer for `pylons.error`.

Provides error handling utilities for Mako templates that were
previously provided by Pylons.
"""
import sys


def handle_mako_error(context, error):
    """Error handler for Mako template rendering.

    This is used as the `error_handler` argument to Mako's TemplateLookup.
    When a template error occurs, this function is called to handle it.

    In the original Pylons implementation, this would format the error
    nicely. For now, we simply re-raise the exception.

    Args:
        context: The Mako context object
        error: The exception that occurred

    Raises:
        The original exception with its traceback preserved.
    """
    raise error.with_traceback(sys.exc_info()[2])


__all__ = ['handle_mako_error']
