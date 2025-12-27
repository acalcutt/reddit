"""Minimal pycassa.batch compatibility shim.

Provides a `Mutator` class with the subset of the pycassa API used by
the r2 codebase: context manager support, `insert`, `remove`, and `send`.

This shim is intentionally a no-op/batching recorder so tests can run
without a live Cassandra cluster.  Production environments should use
the real `pycassa` package.
"""
from contextlib import contextmanager
import logging

LOG = logging.getLogger(__name__)


class Mutator:
    """Record mutations and translate to a backend mutator when available.

    If `r2.lib.db.cassandra_compat.Mutator` exists, delegate to it. Otherwise
    fall back to a best-effort apply where `cf.insert` / `cf.remove` are
    invoked (this works with the `ColumnFamily` in `r2.lib.db.cassandra_compat`).
    """

    def __init__(self, pool_or_cf):
        # try to use a dedicated compat Mutator if provided
        self._backend = None
        try:
            from r2.lib.db import cassandra_compat as cc
            if hasattr(cc, 'Mutator'):
                self._backend = cc.Mutator(pool_or_cf)
        except Exception:
            self._backend = None

        self.pool_or_cf = pool_or_cf
        self._ops = []

    def __enter__(self):
        if self._backend is not None and hasattr(self._backend, '__enter__'):
            return self._backend.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._backend is not None and hasattr(self._backend, '__exit__'):
            return self._backend.__exit__(exc_type, exc, tb)
        try:
            self.send()
        except Exception:
            LOG.exception('Mutator.send() failed in __exit__')

    def insert(self, cf, key, columns, ttl=None):
        if self._backend is not None and hasattr(self._backend, 'insert'):
            return self._backend.insert(cf, key, columns, ttl=ttl)
        self._ops.append(('insert', cf, key, columns, ttl))

    def remove(self, cf, key, columns=None, timestamp=None):
        if self._backend is not None and hasattr(self._backend, 'remove'):
            return self._backend.remove(cf, key, columns=columns, timestamp=timestamp)
        self._ops.append(('remove', cf, key, columns, timestamp))

    def send(self):
        if self._backend is not None and hasattr(self._backend, 'send'):
            return self._backend.send()

        # Best-effort: apply to ColumnFamily-like objects
        for op in self._ops:
            kind, cf, key, payload, opt = op
            try:
                if hasattr(cf, 'insert') and hasattr(cf, 'remove'):
                    if kind == 'insert':
                        cf.insert(key, payload, ttl=opt) if opt else cf.insert(key, payload)
                    else:
                        if payload is None and opt is None:
                            cf.remove(key)
                        else:
                            # try remove with columns list
                            cf.remove(key, columns=payload)
            except Exception:
                LOG.debug('pycassa.batch.Mutator: best-effort apply failed', exc_info=True)

        self._ops = []
