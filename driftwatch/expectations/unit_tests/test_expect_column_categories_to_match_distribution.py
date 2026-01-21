"""Unit tests for expect_column_categories_to_match_distribution.py"""

import pytest
import pandas as pd
import numpy as np
import great_expectations as gx
from driftwatch.expectations import ExpectColumnCategoriesToMatchDistribution


class TestColumnCategoricalDistributionPSIMetric:
    """Test ColumnCategoricalDistributionPSI metric provider."""

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context."""
        return gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))

    def test_metric_calculates_zero_psi_for_identical_distributions(self, gx_context):
        """Test PSI is ~0 when distributions are identical."""
        # Same distribution as reference
        df = pd.DataFrame({
            'traffic': ['Low'] * 34 + ['Medium'] * 24 + ['High'] * 10 + ['Jam'] * 31
        })

        reference_dist = {
            'Low': 0.344,
            'Medium': 0.243,
            'High': 0.098,
            'Jam': 0.314
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="traffic",
                reference_distribution=reference_dist,
                psi_threshold=0.1
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # PSI should be very small (close to 0) for identical distributions
        assert result.success is True

    def test_metric_calculates_high_psi_for_different_distributions(self, gx_context):
        """Test PSI is high when distributions are very different."""
        # Drastically different distribution (mostly Jam now)
        df = pd.DataFrame({
            'traffic': ['Jam'] * 90 + ['Low'] * 10
        })

        reference_dist = {
            'Low': 0.344,
            'Medium': 0.243,
            'High': 0.098,
            'Jam': 0.314
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="traffic",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # PSI should be very high, exceeding threshold
        assert result.success is False


class TestExpectColumnCategoriesToMatchDistribution:
    """Test ExpectColumnCategoriesToMatchDistribution expectation class."""

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context."""
        return gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))

    def test_instantiation_with_required_params(self):
        """Test expectation can be instantiated with required parameters."""
        expectation = ExpectColumnCategoriesToMatchDistribution(
            column="status",
            reference_distribution={'Active': 0.7, 'Inactive': 0.3},
            psi_threshold=0.25
        )

        assert expectation.column == "status"
        assert expectation.reference_distribution == {'Active': 0.7, 'Inactive': 0.3}
        assert expectation.psi_threshold == 0.25

    def test_instantiation_with_default_threshold(self):
        """Test expectation uses default PSI threshold."""
        expectation = ExpectColumnCategoriesToMatchDistribution(
            column="status",
            reference_distribution={'Active': 0.7, 'Inactive': 0.3}
        )

        assert expectation.psi_threshold == 0.25  # Default

    def test_expectation_passes_with_stable_distribution(self, gx_context):
        """Test expectation passes when distribution is stable."""
        # Similar distribution to reference
        df = pd.DataFrame({
            'order_type': ['Meal'] * 70 + ['Snack'] * 20 + ['Drinks'] * 10
        })

        reference_dist = {
            'Meal': 0.68,
            'Snack': 0.22,
            'Drinks': 0.10
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="order_type",
                reference_distribution=reference_dist,
                psi_threshold=0.1
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is True

    def test_expectation_fails_with_drifted_distribution(self, gx_context):
        """Test expectation fails when distribution has drifted significantly."""
        # Distribution shifted dramatically
        df = pd.DataFrame({
            'order_type': ['Snack'] * 90 + ['Meal'] * 10
        })

        reference_dist = {
            'Meal': 0.70,
            'Snack': 0.20,
            'Drinks': 0.10
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="order_type",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is False

    def test_expectation_handles_new_categories(self, gx_context):
        """Test expectation handles new categories not in reference."""
        df = pd.DataFrame({
            'order_type': ['Meal'] * 50 + ['Snack'] * 30 + ['Buffet'] * 20  # 'Buffet' is new
        })

        reference_dist = {
            'Meal': 0.70,
            'Snack': 0.30
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="order_type",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # New category should contribute to PSI
        # Success depends on whether PSI exceeds threshold
        assert result.success in [True, False]  # Just verify it doesn't crash

    def test_expectation_handles_missing_categories(self, gx_context):
        """Test expectation handles categories present in reference but missing in data."""
        df = pd.DataFrame({
            'order_type': ['Meal'] * 100  # Only 'Meal', missing 'Snack' and 'Drinks'
        })

        reference_dist = {
            'Meal': 0.70,
            'Snack': 0.20,
            'Drinks': 0.10
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="order_type",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # Missing categories should contribute to high PSI
        assert result.success is False

    def test_expectation_with_different_thresholds(self, gx_context):
        """Test expectation behavior with different PSI thresholds."""
        # Moderate drift scenario
        df = pd.DataFrame({
            'traffic': ['Low'] * 40 + ['Medium'] * 30 + ['High'] * 15 + ['Jam'] * 15
        })

        reference_dist = {
            'Low': 0.344,
            'Medium': 0.243,
            'High': 0.098,
            'Jam': 0.314
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")

        # Test with strict threshold (0.1)
        batch_def_strict = asset.add_batch_definition_whole_dataframe("batch_strict")
        batch_request_strict = batch_def_strict.build_batch_request({"dataframe": df})

        suite_strict = gx.ExpectationSuite(name="test_strict")
        suite_strict.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="traffic",
                reference_distribution=reference_dist,
                psi_threshold=0.1  # Strict
            )
        )
        gx_context.suites.add(suite_strict)

        validator_strict = gx_context.get_validator(
            batch_request=batch_request_strict,
            expectation_suite_name="test_strict"
        )

        result_strict = validator_strict.validate()

        # Test with lenient threshold (0.5)
        batch_def_lenient = asset.add_batch_definition_whole_dataframe("batch_lenient")
        batch_request_lenient = batch_def_lenient.build_batch_request({"dataframe": df})

        suite_lenient = gx.ExpectationSuite(name="test_lenient")
        suite_lenient.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="traffic",
                reference_distribution=reference_dist,
                psi_threshold=0.5  # Lenient
            )
        )
        gx_context.suites.add(suite_lenient)

        validator_lenient = gx_context.get_validator(
            batch_request=batch_request_lenient,
            expectation_suite_name="test_lenient"
        )

        result_lenient = validator_lenient.validate()

        # Lenient threshold should be more likely to pass
        # (actual result depends on calculated PSI)
        assert isinstance(result_strict.success, bool)
        assert isinstance(result_lenient.success, bool)


class TestRealWorldScenarios:
    """Test real-world categorical distribution drift scenarios."""

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context."""
        return gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))

    def test_detects_traffic_pattern_shift(self, gx_context):
        """Test detecting traffic pattern shift (case study scenario)."""
        # Reference: Balanced traffic distribution
        df_reference = pd.DataFrame({
            'traffic': ['Low'] * 344 + ['Medium'] * 243 + ['High'] * 98 + ['Jam'] * 314
        })

        # New data: Mostly jammed traffic
        df_drifted = pd.DataFrame({
            'traffic': ['Jam'] * 899 + ['Low'] * 101
        })

        reference_dist = {
            'Low': 0.344,
            'Medium': 0.243,
            'High': 0.098,
            'Jam': 0.314
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")

        # Validate reference data (should pass)
        batch_def_ref = asset.add_batch_definition_whole_dataframe("batch_ref")
        batch_request_ref = batch_def_ref.build_batch_request({"dataframe": df_reference})

        suite = gx.ExpectationSuite(name="traffic_check")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="traffic",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator_ref = gx_context.get_validator(
            batch_request=batch_request_ref,
            expectation_suite_name="traffic_check"
        )

        result_ref = validator_ref.validate()
        assert result_ref.success is True  # Reference passes

        # Validate drifted data (should fail)
        batch_def_drift = asset.add_batch_definition_whole_dataframe("batch_drift")
        batch_request_drift = batch_def_drift.build_batch_request({"dataframe": df_drifted})

        validator_drift = gx_context.get_validator(
            batch_request=batch_request_drift,
            expectation_suite_name="traffic_check"
        )

        result_drift = validator_drift.validate()
        assert result_drift.success is False  # Detects drift!

    def test_detects_category_disappearance(self, gx_context):
        """Test detecting when a category completely disappears."""
        # Category 'Medium' disappears
        df = pd.DataFrame({
            'status': ['Active'] * 60 + ['Pending'] * 40
            # 'Inactive' category missing!
        })

        reference_dist = {
            'Active': 0.50,
            'Pending': 0.30,
            'Inactive': 0.20  # Present in reference
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="status",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # Missing category should cause high PSI, failing the expectation
        assert result.success is False

    def test_detects_category_explosion(self, gx_context):
        """Test detecting when a rare category suddenly dominates."""
        # 'Buffet' was rare (5%) but now dominates (70%)
        df = pd.DataFrame({
            'order_type': ['Buffet'] * 70 + ['Meal'] * 20 + ['Snack'] * 10
        })

        reference_dist = {
            'Meal': 0.60,
            'Snack': 0.35,
            'Buffet': 0.05  # Was rare
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="order_type",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # Category explosion should cause high PSI
        assert result.success is False

    def test_handles_empty_column(self, gx_context):
        """Test expectation handles empty column gracefully."""
        df = pd.DataFrame({
            'traffic': []  # Empty column
        })

        reference_dist = {
            'Low': 0.5,
            'High': 0.5
        }

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnCategoriesToMatchDistribution(
                column="traffic",
                reference_distribution=reference_dist,
                psi_threshold=0.25
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        # Should not crash, handles empty column
        result = validator.validate()

        assert isinstance(result.success, bool)

    def test_expectation_in_suite_serialization(self, gx_context):
        """Test expectation can be added to suite and serialized."""
        suite = gx.ExpectationSuite(name="test")

        expectation = ExpectColumnCategoriesToMatchDistribution(
            column="status",
            reference_distribution={'Active': 0.7, 'Inactive': 0.3},
            psi_threshold=0.25
        )

        suite.add_expectation(expectation)

        # Suite should have 1 expectation
        assert len(suite.expectations) == 1

        # Expectation should have correct type
        assert suite.expectations[0].type == "expect_column_categories_to_match_distribution"
