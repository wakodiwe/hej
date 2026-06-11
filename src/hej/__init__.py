"""hej — a lightweight CLI for sending prompts to Ollama."""

from __future__ import annotations

import importlib.metadata

VERSION: str = importlib.metadata.version("hej")

CONTEXT_SETTINGS: dict = {"help_option_names": ["-h", "--help"]}
