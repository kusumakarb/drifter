"""Custom Great Expectations expectations for DriftWatch.

Custom expectations are automatically discovered on import.
Simply importing this module makes all custom expectations available.
"""

import logging

from .expect_column_categories_to_match_distribution import (
    ColumnCategoricalDistributionPSI,  # Metric provider
    ExpectColumnCategoriesToMatchDistribution,
)
from .expect_column_values_to_have_decimal_precision import (
    ColumnValuesHaveDecimalPrecision,  # Metric provider
    ExpectColumnValuesToHaveDecimalPrecision,
)

logger = logging.getLogger(__name__)


def register_custom_expectations():
    """
    Initialize custom expectations for Great Expectations.

    Expectations are automatically discovered on import.
    This function exists for backwards compatibility but doesn't need to do anything
    special - simply importing the expectation classes is sufficient.

    The custom expectations become available for use in expectation suites:
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(...)
        )

    Note: This is called automatically when you import from driftwatch.detectors
    """
    logger.debug("Custom expectations initialized")


__all__ = [
    "ColumnCategoricalDistributionPSI",
    "ColumnValuesHaveDecimalPrecision",
    "ExpectColumnCategoriesToMatchDistribution",
    "ExpectColumnValuesToHaveDecimalPrecision",
    "register_custom_expectations",
]
