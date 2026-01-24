"""Enriches GX validation results with DriftWatch-specific metadata.

Adds custom metadata to GX validation results for:
- Configuration tracking
- Drift severity computation
- Duration tracking
- Timestamp recording
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class ValidationResultEnricher:
    """Adds DriftWatch-specific metadata to GX validation results.

    GX validation results are automatically stored in:
    gx/uncommitted/validations/{run_id}/{suite_name}/{result_id}.json

    This enricher adds custom metadata to the 'meta' field:
    - config_file: Path to DriftWatch config
    - total_drifts: Count of failed expectations
    - severity: Overall drift severity (CLEAN, MINOR, MAJOR, CRITICAL)
    - duration_seconds: Validation execution time
    - timestamp: ISO 8601 timestamp
    """

    @staticmethod
    def enrich_result(
        validation_result,
        config_file: str | None,
        duration_seconds: float
    ):
        """Enrich validation result with DriftWatch metadata.

        Args:
            validation_result: GX CheckpointResult or ValidationResult object
            config_file: Path to DriftWatch configuration file
                (optional, only needed during profile)
            duration_seconds: Time taken for validation

        Returns:
            Enriched validation result (same object, modified in place)
        """
        # Compute DriftWatch metrics
        total_drifts = sum(1 for r in validation_result.results if not r.success)
        severity = ValidationResultEnricher._compute_severity(validation_result)

        # Add to GX validation result meta
        if not hasattr(validation_result, 'meta') or validation_result.meta is None:
            validation_result.meta = {}

        validation_result.meta['driftwatch'] = {
            'config_file': config_file,
            'total_drifts': total_drifts,
            'severity': severity,
            'duration_seconds': round(duration_seconds, 2),
            'timestamp': datetime.now(UTC).isoformat()
        }

        logger.info(f"Enriched validation result: drifts={total_drifts}, severity={severity}")

        return validation_result

    @staticmethod
    def _compute_severity(validation_result) -> str:
        """Compute overall severity from validation results.

        Args:
            validation_result: GX validation result

        Returns:
            Severity string: CLEAN, MINOR, MAJOR, or CRITICAL
        """
        # Collect all severities from failed expectations
        severities = []

        for result in validation_result.results:
            if not result.success:
                # Check expectation config for severity, default to MINOR
                expectation_config = result.expectation_config
                if hasattr(expectation_config, 'meta') and expectation_config.meta:
                    severity = expectation_config.meta.get('severity', 'MINOR')
                else:
                    severity = 'MINOR'
                severities.append(severity.upper())

        # No failures = CLEAN
        if not severities:
            return 'CLEAN'

        # Return highest severity
        if 'CRITICAL' in severities:
            return 'CRITICAL'
        if 'MAJOR' in severities:
            return 'MAJOR'
        if 'MINOR' in severities:
            return 'MINOR'
        return 'CLEAN'


    @staticmethod
    def get_enriched_metadata(validation_result) -> dict[str, Any]:
        """Extract DriftWatch metadata from enriched validation result.

        Args:
            validation_result: Enriched GX validation result

        Returns:
            Dictionary with DriftWatch metadata, or empty dict if not enriched
        """
        if hasattr(validation_result, 'meta') and validation_result.meta:
            return validation_result.meta.get('driftwatch', {})
        return {}
