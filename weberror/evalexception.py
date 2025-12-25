"""Tiny EvalException shim used by r2 to patch out unsafe endpoints.

Only the attributes used by `r2` are implemented so the real weberror
package can be safely shadowed when it contains Python2-only syntax.
"""

class EvalException(Exception):
    """Minimal EvalException replacement.

    r2 only needs the `post_traceback` and `relay` attributes so we
    provide callable defaults that can be monkeypatched by `r2`.
    """

    @staticmethod
    def post_traceback(*args, **kwargs):
        return None

    @staticmethod
    def relay(*args, **kwargs):
        return None


def make_eval_exception(*args, **kwargs):
    return EvalException(*args, **kwargs)
