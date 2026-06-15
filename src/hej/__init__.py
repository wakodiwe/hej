"""hej — a lightweight CLI for sending prompts to Ollama."""

from __future__ import annotations

CONTEXT_SETTINGS: dict = {"help_option_names": ["-h", "--help"]}


def __getattr__(name: str) -> str:
    if name == "VERSION":
        import importlib.metadata

        return importlib.metadata.version("hej")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
