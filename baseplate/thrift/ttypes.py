"""
Minimal Thrift type stubs for baseplate.

Provide basic types so imports like `import baseplate.thrift.ttypes`
succeed during application startup. These are lightweight placeholders
and should be replaced with the real Thrift-generated types for full
functionality.
"""

class ActivityInfo:
    """Placeholder matching activity thrift's ActivityInfo."""

    def __init__(self, count=None, is_fuzzed=None):
        self.count = count
        self.is_fuzzed = is_fuzzed

    def read(self, iprot):
        pass

    def write(self, oprot):
        pass

    def __repr__(self):
        return f"ActivityInfo(count={self.count}, is_fuzzed={self.is_fuzzed})"


class InvalidContextIDException(Exception):
    """Placeholder exception type."""
    pass


__all__ = ["ActivityInfo", "InvalidContextIDException"]
