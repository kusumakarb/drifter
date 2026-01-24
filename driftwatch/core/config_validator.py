"""Configuration validator for DriftWatch expectation configs.

Validates expectation configurations upfront to catch errors before suite building.
Checks for:
- Required fields (column, expectation)
- Column existence in reference dataset
- Expectation availability in registry
- Parameter validity for each expectation
"""

import logging

import pandas as pd

from driftwatch.core.config import DriftWatchConfig
from driftwatch.core.expectation_registry import EXPECTATION_REGISTRY

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when config validation fails with specific error details."""

    def __init__(self, errors: list[str]):
        """Initialize with list of validation errors.

        Args:
            errors: List of error messages
        """
        self.errors = errors
        message = self._format_error_message(errors)
        super().__init__(message)

    def _format_error_message(self, errors: list[str]) -> str:
        """Format error messages for clear display.

        Args:
            errors: List of error messages

        Returns:
            Formatted error message string
        """
        error_count = len(errors)
        header = f"Configuration validation failed with {error_count} error(s):\n"
        error_list = "\n".join([f"  {i + 1}. {err}" for i, err in enumerate(errors)])
        return header + error_list


class ConfigValidator:
    """Validates DriftWatch configuration against reference data and expectation registry."""

    def __init__(self):
        """Initialize validator."""
        pass

    def validate(
        self, config: DriftWatchConfig, ref_df: pd.DataFrame | None = None
    ) -> None:
        """Validate configuration against reference data and expectation registry.

        Args:
            config: DriftWatch configuration to validate
            ref_df: Reference dataframe (optional, required for column validation)

        Raises:
            ConfigValidationError: If validation fails with detailed error messages
        """
        errors = []

        expectations_config = config.get_expectations()

        if not expectations_config:
            logger.warning("No expectations defined in config")
            return

        # Validate each expectation definition
        for idx, exp_def in enumerate(expectations_config, start=1):
            exp_errors = self._validate_expectation(exp_def, idx, ref_df)
            errors.extend(exp_errors)

        # Fail with all errors at once
        if errors:
            raise ConfigValidationError(errors)

        logger.info(f"Config validation passed for {len(expectations_config)} expectations")

    def _validate_expectation(
        self, exp_def: dict, idx: int, ref_df: pd.DataFrame | None
    ) -> list[str]:
        """Validate a single expectation definition.

        Args:
            exp_def: Expectation definition dict
            idx: Index of expectation in config (for error messages)
            ref_df: Reference dataframe (optional)

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # 1. Check required fields
        column = exp_def.get("column")
        expectation_name = exp_def.get("expectation")
        values = exp_def.get("values", {})
        severity = exp_def.get("severity")

        if not column:
            errors.append(f"Expectation #{idx}: Missing required field 'column'")

        if not expectation_name:
            errors.append(f"Expectation #{idx}: Missing required field 'expectation'")

        # Validate severity if provided
        if severity is not None:
            valid_severities = ["CRITICAL", "MAJOR", "MINOR"]
            if severity not in valid_severities:
                errors.append(
                    f"Expectation #{idx}: Invalid severity '{severity}'. "
                    f"Must be one of: {', '.join(valid_severities)}"
                )

        # If required fields missing, skip further validation
        if not column or not expectation_name:
            return errors

        # 2. Check column exists in reference data
        if ref_df is not None and column not in ref_df.columns:
            available_cols = ", ".join(list(ref_df.columns)[:5])
            errors.append(
                f"Expectation #{idx}: Column '{column}' not found in reference data. "
                f"Available columns: {available_cols}... (total: {len(ref_df.columns)})"
            )

        # 3. Check expectation exists in registry
        if expectation_name not in EXPECTATION_REGISTRY:
            available = sorted(EXPECTATION_REGISTRY.keys())
            available_preview = ", ".join(available[:5])
            errors.append(
                f"Expectation #{idx}: Expectation '{expectation_name}' not found in registry. "
                f"Available: {available_preview}... (total: {len(available)}). "
                f"Run 'python -m driftwatch.cli list-expectations' to see all."
            )
            return errors

        # 4. Validate parameters for this expectation
        expected_params = EXPECTATION_REGISTRY[expectation_name]["params"]
        param_errors = self._validate_parameters(
            expectation_name, expected_params, values, idx
        )
        errors.extend(param_errors)

        return errors

    def _validate_parameters(
        self, expectation_name: str, expected_params: list[str], values: dict, idx: int
    ) -> list[str]:
        """Validate parameters for an expectation.

        Args:
            expectation_name: Name of expectation
            expected_params: List of expected parameter names
            values: Provided parameter values
            idx: Index of expectation in config

        Returns:
            List of error messages
        """
        errors = []

        # Check for missing required parameters (basic check)
        # Note: Some params like 'mostly' are optional, so we only warn for truly required ones
        provided_params = set(values.keys())
        expected_params_set = set(expected_params)

        # Parameters that are commonly optional
        optional_params = {"mostly", "strict_min", "strict_max", "or_equal", "ties_okay"}

        required_params = expected_params_set - optional_params
        missing_params = required_params - provided_params

        if missing_params:
            errors.append(
                f"Expectation #{idx} ({expectation_name} on '{values.get('column', 'unknown')}'): "
                f"Missing required parameter(s): {', '.join(sorted(missing_params))}"
            )

        # Check for unexpected parameters
        unexpected_params = provided_params - expected_params_set
        if unexpected_params:
            errors.append(
                f"Expectation #{idx} ({expectation_name}): "
                f"Unexpected parameter(s): {', '.join(sorted(unexpected_params))}. "
                f"Expected: {', '.join(expected_params) if expected_params else '(none)'}"
            )

        return errors


def validate_config(
    config: DriftWatchConfig, ref_df: pd.DataFrame | None = None
) -> None:
    """Validate DriftWatch configuration.

    Convenience function for quick validation.

    Args:
        config: DriftWatch configuration
        ref_df: Reference dataframe (optional)

    Raises:
        ConfigValidationError: If validation fails
    """
    validator = ConfigValidator()
    validator.validate(config, ref_df)
