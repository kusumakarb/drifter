"""
Custom Great Expectations expectation for decimal precision validation.

This expectation validates that numeric values in a column have a specific
number of decimal places, which is critical for GPS coordinates and other
high-precision data.

Based on the ChatGPT recommendation for production-grade GX usage.
"""

import logging
import re
from typing import ClassVar, Optional

import pydantic
from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import (
    ColumnMapMetricProvider,
    column_condition_partial,
)

logger = logging.getLogger(__name__)


class ColumnValuesHaveDecimalPrecision(ColumnMapMetricProvider):
    """
    Metric provider that checks if column values have exact decimal precision.

    This is the internal metric that powers the expectation.
    """

    condition_metric_name = "column_values.have_decimal_precision"

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(self, column, precision=6, **kwargs):
        """
        Check if values match decimal precision pattern.

        Args:
            column: Pandas Series
            precision: Required number of decimal places
            **kwargs: Additional arguments

        Returns:
            Boolean Series indicating which values match the precision
        """
        # Pattern matches: optional minus, digits, decimal point, exactly N digits
        pattern = re.compile(rf"^-?\d+(\.\d{{{precision}}})$")
        return column.astype(str).str.match(pattern)


class ExpectColumnValuesToHaveDecimalPrecision(ColumnMapExpectation):
    """
    Expect column values to have a fixed number of decimal places.

    This expectation is critical for validating GPS coordinates where precision
    directly impacts accuracy:
    - 6 decimal places = ~0.11 meter precision (required for delivery locations)
    - 4 decimal places = ~11 meter precision
    - 2 decimal places = ~1.1 kilometer precision

    Example usage:
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="latitude",
                precision=6,
                mostly=0.999
            )
        )

    Args:
        column (str): The column name to check
        precision (int): Required number of decimal places (default: 6)
        mostly (float): Percentage of values that must meet the expectation (default: 1.0)

    Returns:
        ExpectationValidationResult with success status and details
    """

    map_metric: ClassVar[str] = "column_values.have_decimal_precision"

    # Args keys - positional arguments
    args_keys: ClassVar[tuple[str, ...]] = ("column",)

    # Success keys - parameters that affect pass/fail
    success_keys: ClassVar[tuple[str, ...]] = ("precision", "mostly")

    precision: int = pydantic.Field(
        default=6,
        description="Required number of decimal places (e.g., 6 for GPS coordinates)"
    )

    # Default values for other parameters
    default_kwarg_values = {
        "mostly": 1.0,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
    }

    # Library metadata
    library_metadata = {
        "maturity": "production",
        "tags": ["data_quality", "gps", "precision"],
        "contributors": ["@driftwatch"],
    }

    def validate_configuration(
        self, configuration: Optional["ExpectationConfiguration"] = None
    ) -> bool:
        """
        Validate the expectation configuration.

        Args:
            configuration: The expectation configuration to validate

        Returns:
            True if valid, raises ValueError otherwise

        Raises:
            ValueError: If precision is not a positive integer
        """
        super().validate_configuration(configuration)

        if configuration is None:
            configuration = self.configuration

        precision = configuration.kwargs.get("precision")
        if precision is not None and (not isinstance(precision, int) or precision <= 0):
            raise ValueError("precision must be a positive integer")

        return True

    @classmethod
    def _prescriptive_template(
        cls,
        renderer_configuration,
    ):
        """
        Template for rendering the expectation in documentation.

        This makes the expectation show up nicely in data docs.
        """
        add_param_args = [
            ("column", "column"),
            ("precision", "precision"),
            ("mostly", "mostly"),
        ]
        for param_name, param_key in add_param_args:
            renderer_configuration = renderer_configuration.add_param(
                param_name, param_key
            )

        template_str = (
            "Values in $column must have exactly $precision decimal places"
        )

        if renderer_configuration.include_column_name:
            template_str = f"$column : {template_str}"

        if renderer_configuration.mostly:
            template_str += ", at least $mostly % of the time."
        else:
            template_str += "."

        renderer_configuration.template_str = template_str

        return renderer_configuration
