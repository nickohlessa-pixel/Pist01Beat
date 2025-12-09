"""
Pist01 Beat v3.4 package initializer.

This module exposes the Pist01Beat wrapper from pist01beat.model
without making any assumptions about engine internals.

Rules:
- No engine imports here.
- No heavy logic here.
- Only lazy access to Pist01Beat so we avoid circular imports or stale states.
"""

from importlib import import_module

__all__ = ["Pist01Beat"]


def __getattr__(name):
    """
    Lazy attribute resolver so that:

        from pist01beat import Pist01Beat

    grabs Pist01Beat from pist01beat.model at access time.
    """
    if name == "Pist01Beat":
        module = import_module(".model", __name__)
        return getattr(module, "Pist01Beat")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
