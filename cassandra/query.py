class SimpleStatement:
    def __init__(self, *a, **kw):
        pass

class BatchStatement:
    def __init__(self, *a, **kw):
        pass

class BatchType:
    LOGGED = 0
    UNLOGGED = 1
    COUNTER = 2

__all__ = ["SimpleStatement", "BatchStatement", "BatchType"]
