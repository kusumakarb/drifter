"""
Custom Great Expectations expectation for categorical distribution drift detection.

This expectation validates that categorical column distributions remain stable
using Population Stability Index (PSI), an industry-standard metric for
detecting distribution shifts.
"""

import logging
from typing import ClassVar, Optional

import numpy as np
import pydantic
from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.expectation import ColumnAggregateExpectation
from great_expectations.expectations.metrics import (
    ColumnAggregateMetricProvider,
    column_aggregate_value,
)

logger = logging.getLogger(__name__)


class ColumnCategoricalDistributionPSI(ColumnAggregateMetricProvider):
    """
    Metric provider that calculates PSI between observed and reference distributions.

    Population Stability Index (PSI) measures distribution shift:
    - PSI < 0.1: No significant change
    - 0.1 <= PSI < 0.2: Small change
    - 0.2 <= PSI < 0.25: Major change
    - PSI >= 0.25: Critical change (significant drift)
    """

    metric_name = "column.categorical_distribution_psi"
    value_keys = ("reference_distribution",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(self, column, reference_distribution, **kwargs):
        """
        Calculate PSI between observed distribution and reference (Pandas).

        Args:
            column: Pandas Series (observed data)
            reference_distribution: Dict of category -> proportion from reference
            **kwargs: Additional arguments

        Returns:
            PSI value (float)
        """
        # Calculate observed proportions
        observed_counts = column.value_counts()
        total = len(column)

        if total == 0:
            logger.warning("Empty column, returning PSI = 0.0")
            return 0.0

        observed_props = {str(k): v / total for k, v in observed_counts.items()}

        # Get all categories (union of reference and observed)
        all_categories = set(reference_distribution.keys()) | set(observed_props.keys())

        # Calculate PSI
        psi = 0.0
        for category in all_categories:
            # Use small epsilon to avoid division by zero
            ref_p = reference_distribution.get(category, 0.0001)
            obs_p = observed_props.get(category, 0.0001)

            # PSI formula: sum((obs - ref) * ln(obs / ref))
            psi += (obs_p - ref_p) * np.log(obs_p / ref_p)

        return float(psi)


class ExpectColumnCategoriesToMatchDistribution(ColumnAggregateExpectation):
    """
    Expect categorical column distribution to match reference using PSI.

    This expectation detects significant distribution shifts in categorical columns
    using Population Stability Index (PSI), an industry-standard metric used in
    banking, credit scoring, and ML model monitoring.

    PSI measures how much the observed distribution differs from the reference:
    - PSI < 0.1: No drift (distributions are stable)
    - 0.1 <= PSI < 0.2: Minor drift (small change, monitor)
    - 0.2 <= PSI < 0.25: Major drift (significant change, investigate)
    - PSI >= 0.25: Critical drift (distribution shift, action required)

    Example usage:
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="Road_traffic_density",
                reference_distribution={
                    "Jam": 0.314,
                    "Low": 0.344,
                    "Medium": 0.243,
                    "High": 0.098
                },
                psi_threshold=0.25
            )
        )

    Real-world example (food delivery):
        Reference distribution:
            Jam: 31.4%, Low: 34.4%, Medium: 24.3%, High: 9.8%
        Drifted distribution:
            Jam: 89.9%, Low: 10.1%, Medium: 0%, High: 0%

        PSI = 3.48 (far exceeds 0.25 critical threshold) → DRIFT DETECTED

    Args:
        column (str): The column name to check
        reference_distribution (dict): Reference category proportions {category: proportion}
        psi_threshold (float): Maximum allowed PSI value (default: 0.25 for critical)

    Returns:
        ExpectationValidationResult with success status and PSI details
    """

    metric_dependencies = ("column.categorical_distribution_psi",)

    # Args keys - positional arguments
    args_keys: ClassVar[tuple[str, ...]] = ("column",)

    # Success keys - parameters that affect pass/fail
    success_keys: ClassVar[tuple[str, ...]] = ("reference_distribution", "psi_threshold")

    reference_distribution: dict[str, float] = pydantic.Field(
        description="Reference category proportions as {category: proportion}"
    )

    psi_threshold: float = pydantic.Field(
        default=0.25,
        description="Maximum allowed PSI value (critical threshold)"
    )

    # Default values for other parameters
    default_kwarg_values = {
        "psi_threshold": 0.25,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
    }

    # Library metadata
    library_metadata = {
        "maturity": "production",
        "tags": ["data_quality", "categorical", "distribution", "psi"],
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
            ValueError: If reference_distribution is invalid or psi_threshold is negative
        """
        super().validate_configuration(configuration)

        if configuration is None:
            configuration = self.configuration

        # Validate reference_distribution
        ref_dist = configuration.kwargs.get("reference_distribution")
        if not isinstance(ref_dist, dict):
            raise ValueError("reference_distribution must be a dictionary")

        if not ref_dist:
            raise ValueError("reference_distribution cannot be empty")

        # Check that proportions sum to approximately 1.0
        total = sum(ref_dist.values())
        if not (0.99 <= total <= 1.01):
            logger.warning(
                f"reference_distribution proportions sum to {total}, not 1.0. "
                "This may indicate an error in the reference data."
            )

        # Validate psi_threshold
        psi_threshold = configuration.kwargs.get("psi_threshold")
        if psi_threshold is not None:
            if not isinstance(psi_threshold, (int, float)) or psi_threshold < 0:
                raise ValueError("psi_threshold must be a non-negative number")

        return True

    def _validate(
        self,
        metrics: dict,
        runtime_configuration: dict | None = None,
        execution_engine: PandasExecutionEngine | None = None,
    ):
        """
        Validate PSI against threshold.

        Args:
            metrics: Computed metrics including PSI
            runtime_configuration: Runtime configuration
            execution_engine: Execution engine

        Returns:
            Dict with success status and PSI details
        """
        # Get computed PSI from metrics
        observed_psi = metrics.get("column.categorical_distribution_psi")

        # Get configuration parameters
        psi_threshold = self.psi_threshold
        reference_distribution = self.reference_distribution

        # Determine success
        success = observed_psi <= psi_threshold

        # Classify severity based on PSI value
        if observed_psi < 0.1:
            severity = "NONE"
            severity_description = "No drift detected"
        elif observed_psi < 0.2:
            severity = "MINOR"
            severity_description = "Minor drift detected"
        elif observed_psi < 0.25:
            severity = "MAJOR"
            severity_description = "Major drift detected"
        else:
            severity = "CRITICAL"
            severity_description = "Critical drift detected"

        return {
            "success": success,
            "result": {
                "observed_value": observed_psi,
                "element_count": None,  # Not applicable for aggregate metrics
                "missing_count": None,
                "missing_percent": None,
                "details": {
                    "observed_psi": observed_psi,
                    "threshold": psi_threshold,
                    "severity": severity,
                    "severity_description": severity_description,
                    "reference_distribution": reference_distribution,
                }
            }
        }

    @classmethod
    def _prescriptive_template(
        cls,
        renderer_configuration,
    ):
        """
        Template for rendering the expectation in documentation.

        This makes the expectation show up nicely in Data Docs.
        """
        add_param_args = [
            ("column", "column"),
            ("psi_threshold", "psi_threshold"),
        ]
        for param_name, param_key in add_param_args:
            renderer_configuration = renderer_configuration.add_param(
                param_name, param_key
            )

        template_str = (
            "Categorical distribution in $column must have PSI <= $psi_threshold "
            "compared to reference distribution"
        )

        if renderer_configuration.include_column_name:
            template_str = f"$column : {template_str}"

        template_str += "."

        renderer_configuration.template_str = template_str

        return renderer_configuration
