"""
Rate-limiting helpers.

The shared `limiter` instance lives in `extensions.py` to avoid circular
imports.  Import it from there directly::

    from extensions import limiter

This file remains as a convenience for any extra helper utilities.
"""

from extensions import limiter  # noqa: F401 — re-export for backward compat
