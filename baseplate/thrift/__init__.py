"""
Minimal package to hold Thrift-generated stubs for baseplate.

This package provides a small set of files so runtime imports like
`import baseplate.thrift.BaseplateService` succeed even when the
Thrift-generated sources are not present.
"""

__all__ = ["BaseplateService"]
