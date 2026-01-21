"""Unit tests for config_validator.py"""

import pytest
import pandas as pd
from driftwatch.core.config_validator import ConfigValidator, ConfigValidationError
from driftwatch.core.config import DriftWatchConfig


class TestConfigValidationError:
    """Test ConfigValidationError exception class."""

    def test_single_error(self):
        """Test error formatting with single error."""
        errors = ["Column 'foo' not found"]
        exc = ConfigValidationError(errors)

        assert "1 error(s)" in str(exc)
        assert "Column 'foo' not found" in str(exc)
        assert exc.errors == errors

    def test_multiple_errors(self):
        """Test error formatting with multiple errors."""
        errors = [
            "Missing required field 'column'",
            "Column 'bar' not found",
            "Expectation 'InvalidExpectation' not found"
        ]
        exc = ConfigValidationError(errors)

        assert "3 error(s)" in str(exc)
        for error in errors:
            assert error in str(exc)


class TestConfigValidator:
    """Test ConfigValidator class."""

    @pytest.fixture
    def validator(self):
        """Create ConfigValidator instance."""
        return ConfigValidator()

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'Time_taken(min)': [20, 25, 30, 35, 40],
            'Delivery_person_Ratings': [4.5, 4.6, 4.7, 4.8, 4.9],
            'Restaurant_latitude': [12.934523, 12.945231, 12.956789, 12.967345, 12.978901],
            'Type_of_order': ['Meal', 'Snack', 'Drinks', 'Meal', 'Buffet'],
            'Road_traffic_density': ['Low', 'Medium', 'High', 'Jam', 'Low']
        })

    @pytest.fixture
    def valid_config_dict(self):
        """Create valid configuration dictionary."""
        return {
            'schema': {'enabled': True},
            'expectations': [
                {
                    'column': 'Time_taken(min)',
                    'expectation': 'ExpectColumnStdevToBeBetween',
                    'values': {'min_value': 8.5, 'max_value': 11.5}
                },
                {
                    'column': 'Delivery_person_Ratings',
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {'min_value': 3.5, 'max_value': 5.0}
                }
            ]
        }

    def test_validate_success_with_valid_config(self, validator, valid_config_dict, sample_dataframe, tmp_path):
        """Test validation passes with valid configuration."""
        # Create config file
        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(valid_config_dict, f)

        config = DriftWatchConfig(str(config_file))

        # Should not raise exception
        validator.validate(config, sample_dataframe)

    def test_validate_missing_column_field(self, validator, tmp_path):
        """Test validation fails when 'column' field is missing."""
        config_dict = {
            'expectations': [
                {
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {'min_value': 3.5, 'max_value': 5.0}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "Missing required field 'column'" in str(exc_info.value)

    def test_validate_missing_expectation_field(self, validator, tmp_path):
        """Test validation fails when 'expectation' field is missing."""
        config_dict = {
            'expectations': [
                {
                    'column': 'Time_taken(min)',
                    'values': {'min_value': 8.5, 'max_value': 11.5}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "Missing required field 'expectation'" in str(exc_info.value)

    def test_validate_column_not_in_dataframe(self, validator, sample_dataframe, tmp_path):
        """Test validation fails when column doesn't exist in reference data."""
        config_dict = {
            'expectations': [
                {
                    'column': 'NonExistentColumn',
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {'min_value': 0, 'max_value': 100}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config, sample_dataframe)

        error_msg = str(exc_info.value)
        assert "Column 'NonExistentColumn' not found" in error_msg
        assert "Available columns:" in error_msg

    def test_validate_invalid_expectation_name(self, validator, sample_dataframe, tmp_path):
        """Test validation fails with invalid expectation name."""
        config_dict = {
            'expectations': [
                {
                    'column': 'Time_taken(min)',
                    'expectation': 'ExpectSomethingInvalid',
                    'values': {}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config, sample_dataframe)

        error_msg = str(exc_info.value)
        assert "Expectation 'ExpectSomethingInvalid' not found" in error_msg
        assert "Available:" in error_msg

    def test_validate_multiple_errors(self, validator, sample_dataframe, tmp_path):
        """Test validation collects multiple errors before failing."""
        config_dict = {
            'expectations': [
                {
                    'column': 'NonExistent1',
                    'expectation': 'InvalidExpectation1',
                    'values': {}
                },
                {
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {}
                },
                {
                    'column': 'NonExistent2',
                    'values': {}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config, sample_dataframe)

        # Should collect all errors
        exc = exc_info.value
        assert len(exc.errors) >= 3
        assert "3 error(s)" in str(exc) or len(exc.errors) > 3

    def test_validate_no_expectations(self, validator, tmp_path, caplog):
        """Test validation with empty expectations (should log warning)."""
        config_dict = {
            'expectations': []
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))

        # Should not raise, just warn
        validator.validate(config)

        assert "No expectations defined" in caplog.text

    def test_validate_without_reference_dataframe(self, validator, valid_config_dict, tmp_path):
        """Test validation without reference dataframe (skips column checks)."""
        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(valid_config_dict, f)

        config = DriftWatchConfig(str(config_file))

        # Should pass - column existence not checked without ref_df
        validator.validate(config, ref_df=None)


class TestValidateExpectation:
    """Test _validate_expectation private method."""

    @pytest.fixture
    def validator(self):
        """Create ConfigValidator instance."""
        return ConfigValidator()

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4.5, 5.5, 6.5]
        })

    def test_validate_expectation_valid(self, validator, sample_dataframe):
        """Test _validate_expectation with valid expectation definition."""
        exp_def = {
            'column': 'col1',
            'expectation': 'ExpectColumnMeanToBeBetween',
            'values': {'min_value': 0, 'max_value': 10}
        }

        errors = validator._validate_expectation(exp_def, 1, sample_dataframe)

        assert errors == []

    def test_validate_expectation_missing_column_field(self, validator):
        """Test _validate_expectation detects missing column field."""
        exp_def = {
            'expectation': 'ExpectColumnMeanToBeBetween',
            'values': {}
        }

        errors = validator._validate_expectation(exp_def, 1, None)

        assert len(errors) >= 1
        assert any("Missing required field 'column'" in err for err in errors)

    def test_validate_expectation_missing_expectation_field(self, validator):
        """Test _validate_expectation detects missing expectation field."""
        exp_def = {
            'column': 'col1',
            'values': {}
        }

        errors = validator._validate_expectation(exp_def, 1, None)

        assert len(errors) >= 1
        assert any("Missing required field 'expectation'" in err for err in errors)

    def test_validate_expectation_column_not_in_df(self, validator, sample_dataframe):
        """Test _validate_expectation detects column not in dataframe."""
        exp_def = {
            'column': 'nonexistent',
            'expectation': 'ExpectColumnMeanToBeBetween',
            'values': {}
        }

        errors = validator._validate_expectation(exp_def, 1, sample_dataframe)

        assert len(errors) >= 1
        assert any("Column 'nonexistent' not found" in err for err in errors)

    def test_validate_expectation_invalid_expectation_name(self, validator, sample_dataframe):
        """Test _validate_expectation detects invalid expectation name."""
        exp_def = {
            'column': 'col1',
            'expectation': 'InvalidExpectation',
            'values': {}
        }

        errors = validator._validate_expectation(exp_def, 1, sample_dataframe)

        assert len(errors) >= 1
        assert any("Expectation 'InvalidExpectation' not found" in err for err in errors)

    def test_validate_expectation_skips_column_check_without_df(self, validator):
        """Test _validate_expectation skips column check when ref_df is None."""
        exp_def = {
            'column': 'any_column',
            'expectation': 'ExpectColumnMeanToBeBetween',
            'values': {'min_value': 0, 'max_value': 10}
        }

        # Should not error even though we can't verify column exists
        errors = validator._validate_expectation(exp_def, 1, None)

        # Should only fail if expectation itself is invalid, not column
        assert not any("not found in reference data" in err for err in errors)

    def test_validate_expectation_early_return_on_missing_required_fields(self, validator):
        """Test _validate_expectation returns early if required fields missing."""
        exp_def = {
            'values': {}
        }

        errors = validator._validate_expectation(exp_def, 1, None)

        # Should have errors for both missing fields
        assert len(errors) == 2
        assert any("Missing required field 'column'" in err for err in errors)
        assert any("Missing required field 'expectation'" in err for err in errors)
