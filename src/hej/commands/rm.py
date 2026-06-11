"""rm command"""

import logging

logger = logging.getLogger(__name__)

import click
import requests

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error


@click.command("rm", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option("--host", help="Ollama server URL")
def cmd(model, force, host):
    """Delete a model"""
    cfg = config.load()
    host = host or cfg["host"]

    if not force:
        click.confirm(f"Delete {model}?", abort=True)

    try:
        resp = requests.delete(
            f"{host}/api/delete", json={"model": model}, timeout=cfg["timeout"]
        )
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
    click.echo(f"Deleted {model}")
