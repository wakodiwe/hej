# hej

A lightweight CLI for interacting with [ollama](https://ollama.ai).

![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-Unlicense-green)

```
┌────────────────────────────────┐
│  Calvin:  "I made a program!"  │
│  Hobbes:  "What does it do?"   │
│                                │
│  $ hej                         │
│  hej                           │
│                                │
│  Calvin:  "Exactly."           │
└────────────────────────────────┘
```

## Overview

**hej** is a personal productivity tool designed to simplify interactions with locally-running Ollama models through a clean command-line interface. This Python-based CLI provides:

- **Prompt Execution**: Send prompts and get streaming model responses with real-time token output
- **Model Management**: List, download, upload, copy, and delete models  
- **Server Control**: Check server status, list running models, and stop models
- **Interactive Chat**: Built-in chat mode for multi-turn conversations
- **Flexible Configuration**: Customizable via `config.toml` (model, host, timeout)
- **Streaming Display**: Token-by-token output with a loading spinner and progress indicator

The project is organized into core modules (CLI entry point, logging, configuration, Ollama HTTP client), 10+ subcommands, and includes a test suite using pytest. It's written almost entirely in Python (99.1%) with a Makefile component, released under the Unlicense (public domain).

## Installation

```sh
# Clone repository
git clone https://github.com/wakodiwe/hej

```
```sh
# Create virtual environment
cd hej
python3 -m venv venv
source venv/bin/activate
```

```sh
# Install hej into venv
pip install -e
```

```sh
# Or for development with tests
pip install -e ".[tests]"
```

## Configuration

Config file at `~/.config/hej/config.toml` or `$XDG_CONFIG_HOME/hej/config.toml`.
Run `hej config --help` for more information.

```toml
default_model = "phi3"
host = "http://localhost:11434"
timeout = 600
streaming = false
stats = true
```

All keys are optional. Precedence (highest to lowest):

| Priority | Source              |
|----------|---------------------|
| 1        | CLI flags           |
| 2        | Environment vars    |
| 3        | Config file         |
| 4        | Hard-coded defaults |

| Config key       | Default                  | Env var               |
|------------------|--------------------------|-----------------------|
| `default_model`  | `phi3`                   | `HEJ_DEFAULT_MODEL`   |
| `host`           | `http://localhost:11434` | `OLLAMA_HOST`         |
| `timeout`        | `600`                    | `OLLAMA_LOAD_TIMEOUT` |
| `streaming`      | `false`                  | `HEJ_STREAMING`       |
| `stats`          | `true`                   | `HEJ_STATS`           |
| `keep_alive`     | `-`                      | `OLLAMA_KEEP_ALIVE`   |

Invalid config values (e.g. malformed TOML, negative timeout, empty host) log a warning and fall back to the hard-coded default.

Structured JSON logging is available via the `--json-logs` flag to `hej`:

```
hej --json-logs run "hello"
# → {"time": "...", "level": "WARNING", "name": "hej.config", "message": "..."}
```

## Usage

```
hej --help                             # Show help
hej status                             # Check if ollama server is running
hej config                             # Print sample config to stdout
hej config --help                      # Show help for config command
hej config -w                          # Write config to ~/.config/hej/config.toml
hej run "hello"                        # Send prompt (uses default model from config)
hej run -m smollm:135m "hello"         # Override model
hej ls                                 # List installed models
hej ps                                 # List running models
hej show phi3                          # Show model info
hej show phi3 --full                   # Show license, modelfile, template, and parameters
hej show phi3 --json                   # Raw JSON output
hej pull phi3                          # Download a model
hej push phi3                          # Upload a model
hej create mymodel --from-model phi3   # Create a model
hej cp phi3 phi3-copy                  # Copy a model
hej rm phi3                            # Delete a model (confirms)
hej rm phi3 -f                         # Delete without confirming
hej stop phi3                          # Stop a running model
hej chat                               # Interactive chat (type 'exit' to quit)
```

## Tests

```sh
pytest -q                    # run all tests
pytest -q tests/test_api.py  # run a single module
pytest -q -k test_generate   # run a specific test
```

Unit tests use `unittest.mock.patch` patching at the importer module.
Integration tests use `responses.activate` for HTTP-level mocking.
No live ollama server needed.
