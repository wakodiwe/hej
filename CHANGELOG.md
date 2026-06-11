# Changelog

## 0.1.0 (2026-06-11)

- Project infrastructure (CI, build config, ignores, license)
- Core package: config loading (TOML + env vars), logging (ANSI colors), utilities
- API client with Ollama HTTP wrapper (generate, streaming, model management)
- CLI boilerplate with Click, 13 subcommands
- Commands: chat, config, cp, create, ls, ps, pull, push, rm, run, show, status, stop
- Rich progress indicators for streaming operations (pull, push, create)
- Full test suite: unit tests, API error handling, CLI integration
- API documentation via pdoc
