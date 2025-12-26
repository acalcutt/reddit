# Lightweight shim for cassandra driver used in tests when the real
# `cassandra` package is not installed. This provides minimal interfaces
# expected by the code (Cluster, NoHostAvailable) so unit tests that mock
# higher-level DB interactions can import successfully.
from .cluster import Cluster, NoHostAvailable
from .query import SimpleStatement, BatchStatement, BatchType

# Minimal exceptions/aliases expected by imported modules
class InvalidRequest(Exception):
	pass

__all__ = [
	"Cluster",
	"NoHostAvailable",
	"SimpleStatement",
	"BatchStatement",
	"BatchType",
	"InvalidRequest",
]
