"""Click command modules and registration."""

from __future__ import annotations

import importlib

import click


def register_commands(cli: click.Group) -> None:
    """Register all subcommands with the CLI group.

    Args:
        cli: The root Click group.
    """
    for name in [
        "chat",
        "config",
        "cp",
        "create",
        "ls",
        "ps",
        "pull",
        "push",
        "rm",
        "run",
        "show",
        "status",
        "stop",
        "batch",
        "bench",
        "compare",
        "session",
        "template",
    ]:
        mod = importlib.import_module(f".{name}", __package__)
        cli.add_command(mod.cmd)
