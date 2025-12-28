"""
Minimal Thrift-style stub module for BaseplateService.

This provides lightweight `Iface` and `Client` classes so code that
imports `baseplate.thrift.BaseplateService` can run without full
Thrift-generated sources. It should be replaced with the proper
generated module for full functionality.
"""

class Iface:
    """BaseplateService interface stub."""

    def ping(self):
        """Example method placeholder."""
        pass


class Client(Iface):
    """Client stub for BaseplateService."""

    def __init__(self, iprot, oprot=None):
        self._iprot = iprot
        self._oprot = oprot if oprot is not None else iprot


class Processor:
    """Processor stub placeholder."""

    def __init__(self, iface):
        self.iface = iface


__all__ = ["Iface", "Client", "Processor"]
