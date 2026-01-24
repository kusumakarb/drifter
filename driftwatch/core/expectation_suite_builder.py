"""Builds Great Expectations Expectation Suites from config.

Simplified approach:
1. Schema check (automated from reference data)
2. Column-level expectations (user-provided values from config)
"""

import logging

import great_expectations as gx
import pandas as pd
from great_expectations.expectations import ExpectColumnToExist

from driftwatch.core.config import DriftWatchConfig
from driftwatch.core.config_validator import validate_config
from driftwatch.core.expectation_registry import get_registry

logger = logging.getLogger(__name__)


class ExpectationSuiteBuilder:
    """Builds GX Expectation Suites from config.

    Simple two-level approach:
    - Schema expectations: Check all columns exist (from reference data)
    - Column expectations: User-specified expectations from config
    """

    def __init__(self):
        """Initialize builder with expectation registry."""
        self.registry = get_registry()

    def build_suite(
            self,
            context,
            config: DriftWatchConfig,
            suite_name: str,
            ref_df: pd.DataFrame | None = None
    ):
        """Build expectation suite from config.

        Args:
            context: GX context object
            config: DriftWatch configuration
            suite_name: Name for the expectation suite
            ref_df: Optional reference dataset (only used for schema check)

        Returns:
            GX ExpectationSuite object

        Raises:
            ConfigValidationError: If config validation fails
        """
        logger.info(f"Building expectation suite: {suite_name}")
        if ref_df is not None:
            logger.info(f"Reference data: {len(ref_df)} rows, {len(ref_df.columns)} columns")

        # Validate config upfront before building suite
        validate_config(config, ref_df)

        # Check if suite exists and delete it before creating new one
        existing_suite_names = [s.name for s in context.suites.all()]
        if suite_name in existing_suite_names:
            logger.info(f"Found existing suite '{suite_name}', deleting to recreate")
            context.suites.delete(suite_name)
            logger.info(f"Deleted existing suite '{suite_name}'")
        else:
            logger.info(f"No existing suite '{suite_name}' found, creating new")

        # Create expectation suite
        suite = gx.ExpectationSuite(name=suite_name)

        # 1. Schema expectations (if enabled and reference data provided)
        if config.is_schema_check_enabled():
            self._add_schema_expectations(suite, ref_df)

        # 2. Column-level expectations from config
        self._add_expectations(suite, config)

        # Save suite to context
        context.suites.add(suite)
        logger.info(f"✓ Suite saved with {len(suite.expectations)} total expectations")

        return suite

    def _add_schema_expectations(
            self,
            suite: gx.ExpectationSuite,
            ref_df: pd.DataFrame | None
    ):
        """Add schema expectations (column existence checks).

        Args:
            suite: GX expectation suite
            ref_df: Reference dataframe (optional)
        """
        if ref_df is None:
            raise ValueError(
                "Schema check enabled but no reference data provided. "
                "Either provide --reference argument or disable schema check in config."
            )

        logger.info("Adding schema expectations...")
        for col in ref_df.columns:
            suite.add_expectation(
                ExpectColumnToExist(column=col, meta={"severity": "CRITICAL"})
            )
        logger.info(f"✓ Added {len(ref_df.columns)} column existence expectations")

    def _add_expectations(
            self,
            suite: gx.ExpectationSuite,
            config: DriftWatchConfig
    ):
        """Add column-level expectations from config.

        Args:
            suite: GX expectation suite
            config: DriftWatch configuration
        """
        logger.info("Adding column-level expectations...")

        expectations_config = config.get_expectations()

        if not expectations_config:
            logger.info("No column-level expectations defined")
            return

        added_count = 0

        for exp_def in expectations_config:
            column = exp_def.get('column')
            expectation_name = exp_def.get('expectation')
            values = exp_def.get('values', {})
            severity = exp_def.get('severity')

            # Resolve expectation class
            expectation_cls = self.registry.resolve(expectation_name)

            # Instantiate expectation with column + values
            expectation_instance = expectation_cls(
                column=column,
                **values
            )

            # Add severity to metadata if configured
            if severity:
                if not expectation_instance.meta:
                    expectation_instance.meta = {}
                expectation_instance.meta['severity'] = severity

            # Add to suite
            suite.add_expectation(expectation_instance)
            added_count += 1

            logger.debug(
                f"Added expectation: {expectation_name} "
                f"on column '{column}'"
            )

        logger.info(f"✓ Added {added_count} column-level expectations")
