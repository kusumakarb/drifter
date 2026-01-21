"""Unit tests for expect_column_values_to_have_decimal_precision.py"""

import pytest
import pandas as pd
import great_expectations as gx
from driftwatch.expectations import ExpectColumnValuesToHaveDecimalPrecision


class TestColumnValuesHaveDecimalPrecisionMetric:
    """Test ColumnValuesHaveDecimalPrecision metric provider."""

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context."""
        return gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))

    def test_metric_detects_exact_precision(self, gx_context):
        """Test metric correctly identifies values with exact decimal precision."""
        df = pd.DataFrame({
            'latitude': [12.934523, 12.945231, 12.956789]  # All have 6 decimals
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="latitude",
                precision=6,
                mostly=1.0
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is True

    def test_metric_detects_insufficient_precision(self, gx_context):
        """Test metric detects values with insufficient decimal precision."""
        df = pd.DataFrame({
            'latitude': [12.93, 12.94, 12.95]  # Only 2 decimals
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="latitude",
                precision=6,
                mostly=1.0
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is False

    def test_metric_with_mixed_precision(self, gx_context):
        """Test metric with mixed precision values."""
        df = pd.DataFrame({
            'latitude': [12.934523, 12.93, 12.956789, 12.94]  # Mix of 6 and 2 decimals
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="latitude",
                precision=6,
                mostly=0.5  # 50% threshold
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # 2 out of 4 have 6 decimals (50%), should pass with mostly=0.5
        assert result.success is True


class TestExpectColumnValuesToHaveDecimalPrecision:
    """Test ExpectColumnValuesToHaveDecimalPrecision expectation class."""

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context."""
        return gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))

    def test_instantiation_with_default_params(self):
        """Test expectation can be instantiated with default parameters."""
        expectation = ExpectColumnValuesToHaveDecimalPrecision(
            column="test_column"
        )

        assert expectation.column == "test_column"
        assert expectation.precision == 6  # Default
        assert expectation.mostly == 1.0  # Default

    def test_instantiation_with_custom_params(self):
        """Test expectation can be instantiated with custom parameters."""
        expectation = ExpectColumnValuesToHaveDecimalPrecision(
            column="latitude",
            precision=4,
            mostly=0.95
        )

        assert expectation.column == "latitude"
        assert expectation.precision == 4
        assert expectation.mostly == 0.95

    def test_expectation_passes_with_exact_precision(self, gx_context):
        """Test expectation passes when all values have exact precision."""
        df = pd.DataFrame({
            'gps_lat': [12.934523, 13.045231, 14.156789, 15.267345]
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="gps_lat",
                precision=6
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is True
        assert len(result.results) == 1
        assert result.results[0].success is True

    def test_expectation_fails_with_insufficient_precision(self, gx_context):
        """Test expectation fails when values lack required precision."""
        df = pd.DataFrame({
            'gps_lat': [12.93, 13.04, 14.15, 15.26]  # Only 2 decimals
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="gps_lat",
                precision=6
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is False

    def test_expectation_with_mostly_parameter(self, gx_context):
        """Test expectation respects 'mostly' parameter."""
        df = pd.DataFrame({
            'gps_lat': [
                12.934523,  # 6 decimals ✓
                13.045231,  # 6 decimals ✓
                14.156789,  # 6 decimals ✓
                15.26,      # 2 decimals ✗
                16.37       # 2 decimals ✗
            ]
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="gps_lat",
                precision=6,
                mostly=0.6  # 60% threshold - should pass with 3/5 = 60%
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is True

    def test_expectation_with_different_precision_levels(self, gx_context):
        """Test expectation works with different precision levels."""
        test_cases = [
            (2, [12.93, 13.04], True),    # 2 decimals required
            (4, [12.9345, 13.0452], True),  # 4 decimals required
            (8, [12.93452312, 13.04523145], True),  # 8 decimals required
        ]

        for precision, values, should_pass in test_cases:
            df = pd.DataFrame({'coord': values})

            datasource = gx_context.data_sources.add_pandas(f"test_ds_{precision}")
            asset = datasource.add_dataframe_asset(name="test_asset")
            batch_def = asset.add_batch_definition_whole_dataframe("batch")
            batch_request = batch_def.build_batch_request({"dataframe": df})

            suite = gx.ExpectationSuite(name=f"test_{precision}")
            suite.add_expectation(
                ExpectColumnValuesToHaveDecimalPrecision(
                    column="coord",
                    precision=precision
                )
            )
            gx_context.suites.add(suite)

            validator = gx_context.get_validator(
                batch_request=batch_request,
                expectation_suite_name=f"test_{precision}"
            )

            result = validator.validate()
            assert result.success == should_pass

    def test_expectation_handles_negative_values(self, gx_context):
        """Test expectation correctly handles negative coordinate values."""
        df = pd.DataFrame({
            'longitude': [-122.934523, -123.045231, -124.156789]  # Negative with 6 decimals
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="longitude",
                precision=6
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        assert result.success is True

    def test_expectation_with_zero_decimals(self, gx_context):
        """Test expectation with integer values (0 decimal places)."""
        df = pd.DataFrame({
            'integers': [12.0, 13.0, 14.0]  # Should be treated as having 0 decimals when converted to string
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="integers",
                precision=6
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # Integer values don't have 6 decimal places, should fail
        assert result.success is False

    def test_expectation_validation_error_on_invalid_precision(self):
        """Test expectation raises error on invalid precision parameter."""
        # Precision must be positive integer
        with pytest.raises((ValueError, Exception)):
            ExpectColumnValuesToHaveDecimalPrecision(
                column="test",
                precision=-1
            )

    def test_expectation_in_suite_serialization(self, gx_context):
        """Test expectation can be added to suite and serialized."""
        suite = gx.ExpectationSuite(name="test")

        expectation = ExpectColumnValuesToHaveDecimalPrecision(
            column="latitude",
            precision=6,
            mostly=0.95
        )

        suite.add_expectation(expectation)

        # Suite should have 1 expectation
        assert len(suite.expectations) == 1

        # Expectation should have correct type
        assert suite.expectations[0].type == "expect_column_values_to_have_decimal_precision"


class TestRealWorldScenarios:
    """Test real-world GPS precision drift scenarios."""

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context."""
        return gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))

    def test_detects_database_truncation_bug(self, gx_context):
        """Test detecting GPS precision loss from database type change (DECIMAL(10,6) → DECIMAL(4,2))."""
        # Scenario: Database migration changed column type, truncating decimals
        df_before = pd.DataFrame({
            'restaurant_lat': [12.934523, 12.945231, 12.956789]
        })

        df_after = pd.DataFrame({
            'restaurant_lat': [12.93, 12.94, 12.95]  # Truncated to 2 decimals
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")

        # Validate reference data (should pass)
        batch_def_before = asset.add_batch_definition_whole_dataframe("batch_before")
        batch_request_before = batch_def_before.build_batch_request({"dataframe": df_before})

        suite = gx.ExpectationSuite(name="precision_check")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="restaurant_lat",
                precision=6,
                mostly=0.95
            )
        )
        gx_context.suites.add(suite)

        validator_before = gx_context.get_validator(
            batch_request=batch_request_before,
            expectation_suite_name="precision_check"
        )

        result_before = validator_before.validate()
        assert result_before.success is True  # Reference data passes

        # Validate new data with truncation (should fail)
        batch_def_after = asset.add_batch_definition_whole_dataframe("batch_after")
        batch_request_after = batch_def_after.build_batch_request({"dataframe": df_after})

        validator_after = gx_context.get_validator(
            batch_request=batch_request_after,
            expectation_suite_name="precision_check"
        )

        result_after = validator_after.validate()
        assert result_after.success is False  # Detects precision loss!

    def test_allows_some_null_values_with_mostly(self, gx_context):
        """Test expectation allows some null/missing values when using 'mostly' parameter."""
        df = pd.DataFrame({
            'restaurant_lat': [12.934523, 12.945231, None, 12.956789, None]
        })

        datasource = gx_context.data_sources.add_pandas("test_ds")
        asset = datasource.add_dataframe_asset(name="test_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")
        batch_request = batch_def.build_batch_request({"dataframe": df})

        suite = gx.ExpectationSuite(name="test")
        suite.add_expectation(
            ExpectColumnValuesToHaveDecimalPrecision(
                column="restaurant_lat",
                precision=6,
                mostly=0.60  # 60% threshold - 3/5 have 6 decimals (nulls excluded from calculation)
            )
        )
        gx_context.suites.add(suite)

        validator = gx_context.get_validator(
            batch_request=batch_request,
            expectation_suite_name="test"
        )

        result = validator.validate()

        # Should pass - 3 valid values with 6 decimals, 2 nulls ignored
        assert result.success is True
