"""Date and size formatting utilities."""

from __future__ import annotations

import logging
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime

logger = logging.getLogger(__name__)


def copy_to_clipboard(text: str) -> bool:
    """Copy *text* to the system clipboard.

    Tries common clipboard tools in order: xclip, xsel, wl-copy, pbcopy.

    Returns:
        True if the copy succeeded.
    """
    for cmd in (
        ["xclip", "-selection", "clipboard"],
        ["xsel", "-i", "-b"],
        ["wl-copy"],
        ["pbcopy"],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text, text=True, check=True)
                return True
            except subprocess.CalledProcessError:
                continue
    logger.warning("No clipboard tool found (install xclip, xsel, wl-copy, or pbcopy)")
    return False


def open_in_editor(text: str, suffix: str = ".txt") -> bool:
    """Open *text* in the user's default editor.

    Writes to a temp file, opens it, and waits for the editor to exit.
    Uses ``$EDITOR`` or ``$VISUAL``, falling back to ``xdg-open`` / ``open``.

    Returns:
        True if the editor was launched.
    """
    import tempfile

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        for fallback in ("xdg-open", "open"):
            if shutil.which(fallback):
                editor = fallback
                break
    if not editor:
        logger.warning("No editor found (set $EDITOR)")
        return False

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False
    ) as f:
        f.write(text)
        tmp_path = f.name

    try:
        subprocess.call(shlex.split(editor) + [tmp_path])
    except Exception:
        logger.exception("Failed to open editor")
        return False
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return True


def fmt_date(s: str, format_type: str = "datetime") -> str:
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        logger.warning("invalid date string: %r", s)
        return ""
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
