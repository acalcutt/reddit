"""Minimal events module used by tests.

`r2` expects `baseplate.events.EventQueue` to be assignable; provide a
placeholder so tests can set it to `queue.Queue` during setup.
"""

EventQueue = None
