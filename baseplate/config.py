"""Minimal baseplate.config shim used by r2 config parsing.
"""

def Optional(inner=None):
    """Return a parser that accepts empty values as None and otherwise
    delegates to `inner`.
    """
    def parser(v):
        if v is None or v == '':
            return None
        if callable(inner):
            return inner(v)
        return v
    return parser


def Endpoint(v):
    """Parse an endpoint string. For tests a simple identity parser is
    sufficient (return the string).
    """
    return str(v)
