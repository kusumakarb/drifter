"""Expectation registry with unified class and parameter mapping.

Provides a single source of truth for all supported Great Expectations expectation classes
and their parameters. Replaces the previous two-dict approach (class registry + pattern matching)
with a unified registry for better accuracy and maintainability.
"""

import logging

from great_expectations.expectations import (
    # Column values - set membership
    ExpectColumnDistinctValuesToBeInSet,
    ExpectColumnDistinctValuesToContainSet,
    ExpectColumnDistinctValuesToEqualSet,
    # Column aggregate
    ExpectColumnKLDivergenceToBeLessThan,
    ExpectColumnMaxToBeBetween,
    ExpectColumnMeanToBeBetween,
    ExpectColumnMedianToBeBetween,
    ExpectColumnMinToBeBetween,
    ExpectColumnMostCommonValueToBeInSet,
    # Column pair
    ExpectColumnPairValuesAToBeGreaterThanB,
    ExpectColumnPairValuesToBeEqual,
    ExpectColumnPairValuesToBeInSet,
    ExpectColumnProportionOfNonNullValuesToBeBetween,
    ExpectColumnProportionOfUniqueValuesToBeBetween,
    ExpectColumnQuantileValuesToBeBetween,
    ExpectColumnStdevToBeBetween,
    ExpectColumnSumToBeBetween,
    # Column existence
    ExpectColumnToExist,
    ExpectColumnUniqueValueCountToBeBetween,
    ExpectColumnValueLengthsToBeBetween,
    # Column values - string length
    ExpectColumnValueLengthsToEqual,
    # Column values - range
    ExpectColumnValuesToBeBetween,
    # Column values - datetime
    ExpectColumnValuesToBeDateutilParseable,
    # Column values - ordering
    ExpectColumnValuesToBeDecreasing,
    ExpectColumnValuesToBeIncreasing,
    ExpectColumnValuesToBeInSet,
    # Column values - type
    ExpectColumnValuesToBeInTypeList,
    # Column values - JSON
    ExpectColumnValuesToBeJsonParseable,
    # Column values - null
    ExpectColumnValuesToBeNull,
    ExpectColumnValuesToBeOfType,
    # Column values - uniqueness
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToMatchJsonSchema,
    # Column values - regex/pattern
    ExpectColumnValuesToMatchLikePattern,
    ExpectColumnValuesToMatchLikePatternList,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnValuesToMatchRegexList,
    ExpectColumnValuesToMatchStrftimeFormat,
    ExpectColumnValuesToNotBeInSet,
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToNotMatchLikePattern,
    ExpectColumnValuesToNotMatchLikePatternList,
    ExpectColumnValuesToNotMatchRegex,
    ExpectColumnValuesToNotMatchRegexList,
    # Column values - statistical
    ExpectColumnValueZScoresToBeLessThan,
    # Multi-column
    ExpectCompoundColumnsToBeUnique,
    ExpectMulticolumnSumToEqual,
    ExpectMulticolumnValuesToBeUnique,
    # Query
    ExpectQueryResultsToMatchComparison,
    ExpectSelectColumnValuesToBeUniqueWithinRecord,
    # Table
    ExpectTableColumnCountToBeBetween,
    ExpectTableColumnCountToEqual,
    ExpectTableColumnsToMatchOrderedList,
    ExpectTableColumnsToMatchSet,
    ExpectTableRowCountToBeBetween,
    ExpectTableRowCountToEqual,
    ExpectTableRowCountToEqualOtherTable,
)

from driftwatch.expectations import (
    ExpectColumnCategoriesToMatchDistribution,
    ExpectColumnValuesToHaveDecimalPrecision,
)

logger = logging.getLogger(__name__)


