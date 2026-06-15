"""stop command"""

import logging

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error

logger = logging.getLogger(__name__)


@click.command("stop", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--host", help="Ollama server URL")
def cmd(model: str, host: str | None = None) -> None:
    """Stop a running model"""
    import requests

    cfg = config.load()
    host = host or cfg["host"]

    logger.debug("stop %s", model)

    try:
        resp = requests.post(
            f"{host}/api/generate",
            json={"model": model, "keep_alive": 0},
            timeout=cfg["timeout"],
        )
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
    click.echo(f"Stopped {model}")
