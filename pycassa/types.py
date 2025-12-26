"""Minimal types shim for code importing pycassa.types."""
class LongType:
    pass

class DateType:
    pass

class IntegerType:
    pass

class AsciiType:
    pass

class UTF8Type:
    pass


class CompositeType:
    """Minimal stub for pycassa.types.CompositeType used by the codebase.

    The real CompositeType provides serialization behavior; tests only need
    the existence and ability to be instantiated with element types.
    """
    def __init__(self, *types):
        self.types = types

    def __repr__(self):
        return f"CompositeType({', '.join(getattr(t, '__name__', str(t)) for t in self.types)})"
