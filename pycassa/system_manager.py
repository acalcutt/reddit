"""Minimal subset of pycassa.system_manager used by r2.
Provides type constants and a SystemManager wrapper that delegates to
`r2.lib.db.cassandra_compat.SystemManager`.
"""
from r2.lib.db.cassandra_compat import SystemManager as _SystemManager

# Type placeholders (these are not used programmatically in our compat layer,
# but some modules import them as metadata). Using simple strings/objects
# allows the application to continue referencing these names.
ASCII_TYPE = 'AsciiType'
UTF8_TYPE = 'UTF8Type'
TIME_UUID_TYPE = 'TimeUUIDType'
DATE_TYPE = 'DateType'
INT_TYPE = 'IntType'
DOUBLE_TYPE = 'DoubleType'
FLOAT_TYPE = 'FloatType'
LONG_TYPE = 'LongType'

# Expose the SystemManager API
class SystemManager(_SystemManager):
    pass
