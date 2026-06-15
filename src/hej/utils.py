"""Date and size formatting utilities."""

from __future__ import annotations

from datetime import datetime


def fmt_date(s: str, format_type: str = "datetime") -> str:
    dt = datetime.fromisoformat(s)
    _date = dt.strftime("%d.%m.%y")
    _time = dt.strftime("%I:%M")
    if format_type == "datetime":
        return f"{_date}, {_time}"
    if format_type == "date":
        return _date
    if format_type == "time":
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
