"""Unit tests for expectation_registry.py"""

import pytest
from driftwatch.core.expectation_registry import (
    ExpectationRegistry,
    EXPECTATION_REGISTRY,
    get_registry
)
from great_expectations.expectations import (
    ExpectColumnToExist,
    ExpectColumnMeanToBeBetween,
    ExpectColumnStdevToBeBetween,
)
from driftwatch.expectations import (
    ExpectColumnValuesToHaveDecimalPrecision,
    ExpectColumnCategoriesToMatchDistribution,
)


class TestExpectationRegistryConstant:
    """Test EXPECTATION_REGISTRY module-level constant."""

    def test_registry_not_empty(self):
        """Test that registry contains expectations."""
        assert len(EXPECTATION_REGISTRY) > 0

    def test_registry_has_built_in_expectations(self):
        """Test registry contains common built-in GX expectations."""
        expected_expectations = [
            "ExpectColumnToExist",
            "ExpectColumnMeanToBeBetween",
            "ExpectColumnStdevToBeBetween",
            "ExpectColumnMinToBeBetween",
            "ExpectColumnMaxToBeBetween",
            "ExpectColumnValuesToBeInSet",
        ]

        for exp_name in expected_expectations:
            assert exp_name in EXPECTATION_REGISTRY, f"{exp_name} not in registry"

    def test_registry_has_custom_expectations(self):
        """Test registry contains DriftWatch custom expectations."""
        custom_expectations = [
            "ExpectColumnValuesToHaveDecimalPrecision",
            "ExpectColumnCategoriesToMatchDistribution",
        ]

        for exp_name in custom_expectations:
            assert exp_name in EXPECTATION_REGISTRY, f"{exp_name} not in registry"

    def test_registry_entry_structure(self):
        """Test each registry entry has required fields."""
        for exp_name, entry in EXPECTATION_REGISTRY.items():
            # Each entry should have 'class' and 'params'
            assert "class" in entry, f"{exp_name} missing 'class' field"
            assert "params" in entry, f"{exp_name} missing 'params' field"

            # 'class' should be an expectation class
            assert callable(entry["class"]), f"{exp_name} class is not callable"

            # 'params' should be a list
            assert isinstance(entry["params"], list), f"{exp_name} params is not a list"

    def test_registry_maps_to_correct_classes(self):
        """Test registry maps expectation names to correct classes."""
        test_cases = [
            ("ExpectColumnToExist", ExpectColumnToExist),
            ("ExpectColumnMeanToBeBetween", ExpectColumnMeanToBeBetween),
            ("ExpectColumnStdevToBeBetween", ExpectColumnStdevToBeBetween),
            ("ExpectColumnValuesToHaveDecimalPrecision", ExpectColumnValuesToHaveDecimalPrecision),
            ("ExpectColumnCategoriesToMatchDistribution", ExpectColumnCategoriesToMatchDistribution),
        ]

        for exp_name, expected_class in test_cases:
            assert EXPECTATION_REGISTRY[exp_name]["class"] == expected_class


class TestExpectationRegistry:
    """Test ExpectationRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create ExpectationRegistry instance."""
        return ExpectationRegistry()

    def test_init(self, registry):
        """Test registry initialization."""
        assert isinstance(registry, ExpectationRegistry)

    def test_get_class_valid_expectation(self, registry):
        """Test get_class returns correct class for valid expectation."""
        exp_class = registry.get_class("ExpectColumnMeanToBeBetween")

        assert exp_class == ExpectColumnMeanToBeBetween

    def test_get_class_custom_expectation(self, registry):
        """Test get_class returns correct class for custom expectation."""
        exp_class = registry.get_class("ExpectColumnValuesToHaveDecimalPrecision")

        assert exp_class == ExpectColumnValuesToHaveDecimalPrecision

    def test_get_class_invalid_expectation(self, registry):
        """Test get_class returns None for invalid expectation."""
        exp_class = registry.get_class("NonExistentExpectation")

        assert exp_class is None

    def test_get_class_empty_string(self, registry):
        """Test get_class returns None for empty string."""
        exp_class = registry.get_class("")

        assert exp_class is None

    def test_list_expectations(self, registry):
        """Test list_expectations returns all expectation names."""
        expectations = registry.list_expectations()

        assert isinstance(expectations, list)
        assert len(expectations) > 0
        assert "ExpectColumnMeanToBeBetween" in expectations
        assert "ExpectColumnValuesToHaveDecimalPrecision" in expectations

    def test_list_expectations_sorted(self, registry):
        """Test list_expectations returns sorted list."""
        expectations = registry.list_expectations()

        assert expectations == sorted(expectations)

    def test_has_expectation_valid(self, registry):
        """Test has_expectation returns True for valid expectation."""
        assert registry.has_expectation("ExpectColumnMeanToBeBetween") is True
        assert registry.has_expectation("ExpectColumnValuesToHaveDecimalPrecision") is True

    def test_has_expectation_invalid(self, registry):
        """Test has_expectation returns False for invalid expectation."""
        assert registry.has_expectation("NonExistentExpectation") is False
        assert registry.has_expectation("") is False

    def test_get_expectation_info_valid(self, registry):
        """Test get_expectation_info returns correct info for valid expectation."""
        info = registry.get_expectation_info("ExpectColumnMeanToBeBetween")

        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "ExpectColumnMeanToBeBetween"
        assert "parameters" in info
        assert isinstance(info["parameters"], list)

        # Should have parameters like min_value, max_value
        param_names = [p["name"] for p in info["parameters"]]
        assert "min_value" in param_names
        assert "max_value" in param_names

    def test_get_expectation_info_custom_expectation(self, registry):
        """Test get_expectation_info returns correct info for custom expectation."""
        info = registry.get_expectation_info("ExpectColumnValuesToHaveDecimalPrecision")

        assert isinstance(info, dict)
        assert info["name"] == "ExpectColumnValuesToHaveDecimalPrecision"
        assert "parameters" in info

        # Should have precision and mostly parameters
        param_names = [p["name"] for p in info["parameters"]]
        assert "precision" in param_names
        assert "mostly" in param_names

    def test_get_expectation_info_invalid(self, registry):
        """Test get_expectation_info returns empty dict for invalid expectation."""
        info = registry.get_expectation_info("NonExistentExpectation")

        assert info == {}

    def test_get_expectation_info_empty_string(self, registry):
        """Test get_expectation_info returns empty dict for empty string."""
        info = registry.get_expectation_info("")

        assert info == {}


