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
from typing import Any

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
    """Prepend ``http://`` to *val* if no scheme is present.

    Strips trailing slashes and validates the result is a well-formed
    URL with a hostname.  Returns the validated URL or raises
    ``ValueError`` if the input is clearly invalid.
    """
    if not val:
        return val
    val = val.rstrip("/")
    if not val.startswith(("http://", "https://")):
        val = f"http://{val}"
    parts = val.partition("://")
    host_part = parts[2] if parts[0] in ("http", "https") else parts[0]
    if not host_part or " " in host_part:
        raise ValueError(f"Invalid host URL: {val}")
    return val


def _parse_duration(val: str) -> int | None:
    """Parse a timeout string into seconds, or None if invalid."""
    try:
        return int(val)
    except ValueError:
        return None


def _find_config() -> Path | None:
    """Return the config file path if it exists, or ``None``."""
    return CONFIG_PATH if CONFIG_PATH.exists() else None


def _validate(cfg: dict[str, Any]) -> dict[str, Any]:
    """Validate and coerce config values, logging warnings for bad entries."""
    if not isinstance(cfg.get("timeout"), (int, float)) or cfg["timeout"] <= 0:
        logger.warning("Invalid timeout %r, resetting to default %s", cfg.get("timeout"), DEFAULTS["timeout"])
        cfg["timeout"] = DEFAULTS["timeout"]
    if not isinstance(cfg.get("host"), str) or not cfg["host"]:
        logger.warning("Invalid host %r, resetting to default %s", cfg.get("host"), DEFAULTS["host"])
        cfg["host"] = DEFAULTS["host"]
    return cfg


def load() -> dict[str, Any]:
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
            try:
                config[key] = _resolve_host(val)
            except ValueError:
                logger.debug("Invalid %s value %r, ignoring", env_var, val)
        elif key == "timeout":
            parsed = _parse_duration(val)
            if parsed is not None:
                config[key] = parsed
            else:
                logger.debug("Invalid %s value %r, ignoring", env_var, val)
        elif key in ("streaming", "stats"):
            config[key] = val.lower() in ("1", "true", "yes")
        else:
            config[key] = val

    return _validate(config)
