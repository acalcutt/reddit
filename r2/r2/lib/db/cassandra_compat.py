"""A minimal compatibility layer providing a subset of pycassa's
ConnectionPool and ColumnFamily APIs on top of the DataStax cassandra-driver.

This implements a simple storage model where each column family is stored
as a CQL table with schema:

  CREATE TABLE IF NOT EXISTS keyspace.cf_name (
      key text PRIMARY KEY,
      columns map<text, blob>
  )

Values are stored as pickled blobs. This is intentionally small and only
implements the operations used by the legacy code (multiget, get, insert,
remove, xget). It should be replaced with a proper CQL model in a full
refactor.
"""
from __future__ import annotations

import pickle
from collections import OrderedDict
from typing import Dict, Iterable, Optional

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, BatchStatement, BatchType
from cassandra import InvalidRequest

# Compatibility constants for pycassa types
UTF8_TYPE = 'org.apache.cassandra.db.marshal.UTF8Type'
ASCII_TYPE = 'org.apache.cassandra.db.marshal.AsciiType'
TIME_UUID_TYPE = 'org.apache.cassandra.db.marshal.TimeUUIDType'
LONG_TYPE = 'org.apache.cassandra.db.marshal.LongType'
INT_TYPE = 'org.apache.cassandra.db.marshal.Int32Type'
COUNTER_COLUMN_TYPE = 'org.apache.cassandra.db.marshal.CounterColumnType'

class NotFoundException(Exception):
    pass


class ConnectionPool:
    """Simple pool that holds a single Cluster and Session per keyspace.

    api: ConnectionPool(keyspace, server_list=[...], **kwargs)
    """
    def __init__(self, keyspace, server_list=None, **kwargs):
        self.keyspace = keyspace
        if not server_list:
            server_list = ["127.0.0.1"]
        # server_list items may be host:port
        self.server_list = server_list  # Store for compatibility
        hosts = [s.split(':', 1)[0] for s in server_list]
        self.cluster = Cluster(hosts)
        self.session = self.cluster.connect()
        try:
            self.session.set_keyspace(keyspace)
        except InvalidRequest:
            # keyspace may not exist yet; caller should create it
            pass


class SystemManager:
    """Minimal manager providing create_keyspace and create_column_family
    compatible with the expectations of the legacy code.
    """
    def __init__(self, host='127.0.0.1'):
        host_only = host.split(':', 1)[0]
        self.cluster = Cluster([host_only])
        self.session = self.cluster.connect()

    def create_keyspace(self, keyspace, strategy_options=None, replication_factor=1):
        # default to SimpleStrategy
        rf = replication_factor
        cql = "CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class':'SimpleStrategy','replication_factor': '%d'};" % (keyspace, rf)
        self.session.execute(SimpleStatement(cql))

    def create_column_family(self, keyspace, cf_name, **kwargs):
        # create a simple table with a map<text, blob> to emulate thrift CF
        cql = (
            "CREATE TABLE IF NOT EXISTS %s.%s (\n"
            "  key text PRIMARY KEY,\n"
            "  columns map<text, blob>\n"
            ")" % (keyspace, cf_name)
        )
        # ensure keyspace exists
        try:
            self.session.set_keyspace(keyspace)
        except Exception:
            # leave as is; creating table with fully qualified name
            pass
        self.session.execute(SimpleStatement(cql))


