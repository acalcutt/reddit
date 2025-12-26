def datetime_from_uuid1(u):
    # Minimal shim for cassandra.util.datetime_from_uuid1 used in tests.
    # Return None — callers in tests should mock this if they rely on it.
    return None

__all__ = ["datetime_from_uuid1"]
