"""CLI root group and entry point."""

import logging
import sys

import click

from . import CONTEXT_SETTINGS, VERSION, log
from .commands import register_commands

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option("-q", "--quiet", is_flag=True, help="Only show errors")
@click.option( "-v", "--verbose", count=True, help="Increase verbosity (-v info, -vv debug)")
@click.option("--no-color", is_flag=True, default=False, help="Disable coloured output")
@click.version_option(message="%(version)s", version=VERSION)
@click.pass_context
def cli(ctx: click.Context, verbose: int, quiet: bool, no_color: bool) -> None:
    """hej — A lightweight CLI for sending prompts to Ollama."""

    log.setup(verbosity=verbose, quiet=quiet, color=not no_color)
    logger.debug("CLI initialized with verbose=%d, quiet=%s", verbose, quiet)

    if ctx.invoked_subcommand is None:
        click.echo("hej")
        ctx.exit()

    ctx.ensure_object(dict)


register_commands(cli)


def main() -> None:
    """Console-script entry point."""
    logger.debug("starting %s", sys.argv[0])
    cli(obj={})


if __name__ == "__main__":
    main()
