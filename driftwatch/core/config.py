"""Configuration management for DriftWatch."""

from pathlib import Path
from typing import Any

import yaml


class DriftWatchConfig:
    """Loads and manages DriftWatch configuration from YAML file."""

    def __init__(self, config_path: str = "driftwatch_config.yaml"):
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create a driftwatch_config.yaml file or specify a valid path."
            )

        with self.config_path.open() as f:
            self.config = yaml.safe_load(f)

        # Extract major sections (simplified)
        self.schema = self.config.get('schema', {'enabled': True})
        self.expectations = self.config.get('expectations', [])
        self.reporting = self.config.get('reporting', {})
        self.logging_config = self.config.get('logging', {})

    def is_schema_check_enabled(self) -> bool:
        """Check if schema validation is enabled.

        Returns:
            True if schema check is enabled (default: True)
        """
        return self.schema.get('enabled', True)

    def get_expectations(self) -> list[dict[str, Any]]:
        """Get column-level expectations from config.

        Returns:
            List of expectation definitions
        """
        return self.expectations

    def get_report_formats(self) -> list[str]:
        """Get list of enabled report formats."""
        return self.reporting.get('formats', ['json'])

    def get_default_format(self) -> str:
        """Get default report format."""
        return self.reporting.get('default_format', 'json')

    def get_output_dir(self) -> str:
        """Get report output directory."""
        return self.reporting.get('output_dir', './reports')

    def get_log_level(self) -> str:
        """Get logging level."""
        return self.logging_config.get('level', 'INFO')

    def should_show_progress(self) -> bool:
        """Check if progress bars should be shown."""
        return self.logging_config.get('progress_bar', True)

    def __repr__(self) -> str:
        return f"DriftWatchConfig(path='{self.config_path}')"
