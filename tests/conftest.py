"""Pytest configuration — clear OLLAMA_* env vars before each test."""

import os
import pytest

OLLAMA_ENV_VARS = [
    "OLLAMA_HOST",
    "OLLAMA_KEEP_ALIVE",
    "OLLAMA_LOAD_TIMEOUT",
    "OLLAMA_DEBUG",
    "OLLAMA_MODELS",
    "OLLAMA_NUM_PARALLEL",
    "OLLAMA_NO_CLOUD",
    "OLLAMA_NOHISTORY",
]


@pytest.fixture(autouse=True)
def _clear_ollama_env():
    """Remove OLLAMA_* env vars that would leak into tests."""
    saved = {k: os.environ.pop(k, None) for k in OLLAMA_ENV_VARS}
    yield
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