class ColumnFamily:
    """Minimal ColumnFamily API backed by a single map<text, blob> column.

    Methods implemented: multiget, multiget_slice (columns filter), get,
    insert, remove, xget.
    """
    def __init__(self, pool: ConnectionPool, name: str, **kwargs):
        self.pool = pool
        self.name = name
        self.keyspace = pool.keyspace
        self.table = name
        self.session = pool.session
        # ensure table exists
        cql = (
            "CREATE TABLE IF NOT EXISTS %s.%s (\n"
            "  key text PRIMARY KEY,\n"
            "  columns map<text, blob>\n"
            ")" % (self.keyspace, self.table)
        )
        try:
            self.session.execute(SimpleStatement(cql))
        except Exception:
            # if keyspace doesn't exist, caller should create it first
            pass

    def _deserialize_map(self, raw_map: Dict[bytes, bytes]) -> OrderedDict:
        if not raw_map:
            return OrderedDict()
        od = OrderedDict()
        for k, v in raw_map.items():
            try:
                val = pickle.loads(v) if v is not None else None
            except Exception:
                val = v
            od[str(k)] = val
        return od

    def multiget(self, keys: Iterable[str], columns: Optional[Iterable[str]] = None, column_count: Optional[int] = None):
        keys = list(keys)
        if not keys:
            return {}
        placeholders = ','.join(["%s"] * len(keys))
        cql = "SELECT key, columns FROM %s.%s WHERE key IN (%s)" % (self.keyspace, self.table, placeholders)
        rows = self.session.execute(cql, tuple(keys))
        ret = {}
        for row in rows:
            raw = row.columns if hasattr(row, 'columns') else row[1]
            od = self._deserialize_map(raw)
            if columns is not None:
                od = OrderedDict((k, od[k]) for k in columns if k in od)
            if column_count is not None and len(od) > column_count:
                # truncate (preserve insertion order)
                reduced = OrderedDict()
                for i, (k, v) in enumerate(od.items()):
                    if i >= column_count:
                        break
                    reduced[k] = v
                od = reduced
            ret[str(row.key)] = od
        return ret

    def get(self, key: str, columns: Optional[Iterable[str]] = None):
        cql = "SELECT columns FROM %s.%s WHERE key = %%s" % (self.keyspace, self.table)
        row = self.session.execute(cql, (key,)).one()
        if not row:
            raise NotFoundException()
        raw = row.columns if hasattr(row, 'columns') else row[0]
        od = self._deserialize_map(raw)
        if columns is not None:
            od = OrderedDict((k, od[k]) for k in columns if k in od)
        return od

    def insert(self, key: str, columns: Dict[str, object], ttl: Optional[int] = None):
        # serialize values
        ser = {k: pickle.dumps(v) for k, v in columns.items()}
        if ttl:
            cql = "UPDATE %s.%s USING TTL %d SET columns = columns + %%s WHERE key = %%s" % (self.keyspace, self.table, ttl)
            self.session.execute(cql, (ser, key))
        else:
            cql = "UPDATE %s.%s SET columns = columns + %%s WHERE key = %%s" % (self.keyspace, self.table)
            self.session.execute(cql, (ser, key))

    def remove(self, key: str, columns: Optional[Iterable[str]] = None):
        if columns is None:
            cql = "DELETE FROM %s.%s WHERE key = %%s" % (self.keyspace, self.table)
            self.session.execute(cql, (key,))
        else:
            # remove specific entries from the map by setting them to null via delete
            for col in columns:
                cql = "DELETE columns[%%s] FROM %s.%s WHERE key = %%s" % (self.keyspace, self.table)
                self.session.execute(cql, (col, key))

    def xget(self, key: str, column_start: Optional[str] = None, buffer_size: Optional[int] = None):
        # approximate xget by returning columns after column_start
        od = self.get(key)
        if column_start is None:
            return od
        items = list(od.items())
        res = OrderedDict()
        found = False
        for k, v in items:
            if not found:
                if k == column_start:
                    found = True
                    continue
                else:
                    continue
            res[k] = v
            if buffer_size and len(res) >= buffer_size:
                break
        return res

    # convenience wrapper for older multiget usages with columns kw
    def multiget_slice(self, keys, columns=None):
        return self.multiget(keys, columns=columns)

    def get_count(self, key: str):
        od = self.get(key)
        return len(od)


class Mutator:
    """Batch mutator backed by DataStax driver's BatchStatement.

    This implements a small subset of the pycassa Mutator API used by r2:
    - context manager usage (`with Mutator(pool) as m:`)
    - `insert(cf, key, columns, ttl=None)`
    - `remove(cf, key, columns=None, timestamp=None)`
    - `send()` commits the batch

    The implementation translates the legacy map-based CF operations to CQL
    and executes them as a single BatchStatement against the session.
    """

    def __init__(self, pool_or_session):
        # accept either a ConnectionPool or a Session
        if hasattr(pool_or_session, 'session'):
            self.session = pool_or_session.session
        else:
            self.session = pool_or_session
        self._ops = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.send()
        except Exception:
            # don't raise during cleanup
            return False

    def insert(self, cf, key, columns, ttl=None):
        # columns expected to be a dict of name->value (already serialized by callers)
        # We'll serialize here using pickle to match ColumnFamily.insert behaviour
        ser = {k: pickle.dumps(v) for k, v in columns.items()}
        if ttl:
            cql = "UPDATE %s.%s USING TTL %d SET columns = columns + %%s WHERE key = %%s" % (cf.keyspace, cf.table, int(ttl))
            params = (ser, key)
        else:
            cql = "UPDATE %s.%s SET columns = columns + %%s WHERE key = %%s" % (cf.keyspace, cf.table)
            params = (ser, key)
        self._ops.append(("insert", cql, params))

    def remove(self, cf, key, columns=None, timestamp=None):
        if columns is None:
            cql = "DELETE FROM %s.%s WHERE key = %%s" % (cf.keyspace, cf.table)
            params = (key,)
            self._ops.append(("delete_row", cql, params))
        else:
            # delete each map entry
            for col in columns:
                cql = "DELETE columns[%%s] FROM %s.%s WHERE key = %%s" % (cf.keyspace, cf.table)
                params = (col, key)
                self._ops.append(("delete_col", cql, params))

    def send(self):
        if not self._ops:
            return
        batch = BatchStatement(batch_type=BatchType.UNLOGGED)
        # add statements to the batch
        for kind, cql, params in self._ops:
            stmt = SimpleStatement(cql)
            batch.add(stmt, params)
        # execute the batch
        self.session.execute(batch)
        self._ops = []
