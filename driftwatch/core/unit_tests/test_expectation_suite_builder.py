"""Unit tests for expectation_suite_builder.py"""

import pytest
import pandas as pd
import great_expectations as gx
from driftwatch.core.expectation_suite_builder import ExpectationSuiteBuilder
from driftwatch.core.config import DriftWatchConfig
from driftwatch.core.config_validator import ConfigValidationError


class TestExpectationSuiteBuilder:
    """Test ExpectationSuiteBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create ExpectationSuiteBuilder instance."""
        return ExpectationSuiteBuilder()

    @pytest.fixture
    def gx_context(self, tmp_path):
        """Create temporary GX context for testing."""
        context = gx.get_context(mode="file", project_root_dir=str(tmp_path / "gx"))
        return context

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'Time_taken(min)': [20, 25, 30, 35, 40],
            'Delivery_person_Ratings': [4.5, 4.6, 4.7, 4.8, 4.9],
            'Restaurant_latitude': [12.934523, 12.945231, 12.956789, 12.967345, 12.978901],
            'Type_of_order': ['Meal', 'Snack', 'Drinks', 'Meal', 'Buffet'],
        })

    @pytest.fixture
    def valid_config(self, tmp_path):
        """Create valid configuration for testing."""
        config_dict = {
            'schema': {'enabled': True},
            'expectations': [
                {
                    'column': 'Time_taken(min)',
                    'expectation': 'ExpectColumnStdevToBeBetween',
                    'values': {'min_value': 5.0, 'max_value': 15.0}
                },
                {
                    'column': 'Delivery_person_Ratings',
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {'min_value': 3.5, 'max_value': 5.0}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        return DriftWatchConfig(str(config_file))

    def test_init(self, builder):
        """Test builder initialization."""
        assert builder is not None
        assert builder.registry is not None

    def test_build_suite_creates_suite(self, builder, gx_context, valid_config, sample_dataframe):
        """Test build_suite creates expectation suite."""
        suite = builder.build_suite(
            context=gx_context,
            config=valid_config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        assert suite is not None
        assert suite.name == "test_suite"
        assert len(suite.expectations) > 0

    def test_build_suite_includes_schema_expectations(self, builder, gx_context, valid_config, sample_dataframe):
        """Test build_suite includes schema expectations when enabled."""
        suite = builder.build_suite(
            context=gx_context,
            config=valid_config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        # Should have schema expectations for each column
        schema_expectations = [
            exp for exp in suite.expectations
            if exp.type == "expect_column_to_exist"
        ]

        assert len(schema_expectations) == len(sample_dataframe.columns)

    def test_build_suite_includes_custom_expectations(self, builder, gx_context, valid_config, sample_dataframe):
        """Test build_suite includes expectations from config."""
        suite = builder.build_suite(
            context=gx_context,
            config=valid_config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        # Should have custom expectations from config
        expectation_types = [exp.type for exp in suite.expectations]

        assert "expect_column_stdev_to_be_between" in expectation_types
        assert "expect_column_mean_to_be_between" in expectation_types

    def test_build_suite_saves_to_context(self, builder, gx_context, valid_config, sample_dataframe):
        """Test build_suite saves suite to GX context."""
        suite = builder.build_suite(
            context=gx_context,
            config=valid_config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        # Suite should be retrievable from context
        retrieved_suite = gx_context.suites.get("test_suite")
        assert retrieved_suite is not None
        assert retrieved_suite.name == suite.name

    def test_build_suite_replaces_existing_suite(self, builder, gx_context, valid_config, sample_dataframe):
        """Test build_suite replaces existing suite with same name."""
        # Create first suite
        suite1 = builder.build_suite(
            context=gx_context,
            config=valid_config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        # Create second suite with same name
        suite2 = builder.build_suite(
            context=gx_context,
            config=valid_config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        # Should only have one suite in context
        all_suites = list(gx_context.suites.all())
        suite_names = [s.name for s in all_suites]

        assert suite_names.count("test_suite") == 1

    def test_build_suite_validates_config(self, builder, gx_context, sample_dataframe, tmp_path):
        """Test build_suite validates config before building."""
        # Create invalid config (non-existent column)
        config_dict = {
            'schema': {'enabled': False},
            'expectations': [
                {
                    'column': 'NonExistentColumn',
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {'min_value': 0, 'max_value': 100}
                }
            ]
        }

        config_file = tmp_path / "invalid_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        invalid_config = DriftWatchConfig(str(config_file))

        # Should raise ConfigValidationError
        with pytest.raises(ConfigValidationError):
            builder.build_suite(
                context=gx_context,
                config=invalid_config,
                suite_name="test_suite",
                ref_df=sample_dataframe
            )

    def test_build_suite_without_schema_check(self, builder, gx_context, sample_dataframe, tmp_path):
        """Test build_suite works with schema check disabled."""
        config_dict = {
            'schema': {'enabled': False},
            'expectations': [
                {
                    'column': 'Time_taken(min)',
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

        suite = builder.build_suite(
            context=gx_context,
            config=config,
            suite_name="test_suite",
            ref_df=sample_dataframe
        )

        # Should not have schema expectations
        schema_expectations = [
            exp for exp in suite.expectations
            if exp.type == "expect_column_to_exist"
        ]

        assert len(schema_expectations) == 0


class TestAddSchemaExpectations:
    """Test _add_schema_expectations private method."""

    @pytest.fixture
    def builder(self):
        """Create ExpectationSuiteBuilder instance."""
        return ExpectationSuiteBuilder()

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame."""
        return pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6],
            'col3': ['a', 'b', 'c']
        })

    def test_add_schema_expectations_adds_column_checks(self, builder, sample_dataframe):
        """Test _add_schema_expectations adds expectation for each column."""
        suite = gx.ExpectationSuite(name="test")

        builder._add_schema_expectations(suite, sample_dataframe)

        # Should have expectation for each column
        assert len(suite.expectations) == 3

        # All should be ExpectColumnToExist
        for exp in suite.expectations:
            assert exp.type == "expect_column_to_exist"

        # Should have expectation for each column name
        column_names = [exp.column for exp in suite.expectations]
        assert 'col1' in column_names
        assert 'col2' in column_names
        assert 'col3' in column_names

    def test_add_schema_expectations_without_ref_df_raises_error(self, builder):
        """Test _add_schema_expectations raises ValueError if ref_df is None."""
        suite = gx.ExpectationSuite(name="test")

        with pytest.raises(ValueError) as exc_info:
            builder._add_schema_expectations(suite, ref_df=None)

        assert "no reference data provided" in str(exc_info.value).lower()


class TestAddExpectations:
    """Test _add_expectations private method."""

    @pytest.fixture
    def builder(self):
        """Create ExpectationSuiteBuilder instance."""
        return ExpectationSuiteBuilder()

    @pytest.fixture
    def config_with_expectations(self, tmp_path):
        """Create config with various expectations."""
        config_dict = {
            'expectations': [
                {
                    'column': 'col1',
                    'expectation': 'ExpectColumnMeanToBeBetween',
                    'values': {'min_value': 0, 'max_value': 100}
                },
                {
                    'column': 'col2',
                    'expectation': 'ExpectColumnStdevToBeBetween',
                    'values': {'min_value': 5, 'max_value': 15}
                },
                {
                    'column': 'col3',
                    'expectation': 'ExpectColumnValuesToBeInSet',
                    'values': {'value_set': ['a', 'b', 'c']}
                }
            ]
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        return DriftWatchConfig(str(config_file))

    def test_add_expectations_adds_all_configured_expectations(self, builder, config_with_expectations):
        """Test _add_expectations adds all expectations from config."""
        suite = gx.ExpectationSuite(name="test")

        builder._add_expectations(suite, config_with_expectations)

        # Should have 3 expectations
        assert len(suite.expectations) == 3

        # Check expectation types
        expectation_types = [exp.type for exp in suite.expectations]
        assert "expect_column_mean_to_be_between" in expectation_types
        assert "expect_column_stdev_to_be_between" in expectation_types
        assert "expect_column_values_to_be_in_set" in expectation_types

    def test_add_expectations_sets_correct_parameters(self, builder, config_with_expectations):
        """Test _add_expectations sets parameters correctly."""
        suite = gx.ExpectationSuite(name="test")

        builder._add_expectations(suite, config_with_expectations)

        # Find mean expectation and check parameters
        mean_exp = [exp for exp in suite.expectations if exp.type == "expect_column_mean_to_be_between"][0]
        assert mean_exp.column == 'col1'
        assert mean_exp.min_value == 0
        assert mean_exp.max_value == 100

    def test_add_expectations_with_empty_config(self, builder, tmp_path):
        """Test _add_expectations handles empty expectations list."""
        config_dict = {'expectations': []}

        config_file = tmp_path / "empty_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))
        suite = gx.ExpectationSuite(name="test")

        # Should not raise error
        builder._add_expectations(suite, config)

        # Should have no expectations
        assert len(suite.expectations) == 0

    def test_add_expectations_with_custom_expectation(self, builder, tmp_path):
        """Test _add_expectations works with custom expectations."""
        config_dict = {
            'expectations': [
                {
                    'column': 'latitude',
                    'expectation': 'ExpectColumnValuesToHaveDecimalPrecision',
                    'values': {'precision': 6, 'mostly': 0.95}
                }
            ]
        }

        config_file = tmp_path / "custom_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f)

        config = DriftWatchConfig(str(config_file))
        suite = gx.ExpectationSuite(name="test")

        builder._add_expectations(suite, config)

        # Should have 1 custom expectation
        assert len(suite.expectations) == 1
        assert suite.expectations[0].type == "expect_column_values_to_have_decimal_precision"
