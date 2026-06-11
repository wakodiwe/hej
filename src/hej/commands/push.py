"""push command"""

import logging

import click

from hej import CONTEXT_SETTINGS, config
from hej.progress import stream_operation

logger = logging.getLogger(__name__)


@click.command("push", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--host", help="Ollama server URL")
def cmd(model, host):
    """Upload a model"""
    cfg = config.load()
    host = host or cfg["host"]
    stream_operation("/api/push", model, host, cfg["timeout"], verb="pushing")
