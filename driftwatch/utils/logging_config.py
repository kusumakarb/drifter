"""Logging configuration for DriftWatch."""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    format_string: str | None = None
):
    """
    Configure logging for DriftWatch.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Optional custom format string
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler (stdout for INFO and below, stderr for WARNING and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(format_string))

    # Filter to send WARNING+ to stderr
    class StdoutFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.WARNING

    class StderrFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= logging.WARNING

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(numeric_level)
    stdout_handler.setFormatter(logging.Formatter(format_string))
    stdout_handler.addFilter(StdoutFilter())

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter(format_string))
    stderr_handler.addFilter(StderrFilter())

    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(format_string))
        root_logger.addHandler(file_handler)

    # Set lower level for third-party libraries
    logging.getLogger("great_expectations").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("numexpr").setLevel(logging.WARNING)
