"""Minimal pool shim exposing ConnectionPool name used by r2 code."""
from r2.lib.db.cassandra_compat import ConnectionPool

class ConnectionPool(ConnectionPool):
    # direct alias to compat ConnectionPool
    pass
