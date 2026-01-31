"""
logger.py - Shared logging utility for NMDP Coach Cross-Reference System

Provides consistent logging across all Python scripts with both console
and file output. Log files are written to output/logs/[school_name]_[date].log
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


# Custom log format matching PRD spec
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Module-level logger instance
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[str] = None


def get_logs_dir() -> str:
    """Get the logs directory path, creating it if needed."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "..", "output", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_log_filename(school_name: str = None, prefix: str = None) -> str:
    """
    Generate a log filename.

    Args:
        school_name: School name (will be normalized for filename)
        prefix: Alternative prefix if no school name

    Returns:
        Filename like "university_of_oregon_2026-01-26.log"
    """
    date_str = datetime.now().strftime("%Y-%m-%d")

    if school_name:
        # Normalize school name for filename
        name_part = school_name.lower().replace(" ", "_").replace("-", "_")
        return f"{name_part}_{date_str}.log"
    elif prefix:
        return f"{prefix}_{date_str}.log"
    else:
        return f"gitgsearch_{date_str}.log"


def setup_logger(
    school_name: str = None,
    prefix: str = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    append: bool = True
) -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        school_name: School name for log file naming
        prefix: Alternative prefix if no school name
        console_level: Minimum level for console output
        file_level: Minimum level for file output
        append: If True, append to existing log file; if False, overwrite

    Returns:
        Configured logger instance
    """
    global _logger, _log_file_path

    # Create logger
    logger = logging.getLogger("gitgsearch")
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers filter

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    logs_dir = get_logs_dir()
    log_filename = get_log_filename(school_name, prefix)
    _log_file_path = os.path.join(logs_dir, log_filename)

    file_mode = "a" if append else "w"
    file_handler = logging.FileHandler(_log_file_path, mode=file_mode, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the current logger instance.

    If no logger has been set up, creates a default one.

    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def get_log_file_path() -> Optional[str]:
    """Get the current log file path."""
    return _log_file_path


def log_section(title: str, char: str = "="):
    """Log a section header for visual separation."""
    logger = get_logger()
    line = char * 50
    logger.info(line)
    logger.info(title)
    logger.info(line)


def log_summary(stats: dict):
    """
    Log a summary of operations.

    Args:
        stats: Dictionary of statistics to log
    """
    logger = get_logger()
    logger.info("Summary:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")


# Convenience functions for quick logging without setup
def info(message: str):
    """Log an INFO message."""
    get_logger().info(message)


def warning(message: str):
    """Log a WARNING message."""
    get_logger().warning(message)


def error(message: str):
    """Log an ERROR message."""
    get_logger().error(message)


def debug(message: str):
    """Log a DEBUG message."""
    get_logger().debug(message)


if __name__ == "__main__":
    # Demo/test the logger
    print("Testing logger...\n")

    # Set up logger for a school
    logger = setup_logger(school_name="Test University")

    log_section("Starting Test Run")

    info("This is an info message")
    warning("This is a warning message")
    error("This is an error message")
    debug("This is a debug message (only in file)")

    log_summary({
        "Total coaches": 12,
        "Overlaps found": 3,
        "Verified": 10,
        "Unverified": 2
    })

    log_section("Test Complete")

    print(f"\nLog file written to: {get_log_file_path()}")
