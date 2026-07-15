"""Held-out evaluation harness exports with lazy imports."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .harness import EvalReport, evaluate, main

__all__ = ["EvalReport", "evaluate", "main"]


def __getattr__(name: str):
    if name in __all__:
        from . import harness

        return getattr(harness, name)
    raise AttributeError(name)
