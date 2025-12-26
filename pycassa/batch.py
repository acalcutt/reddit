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
    """Record mutations and noop on send.

    Usage in r2 expects: `with Mutator(pool) as m:` and calls to
    `m.insert(cf, key, columns, ttl=...)` and `m.remove(cf, key, ...)`.
    """

    def __init__(self, pool_or_cf):
        # store reference for potential adapters; do not touch it here
        self.pool_or_cf = pool_or_cf
        self._ops = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # on context exit, attempt to send mutations
        try:
            self.send()
        except Exception:
            LOG.exception('Mutator.send() failed in __exit__')

    def insert(self, cf, key, columns, ttl=None):
        # record the intent; columns is expected to be a dict of name->value
        self._ops.append(('insert', cf, key, columns, ttl))

    def remove(self, cf, key, columns=None, timestamp=None):
        # record the removal intent
        self._ops.append(('remove', cf, key, columns, timestamp))

    def send(self):
        """Commit recorded mutations.

        This shim does not perform any network IO. If a real connection
        object is present on the provided pool/columnfamily, try to call
        its batch API; otherwise just clear recorded ops.
        """
        # Best-effort attempt to apply to a real ColumnFamily object.
        for op in self._ops:
            kind, cf, key, payload, opt = op
            try:
                # If the cf argument exposes an `insert`/`remove` method,
                # call it directly for tests that provide a fake CF.
                if hasattr(cf, 'insert') and hasattr(cf, 'remove'):
                    if kind == 'insert':
                        cf.insert(key, payload)
                    else:
                        # remove may expect different args; try best-effort
                        if payload is None and opt is None:
                            cf.remove(key)
                        else:
                            cf.remove(key, columns=payload)
            except Exception:
                # swallow: this shim is for tests
                LOG.debug('pycassa.batch.Mutator: best-effort apply failed', exc_info=True)

        # Clear the ops regardless
        self._ops = []
