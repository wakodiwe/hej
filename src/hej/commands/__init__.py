"""Click command modules and registration."""

from __future__ import annotations

import click

from . import chat, config, cp, create, ls, ps, pull, push, rm, run, show, status, stop


def register_commands(cli: click.Group) -> None:
    """Register all subcommands with the CLI group.

    Args:
        cli: The root Click group.
    """
    cli.add_command(chat.cmd)
    cli.add_command(config.cmd)
    cli.add_command(cp.cmd)
    cli.add_command(create.cmd)
    cli.add_command(ls.cmd)
    cli.add_command(ps.cmd)
    cli.add_command(pull.cmd)
    cli.add_command(push.cmd)
    cli.add_command(rm.cmd)
    cli.add_command(run.cmd)
    cli.add_command(show.cmd)
    cli.add_command(status.cmd)
    cli.add_command(stop.cmd)
