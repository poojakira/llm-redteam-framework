"""llm-redteam-framework.

Offline adversarial-prompt generation and detection.

Sub-packages
------------
- :mod:`redteam.generators` -- adversarial-prompt mutation generators.
- :mod:`redteam.detector`   -- TF-IDF (char n-gram) + LogisticRegression detector.
- :mod:`redteam.eval`       -- held-out evaluation harness with a JSON report.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
