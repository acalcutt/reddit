"""Minimal weberror shim to provide just what's needed by r2 for Python 3.

This is intentionally tiny: it avoids importing the system `weberror`
which contains Python 2-only syntax that breaks the CI. It implements
the minimal API surface used by the project (`evalexception.EvalException`
and `reporter.Reporter`).
"""

__all__ = ["evalexception", "reporter"]