# Module-level registry mapping expectation names to classes and parameters
EXPECTATION_REGISTRY = {
    # Column existence
    "ExpectColumnToExist": {"class": ExpectColumnToExist, "params": []},
    # Column aggregate expectations (statistical)
    "ExpectColumnMinToBeBetween": {
        "class": ExpectColumnMinToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    "ExpectColumnMaxToBeBetween": {
        "class": ExpectColumnMaxToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    "ExpectColumnMeanToBeBetween": {
        "class": ExpectColumnMeanToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    "ExpectColumnMedianToBeBetween": {
        "class": ExpectColumnMedianToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    "ExpectColumnStdevToBeBetween": {
        "class": ExpectColumnStdevToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    "ExpectColumnSumToBeBetween": {
        "class": ExpectColumnSumToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    "ExpectColumnQuantileValuesToBeBetween": {
        "class": ExpectColumnQuantileValuesToBeBetween,
        "params": ["quantile_ranges", "mostly"],
    },
    # Column uniqueness/cardinality
    "ExpectColumnUniqueValueCountToBeBetween": {
        "class": ExpectColumnUniqueValueCountToBeBetween,
        "params": ["min_value", "max_value"],
    },
    "ExpectColumnProportionOfUniqueValuesToBeBetween": {
        "class": ExpectColumnProportionOfUniqueValuesToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max"],
    },
    "ExpectColumnMostCommonValueToBeInSet": {
        "class": ExpectColumnMostCommonValueToBeInSet,
        "params": ["value_set", "ties_okay"],
    },
    # Column values - set membership
    "ExpectColumnValuesToBeInSet": {
        "class": ExpectColumnValuesToBeInSet,
        "params": ["value_set", "mostly"],
    },
    "ExpectColumnValuesToNotBeInSet": {
        "class": ExpectColumnValuesToNotBeInSet,
        "params": ["value_set", "mostly"],
    },
    "ExpectColumnDistinctValuesToBeInSet": {
        "class": ExpectColumnDistinctValuesToBeInSet,
        "params": ["value_set"],
    },
    "ExpectColumnDistinctValuesToContainSet": {
        "class": ExpectColumnDistinctValuesToContainSet,
        "params": ["value_set"],
    },
    "ExpectColumnDistinctValuesToEqualSet": {
        "class": ExpectColumnDistinctValuesToEqualSet,
        "params": ["value_set"],
    },
    # Column values - range
    "ExpectColumnValuesToBeBetween": {
        "class": ExpectColumnValuesToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max", "mostly"],
    },
    # Column values - null
    "ExpectColumnValuesToBeNull": {
        "class": ExpectColumnValuesToBeNull,
        "params": ["mostly"],
    },
    "ExpectColumnValuesToNotBeNull": {
        "class": ExpectColumnValuesToNotBeNull,
        "params": ["mostly"],
    },
    "ExpectColumnProportionOfNonNullValuesToBeBetween": {
        "class": ExpectColumnProportionOfNonNullValuesToBeBetween,
        "params": ["min_value", "max_value", "strict_min", "strict_max"],
    },
    # Column values - uniqueness
    "ExpectColumnValuesToBeUnique": {
        "class": ExpectColumnValuesToBeUnique,
        "params": ["mostly"],
    },
    # Column values - ordering
    "ExpectColumnValuesToBeIncreasing": {
        "class": ExpectColumnValuesToBeIncreasing,
        "params": ["strictly", "mostly"],
    },
    "ExpectColumnValuesToBeDecreasing": {
        "class": ExpectColumnValuesToBeDecreasing,
        "params": ["strictly", "mostly"],
    },
    # Column values - type
    "ExpectColumnValuesToBeOfType": {
        "class": ExpectColumnValuesToBeOfType,
        "params": ["type_", "mostly"],
    },
    "ExpectColumnValuesToBeInTypeList": {
        "class": ExpectColumnValuesToBeInTypeList,
        "params": ["type_list", "mostly"],
    },
    # Column values - string length
    "ExpectColumnValueLengthsToBeBetween": {
        "class": ExpectColumnValueLengthsToBeBetween,
        "params": ["min_value", "max_value", "mostly"],
    },
    "ExpectColumnValueLengthsToEqual": {
        "class": ExpectColumnValueLengthsToEqual,
        "params": ["value", "mostly"],
    },
    # Column values - regex/pattern
    "ExpectColumnValuesToMatchRegex": {
        "class": ExpectColumnValuesToMatchRegex,
        "params": ["regex", "mostly"],
    },
    "ExpectColumnValuesToNotMatchRegex": {
        "class": ExpectColumnValuesToNotMatchRegex,
        "params": ["regex", "mostly"],
    },
    "ExpectColumnValuesToMatchRegexList": {
        "class": ExpectColumnValuesToMatchRegexList,
        "params": ["regex_list", "mostly"],
    },
    "ExpectColumnValuesToNotMatchRegexList": {
        "class": ExpectColumnValuesToNotMatchRegexList,
        "params": ["regex_list", "mostly"],
    },
    "ExpectColumnValuesToMatchLikePattern": {
        "class": ExpectColumnValuesToMatchLikePattern,
        "params": ["like_pattern", "mostly"],
    },
    "ExpectColumnValuesToNotMatchLikePattern": {
        "class": ExpectColumnValuesToNotMatchLikePattern,
        "params": ["like_pattern", "mostly"],
    },
    "ExpectColumnValuesToMatchLikePatternList": {
        "class": ExpectColumnValuesToMatchLikePatternList,
        "params": ["like_pattern_list", "mostly"],
    },
    "ExpectColumnValuesToNotMatchLikePatternList": {
        "class": ExpectColumnValuesToNotMatchLikePatternList,
        "params": ["like_pattern_list", "mostly"],
    },
    # Column values - datetime
    "ExpectColumnValuesToMatchStrftimeFormat": {
        "class": ExpectColumnValuesToMatchStrftimeFormat,
        "params": ["strftime_format", "mostly"],
    },
    "ExpectColumnValuesToBeDateutilParseable": {
        "class": ExpectColumnValuesToBeDateutilParseable,
        "params": ["mostly"],
    },
    # Column values - JSON
    "ExpectColumnValuesToBeJsonParseable": {
        "class": ExpectColumnValuesToBeJsonParseable,
        "params": ["mostly"],
    },
    "ExpectColumnValuesToMatchJsonSchema": {
        "class": ExpectColumnValuesToMatchJsonSchema,
        "params": ["json_schema", "mostly"],
    },
    # Column values - statistical
    "ExpectColumnValueZScoresToBeLessThan": {
        "class": ExpectColumnValueZScoresToBeLessThan,
        "params": ["threshold", "mostly", "double_sided"],
    },
    "ExpectColumnKLDivergenceToBeLessThan": {
        "class": ExpectColumnKLDivergenceToBeLessThan,
        "params": ["partition_object", "threshold", "tail_weight_holdout"],
    },
    # Column pair expectations
    "ExpectColumnPairValuesAToBeGreaterThanB": {
        "class": ExpectColumnPairValuesAToBeGreaterThanB,
        "params": ["column_A", "column_B", "or_equal", "mostly"],
    },
    "ExpectColumnPairValuesToBeEqual": {
        "class": ExpectColumnPairValuesToBeEqual,
        "params": ["column_A", "column_B", "mostly"],
    },
    "ExpectColumnPairValuesToBeInSet": {
        "class": ExpectColumnPairValuesToBeInSet,
        "params": ["column_A", "column_B", "value_pairs_set", "mostly"],
    },
    # Multi-column expectations
    "ExpectCompoundColumnsToBeUnique": {
        "class": ExpectCompoundColumnsToBeUnique,
        "params": ["column_list", "mostly"],
    },
    "ExpectMulticolumnValuesToBeUnique": {
        "class": ExpectMulticolumnValuesToBeUnique,
        "params": ["column_list", "mostly"],
    },
    "ExpectMulticolumnSumToEqual": {
        "class": ExpectMulticolumnSumToEqual,
        "params": ["column_list", "sum_total", "mostly"],
    },
    "ExpectSelectColumnValuesToBeUniqueWithinRecord": {
        "class": ExpectSelectColumnValuesToBeUniqueWithinRecord,
        "params": ["column_list", "mostly"],
    },
    # Table expectations
    "ExpectTableRowCountToBeBetween": {
        "class": ExpectTableRowCountToBeBetween,
        "params": ["min_value", "max_value"],
    },
    "ExpectTableRowCountToEqual": {
        "class": ExpectTableRowCountToEqual,
        "params": ["value"],
    },
    "ExpectTableRowCountToEqualOtherTable": {
        "class": ExpectTableRowCountToEqualOtherTable,
        "params": ["other_table_name"],
    },
    "ExpectTableColumnCountToBeBetween": {
        "class": ExpectTableColumnCountToBeBetween,
        "params": ["min_value", "max_value"],
    },
    "ExpectTableColumnCountToEqual": {
        "class": ExpectTableColumnCountToEqual,
        "params": ["value"],
    },
    "ExpectTableColumnsToMatchSet": {
        "class": ExpectTableColumnsToMatchSet,
        "params": ["column_set", "exact_match"],
    },
    "ExpectTableColumnsToMatchOrderedList": {
        "class": ExpectTableColumnsToMatchOrderedList,
        "params": ["column_list"],
    },
    # Query expectations
    "ExpectQueryResultsToMatchComparison": {
        "class": ExpectQueryResultsToMatchComparison,
        "params": ["query", "comparison_query", "comparison_type"],
    },
    # Custom DriftWatch expectations
    "ExpectColumnValuesToHaveDecimalPrecision": {
        "class": ExpectColumnValuesToHaveDecimalPrecision,
        "params": ["precision", "mostly"],
    },
    "ExpectColumnCategoriesToMatchDistribution": {
        "class": ExpectColumnCategoriesToMatchDistribution,
        "params": ["reference_distribution", "psi_threshold"],
    },
}


class ExpectationRegistry:
    """Registry for resolving expectation class names to actual Python classes.

    Uses a module-level constant EXPECTATION_REGISTRY for explicit mapping of
    expectation names to classes and parameters. This provides a single source
    of truth with accurate parameter information for all supported expectations.
    """

    def __init__(self):
        """Initialize the registry."""
        logger.info(f"Loaded {len(EXPECTATION_REGISTRY)} expectations")

    def resolve(self, expectation_name: str) -> type:
        """Resolve expectation name to class.

        Args:
            expectation_name: Name of expectation class (e.g., "ExpectColumnMaxToBeBetween")

        Returns:
            Expectation class

        Raises:
            ValueError: If expectation name not found in registry
        """
        entry = EXPECTATION_REGISTRY.get(expectation_name)

        if entry is None:
            raise ValueError(
                f"Expectation '{expectation_name}' not found in registry. "
                f"Run 'python -m driftwatch.cli list-expectations' to see all available."
            )

        return entry["class"]

    def list_available(self) -> list[str]:
        """List all available expectation names.

        Returns:
            Sorted list of expectation class names
        """
        return sorted(EXPECTATION_REGISTRY.keys())

    def is_available(self, expectation_name: str) -> bool:
        """Check if expectation is available in registry.

        Args:
            expectation_name: Name of expectation class

        Returns:
            True if expectation exists in registry
        """
        return expectation_name in EXPECTATION_REGISTRY

    def get_expectation_info(self, expectation_name: str) -> dict:
        """Get parameter information for an expectation.

        Args:
            expectation_name: Name of expectation class

        Returns:
            Dictionary with expectation metadata including parameters
        """
        entry = EXPECTATION_REGISTRY.get(expectation_name)
        if entry is None:
            return {}

        return {
            "name": expectation_name,
            "parameters": [{"name": p} for p in entry["params"]],
        }


def get_registry() -> ExpectationRegistry:
    """Create a new expectation registry instance.

    Returns:
        ExpectationRegistry instance with all supported expectations loaded
    """
    return ExpectationRegistry()
