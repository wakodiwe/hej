"""Centralized logging setup.

Public API:
    log.setup(verbosity, quiet, color)   # call once, in cli()
"""

from __future__ import annotations

import logging

_RESET = "\033[0m"
_COLORS = {
    "DEBUG": "\033[36m",  # cyan
    "INFO": "\033[32m",  # green
    "WARNING": "\033[33m",  # yellow
    "ERROR": "\033[31m",  # red
    "CRITICAL": "\033[1;31m",  # bold red
}

_LEVELS = ["WARNING", "INFO", "DEBUG"]


class _ColorFormatter(logging.Formatter):
    """Custom formatter that adds ANSI colour codes to log level names."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with ANSI colour codes around the level name."""
        code = _COLORS.get(record.levelname, "")
        if code:
            record.levelname = f"{code}{record.levelname}{_RESET}"
        return super().format(record)


def setup(verbosity: int = 0, quiet: bool = False, color: bool = True) -> None:
    """Configure the root logger. Safe to call multiple times.

    Args:
        verbosity: Number of ``-v`` flags (0=WARNING, 1=INFO, 2=DEBUG).
        quiet: If True, only show ERROR level messages.
        color: If True, use ANSI colour codes for log levels.
    """
    if quiet:
        level = "ERROR"
    else:
        level = _LEVELS[min(verbosity, len(_LEVELS) - 1)]

    handler = logging.StreamHandler()
    if color:
        handler.setFormatter(_ColorFormatter("%(levelname)s %(message)s"))
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    logging.basicConfig(level=level, handlers=[handler], force=True)

