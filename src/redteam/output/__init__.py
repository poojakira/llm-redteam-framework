"""
src/redteam/output/__init__.py
──────────────────────────────────────────────────────────────────────────────
Public API for the output sub-package.

Exports
-------
findings_to_sarif            — Convert findings list to SARIF 2.1.0 document
sarif_has_high_or_critical   — Return True if SARIF doc has any error-level result
"""
from __future__ import annotations

from redteam.output.sarif import findings_to_sarif, sarif_has_high_or_critical

__all__ = [
    "findings_to_sarif",
    "sarif_has_high_or_critical",
]
