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
  commands/        # 18 CLI subcommands
tests/             # Test suite
docs/api/          # pdoc-generated API docs
```

## Adding a Command

1. Create `src/hej/commands/<name>.py` with a `cmd` decorated with `@click.command` (leaf) or `@click.group` (subcommand group)
2. Register it in `src/hej/commands/__init__.py` by adding the name to the list in `register_commands()`
3. Add logging where useful (info, warn, error)
4. Add tests in `tests/`
5. Regenerate docs with `make docs`

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

1. Update `README.md`
2. Update `CHANGELOG.md`
3. Update `docs/DEVELOPMENT.md`
4. Update `docs/ARCHITECTURE.md`
5. Regenerate API docs:

```sh
make docs               
```
## Normal update
1. See docs/DEVELOPMENT.md if anything missing
2. Stage and commit changed files

## Releasing
1. Update version in `pyproject.toml`
   - small updates x.x.+1
   - medium updates x.+1.0
   - huge updates +1.0.0
2. Commit and tag: `git tag v1.0.0`
3. Push: `git push origin main --tags`
