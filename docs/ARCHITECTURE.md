# Architecture

## Overview

hej is a CLI client for Ollama's HTTP API, organized as a Click-based multi-command application.

## Layer Diagram

```
CLI (cli.py)
  ├── Config (config.py)     ← TOML + env vars
  ├── Logging (log.py)       ← ANSI-colored output
  ├── Commands (commands/)   ← 15 @click.command/@click.group modules
  │     └── Progress (progress.py)  ← Rich progress bars
  └── API (api.py)           ← Ollama HTTP client (requests)
        └── Ollama server    ← http://localhost:11434
```

## Data Flow

1. `hej run "prompt"` → `cli.py` → `commands/run.py`
2. `run.py` reads config, calls `api.generate()`
3. `api.py` POSTs to Ollama `/api/generate`
4. Response streamed back, displayed via Rich spinner or progress bar
5. Stats shown (duration, tokens, speed) if `stats=true`

## Key Design Decisions

- **No global state**: Config loaded fresh per command in `invoke` callback
- **Lazy config**: `cli.py` loads config on first access, not at import time
- **Mocking pattern**: Tests patch the importer module, never the origin
- **Single version source**: `pyproject.toml` → read via `importlib.metadata`
- **Streaming**: Two modes — token-by-token (run/chat) and progress bar (pull/push/create)

## Configuration Precedence

CLI flags > Environment vars > config.toml > Hard-coded defaults
