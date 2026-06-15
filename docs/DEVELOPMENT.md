# Development Guide

## Getting Started

```sh
make devinstall
source venv/bin/activate
```

This creates a virtual environment and installs hej in editable mode with test and docs dependencies.

## Project Layout

```
src/hej/           # Package source
  cli.py           # CLI entry point
  api.py           # Ollama HTTP client
  config.py        # Configuration (TOML + env vars)
  log.py           # Logging setup
  utils.py         # Date/size formatting
  progress.py      # Rich progress bars
  commands/        # 13 CLI subcommands
tests/             # Test suite
docs/api/          # pdoc-generated API docs
```

## Adding a Command

1. Create `src/hej/commands/<name>.py` with a `cmd` function decorated with `@click.command`
2. Register it in `src/hej/commands/__init__.py` via `register_commands(cli)`
3. Add tests in `tests/`
4. Regenerate docs with `make docs`

## Testing

```sh
make tests              # run all
venv/bin/pytest -q -k test_generate      # single test
```

- Unit tests mock at the importing module, never the origin.
- Integration tests use `@responses.activate` for HTTP mocking.
- No live Ollama required.

## Code Quality

```sh
make check              # lint + type-check
make lint               # auto-format
make coverage           # coverage report
make all-checks         # everything
```

## Documentation

```sh
make docs               # regenerate API docs
```

## Releasing

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit and tag: `git tag v1.0.0`
4. Push: `git push origin main --tags`
