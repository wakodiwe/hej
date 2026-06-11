"""pull command"""

import logging

logger = logging.getLogger(__name__)

import click

from hej import CONTEXT_SETTINGS, config
from hej.progress import stream_operation


@click.command("pull", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--host", help="Ollama server URL")
def cmd(model, host):
    """Download a model"""
    cfg = config.load()
    host = host or cfg["host"]
    stream_operation("/api/pull", model, host, cfg["timeout"], verb="pulling")
