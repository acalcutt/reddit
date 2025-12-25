"""Minimal baseplate.config shim used by r2 config parsing.
"""

class Optional:
    def __init__(self, inner=None):
        self.inner = inner


class Endpoint:
    pass