class TestGetRegistry:
    """Test get_registry factory function."""

    def test_get_registry_returns_instance(self):
        """Test get_registry returns ExpectationRegistry instance."""
        registry = get_registry()

        assert isinstance(registry, ExpectationRegistry)

    def test_get_registry_creates_new_instance(self):
        """Test get_registry creates new instance each time."""
        registry1 = get_registry()
        registry2 = get_registry()

        # Should be different instances
        assert registry1 is not registry2

    def test_get_registry_has_expectations(self):
        """Test registry from get_registry has expectations loaded."""
        registry = get_registry()

        expectations = registry.list_expectations()
        assert len(expectations) > 0


class TestRegistryParameters:
    """Test parameter lists in registry are accurate."""

    @pytest.fixture
    def registry(self):
        """Create ExpectationRegistry instance."""
        return ExpectationRegistry()

    def test_mean_expectation_parameters(self, registry):
        """Test ExpectColumnMeanToBeBetween has correct parameters."""
        info = registry.get_expectation_info("ExpectColumnMeanToBeBetween")
        param_names = [p["name"] for p in info["parameters"]]

        # Should have min_value and max_value
        assert "min_value" in param_names
        assert "max_value" in param_names

    def test_stdev_expectation_parameters(self, registry):
        """Test ExpectColumnStdevToBeBetween has correct parameters."""
        info = registry.get_expectation_info("ExpectColumnStdevToBeBetween")
        param_names = [p["name"] for p in info["parameters"]]

        # Should have min_value and max_value
        assert "min_value" in param_names
        assert "max_value" in param_names

    def test_values_in_set_parameters(self, registry):
        """Test ExpectColumnValuesToBeInSet has correct parameters."""
        info = registry.get_expectation_info("ExpectColumnValuesToBeInSet")
        param_names = [p["name"] for p in info["parameters"]]

        # Should have value_set
        assert "value_set" in param_names

    def test_decimal_precision_parameters(self, registry):
        """Test ExpectColumnValuesToHaveDecimalPrecision has correct parameters."""
        info = registry.get_expectation_info("ExpectColumnValuesToHaveDecimalPrecision")
        param_names = [p["name"] for p in info["parameters"]]

        # Should have precision and mostly
        assert "precision" in param_names
        assert "mostly" in param_names

    def test_categorical_distribution_parameters(self, registry):
        """Test ExpectColumnCategoriesToMatchDistribution has correct parameters."""
        info = registry.get_expectation_info("ExpectColumnCategoriesToMatchDistribution")
        param_names = [p["name"] for p in info["parameters"]]

        # Should have reference_distribution and psi_threshold
        assert "reference_distribution" in param_names
        assert "psi_threshold" in param_names


class TestRegistryIntegration:
    """Test registry integrates correctly with actual expectation classes."""

    @pytest.fixture
    def registry(self):
        """Create ExpectationRegistry instance."""
        return ExpectationRegistry()

    def test_can_instantiate_class_from_registry(self, registry):
        """Test can instantiate expectation class retrieved from registry."""
        exp_class = registry.get_class("ExpectColumnToExist")

        # Should be able to instantiate
        expectation = exp_class(column="test_column")

        assert expectation is not None
        assert hasattr(expectation, "column")
        assert expectation.column == "test_column"

    def test_can_instantiate_with_parameters(self, registry):
        """Test can instantiate expectation with parameters from registry."""
        exp_class = registry.get_class("ExpectColumnMeanToBeBetween")

        # Should be able to instantiate with parameters
        expectation = exp_class(
            column="test_column",
            min_value=0,
            max_value=100
        )

        assert expectation is not None
        assert expectation.column == "test_column"

    def test_can_instantiate_custom_expectation(self, registry):
        """Test can instantiate custom expectation from registry."""
        exp_class = registry.get_class("ExpectColumnValuesToHaveDecimalPrecision")

        # Should be able to instantiate
        expectation = exp_class(
            column="latitude",
            precision=6,
            mostly=0.95
        )

        assert expectation is not None
        assert expectation.column == "latitude"
