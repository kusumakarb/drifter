"""Great Expectations context manager for DriftWatch.

Provides centralized GX file context management for persistent state storage.
"""

import logging
from pathlib import Path

import great_expectations as gx

logger = logging.getLogger(__name__)


class DriftWatchGXContext:
    """Manages Great Expectations file context for DriftWatch.

    Provides persistent state management using GX file context:
    - Expectation suites stored in gx/expectations/
    - Validation results stored in gx/uncommitted/validations/
    - Data Docs generated in gx/uncommitted/data_docs/
    """

    def __init__(self, project_root: str = "."):
        """Initialize GX file context.

        Args:
            project_root: Root directory for GX context (default: current directory)
        """
        self.project_root = Path(project_root)

        # Initialize or load file context (GX handles both cases)
        logger.info(f"Loading GX file context with project root: {self.project_root}")
        self.context = gx.get_context(mode="file", project_root_dir=str(self.project_root))

    def get_context(self):
        """Get the GX context.

        Returns:
            Great Expectations context object
        """
        return self.context
