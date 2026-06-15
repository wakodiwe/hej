"""cp command"""

import logging

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error

logger = logging.getLogger(__name__)


@click.command("cp", context_settings=CONTEXT_SETTINGS)
@click.argument("source")
@click.argument("destination")
@click.option("--host", help="Ollama server URL")
def cmd(source: str, destination: str, host: str | None = None) -> None:
    """Copy a model"""
    import requests

    cfg = config.load()
    host = host or cfg["host"]

    logger.debug("cp %s -> %s", source, destination)

    try:
        resp = requests.post(
            f"{host}/api/copy",
            json={"source": source, "destination": destination},
            timeout=cfg["timeout"],
        )
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
    click.echo(f"Copied {source} \u2192 {destination}")
