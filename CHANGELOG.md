# Changelog

## 1.0.0 (2026-06-15)

- Error handling: replaced bare `except Exception:` with specific types in API client
- Validation: datetime parsing in `fmt_date()` now returns empty string on invalid input
- Type safety: enabled strict mypy (`disallow_untyped_defs = true`), added type hints to all modules
- SSRF protection: `_resolve_host()` validates URL format and rejects malformed hosts
- Config validation: new `_validate()` checks timeout/host values, resets bad entries to defaults
- Logging: added JSON output mode (`--json-logs`) via `_JsonFormatter`
- Dependencies: tightened version bounds in `pyproject.toml`
- Tests: added edge case coverage for `fmt_date()` invalid dates, `fmt_size(0)`, config validation

## 0.1.0 (2026-06-11)

- Project infrastructure (CI, build config, ignores, license)
- Core package: config loading (TOML + env vars), logging (ANSI colors), utilities
- API client with Ollama HTTP wrapper (generate, streaming, model management)
- CLI boilerplate with Click, 13 subcommands
- Commands: chat, config, cp, create, ls, ps, pull, push, rm, run, show, status, stop
- Rich progress indicators for streaming operations (pull, push, create)
- Full test suite: unit tests, API error handling, CLI integration
- API documentation via pdoc
