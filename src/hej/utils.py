"""Date and size formatting utilities."""

from __future__ import annotations

from datetime import datetime

DATE_FORMAT = "%d.%m.%y"
TIME_FORMAT = "%I:%M"
FORMAT_DATETIME = "datetime"
FORMAT_DATE = "date"
FORMAT_TIME = "time"


def fmt_date(s: str, format_type: str = FORMAT_DATETIME) -> str:
    """Parse an ISO-8601 datetime string and return a formatted string.

    Args:
        s: ISO-8601 datetime string to format.
        format_type: Format type — ``"datetime"``, ``"date"``, or ``"time"``.

    Returns:
        Formatted date/time string, or empty string for unknown *format_type*.
    """
    dt = datetime.fromisoformat(s)
    _date = dt.strftime(DATE_FORMAT)
    _time = dt.strftime(TIME_FORMAT)
    if FORMAT_DATETIME == format_type:
        return f"{_date}, {_time}"
    if FORMAT_DATE == format_type:
        return _date
    if FORMAT_TIME == format_type:
        return _time
    return ""


def fmt_size(n: int | float) -> str:
    """Format a byte count into a human-readable size string.

    Args:
        n: Size in bytes. Must be non-negative.

    Returns:
        Formatted size string (e.g. ``"1.5G"``, ``"3.2T"``, ``"7.0E"``).

    Raises:
        ValueError: If *n* is negative.
    """
    if n < 0:
        raise ValueError("Size cannot be negative")
    for unit in ("B", "K", "M", "G", "T", "P", "E"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}E"
