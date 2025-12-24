# Local pycassa compatibility shim for the r2 codebase.
# This module provides a tiny subset of pycassa's public API by
# delegating to r2.lib.db.cassandra_compat where appropriate.
from .system_manager import *
from .pool import *
from .types import *
from .util import *
