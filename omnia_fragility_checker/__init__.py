"""OMNIA Fragility Checker.

Structural Fragility Bridge for measuring stability under equivalent variants.

Boundary:
measurement != inference != decision
"""

__version__ = "0.2.0"

from .classifier import (
    SEVERITY_ORDER,
    classify_pair,
    classify_case,
    classify_records,
)

__all__ = [
    "SEVERITY_ORDER",
    "classify_pair",
    "classify_case",
    "classify_records",
]
