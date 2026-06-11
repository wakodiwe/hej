"""Configuration loading from TOML and environment variables.

Precedence (highest to lowest):
    1. CLI flags (applied by each command)
    2. Environment variables (OLLAMA_*)
    3. Config file (``~/.config/hej/config.toml``)
    4. Hard-coded defaults
"""

from __future__ import annotations

import logging
import os
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULTS = {
    "default_model": "phi3",
    "host": "http://localhost:11434",
    "timeout": 600,
    "streaming": False,
    "keep_alive": None,
    "stats": True,
}

ENV_MAP: dict[str, str] = {
    "host": "OLLAMA_HOST",
    "keep_alive": "OLLAMA_KEEP_ALIVE",
    "timeout": "OLLAMA_LOAD_TIMEOUT",
    "default_model": "HEJ_DEFAULT_MODEL",
    "streaming": "HEJ_STREAMING",
    "stats": "HEJ_STATS",
}

XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = XDG_CONFIG_HOME / "hej"
CONFIG_PATH = CONFIG_DIR / "config.toml"


def _resolve_host(val: str) -> str:
    """Prepend ``http://`` to *val* if no scheme is present."""
    if val and not val.startswith(("http://", "https://")):
        return f"http://{val}"
    return val


_DURATION_UNITS = {"s": 1, "m": 60, "h": 3600}


def _parse_duration(val: str) -> int | None:
    """Parse a duration string (e.g. ``5m``, ``2m0s``, ``1h``) into seconds.

    Returns:
        Integer seconds, or ``None`` if the string cannot be parsed.
    """
    import re

    total = 0
    for match in re.finditer(r"(\d+)([smh])", val):
        try:
            total += int(match.group(1)) * _DURATION_UNITS[match.group(2)]
        except (ValueError, KeyError):
            return None
    if total == 0:
        try:
            return int(val)
        except ValueError:
            return None
    return total


def _find_config() -> Path | None:
    """Return the first existing config file from XDG paths, or ``None``."""
    candidates = [CONFIG_PATH]
    for p in candidates:
        if p.exists():
            return p
    return None


def load() -> dict:
    """Load configuration with precedence: defaults → config → env vars.

    Returns:
        Configuration dict with all :data:`DEFAULTS` keys present.
    """
    config = DEFAULTS.copy()

    config_path = _find_config()
    if config_path is not None:
        try:
            with open(config_path, "rb") as f:
                config.update(tomllib.load(f))
        except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
            logger.warning("Failed to load config: %s, using defaults", e)

    for key, env_var in ENV_MAP.items():
        val = os.environ.get(env_var)
        if val is None:
            continue
        if key == "host":
            config[key] = _resolve_host(val)
        elif key == "timeout":
            parsed = _parse_duration(val)
            if parsed is not None:
                config[key] = parsed
            else:
                logger.warning("Invalid %s value %r, ignoring", env_var, val)
        elif key in ("streaming", "stats"):
            config[key] = val.lower() in ("1", "true", "yes")
        else:
            config[key] = val

    return config
