# pycassa ColumnFamily compatibility shim
# Re-exports ColumnFamily from r2.lib.db.cassandra_compat

from r2.lib.db.cassandra_compat import ColumnFamily, NotFoundException

__all__ = ['ColumnFamily', 'NotFoundException']
