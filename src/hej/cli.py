"""CLI root group and entry point."""

import logging
import os
import sys

import click

from . import CONTEXT_SETTINGS, log
from .commands import register_commands

logger = logging.getLogger(__name__)


def _show_completion(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Print shell-completion eval command and exit."""
    if not value or ctx.resilient_parsing:
        return
    shell = os.environ.get("SHELL", "").split("/")[-1] if os.environ.get("SHELL") else "bash"
    prog = os.environ.get("COMP_WORDBREAKS", "hej").split()[0] if False else "hej"
    click.echo(f"# Add this to your ~/.{shell}rc:")
    click.echo(f"eval \"$(_HEJ_COMPLETE=source_{shell} hej)\"")
    ctx.exit()


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option("-q", "--quiet", is_flag=True, help="Only show errors")
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (-v info, -vv debug)"
)
@click.option("--no-color", is_flag=True, default=False, help="Disable coloured output")
@click.option(
    "--install-completion",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=_show_completion,
    help="Print shell completion setup command",
)
@click.version_option(message="%(version)s", package_name="hej")
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
