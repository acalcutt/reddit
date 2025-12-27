"""Small utility shim exposing OrderedDict and convert_uuid_to_time used in r2."""
from collections import OrderedDict

from cassandra.util import datetime_from_uuid1


def convert_uuid_to_time(u):
    try:
        return datetime_from_uuid1(u)
    except Exception:
        return None


__all__ = [
    'OrderedDict',
    'convert_uuid_to_time',
]
