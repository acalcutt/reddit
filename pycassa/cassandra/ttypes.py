# Minimal ttypes shim providing NotFoundException and ConsistencyLevel
# used by legacy code migrating from pycassa to cassandra-driver

class NotFoundException(Exception):
    pass


class ConsistencyLevel:
    """Cassandra consistency levels compatible with pycassa's API.

    These map to the cassandra-driver's ConsistencyLevel values.
    """
    ANY = 0
    ONE = 1
    TWO = 2
    THREE = 3
    QUORUM = 4
    ALL = 5
    LOCAL_QUORUM = 6
    EACH_QUORUM = 7
    SERIAL = 8
    LOCAL_SERIAL = 9
    LOCAL_ONE = 10
