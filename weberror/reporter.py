"""Minimal Reporter base class used by r2's error reporters.

This provides a tiny, well-behaved API surface that `r2` subclasses
to integrate with Sentry or logging. It's intentionally small and
safe for Python 3.
"""

class Reporter:
    @classmethod
    def get_module_versions(cls):
        return {}

    @classmethod
    def add_http_context(cls, client):
        pass

    @classmethod
    def add_reddit_context(cls, client):
        pass

    @classmethod
    def add_user_context(cls, client):
        pass

    @classmethod
    def get_raven_client(cls):
        return None

    @classmethod
    def capture_exception(cls, exc_info=None):
        return None

    def format_text(self, exc_data):
        try:
            if hasattr(exc_data, 'exception_formatted'):
                text = "\n".join(exc_data.exception_formatted)
            else:
                text = str(exc_data)
        except Exception:
            text = ""
        return text, {}

    def report(self, exc_data):
        pass
