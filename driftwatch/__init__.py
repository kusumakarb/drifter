"""
DriftWatch - Automated Data Drift Detection Framework

A modular, extensible framework for detecting schema and data drift
in datasets.
"""

__version__ = "0.1.0"
__author__ = "Kusumakar"

from driftwatch.core.config import DriftWatchConfig
from driftwatch.core.expectation_suite_builder import ExpectationSuiteBuilder
from driftwatch.core.gx_context import DriftWatchGXContext
from driftwatch.core.validation_result_enricher import ValidationResultEnricher

__all__ = [
    "DriftWatchConfig",
    "DriftWatchGXContext",
    "ExpectationSuiteBuilder",
    "ValidationResultEnricher",
]
