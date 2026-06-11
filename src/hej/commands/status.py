"""status command"""

import logging

import click

from .. import CONTEXT_SETTINGS, config
from ..api import isrunning

logger = logging.getLogger(__name__)


@click.command("status", context_settings=CONTEXT_SETTINGS)
@click.option("--host", help="Ollama server URL")
def cmd(host):
    """Show Ollama server information"""
    logger.debug(f"{__name__} called")

    cfg = config.load()
    host = host or cfg["host"]

    if isrunning(host):
        click.echo("Ollama server is running")
    else:
        click.echo("Ollama server is not running")
