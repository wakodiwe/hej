"""ls (list) command"""

import logging

import click
import requests
from rich import box
from rich.console import Console
from rich.table import Table

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error
from hej.utils import fmt_date, fmt_size

logger = logging.getLogger(__name__)


@click.command("ls", context_settings=CONTEXT_SETTINGS)
@click.option("--host", help="Ollama server URL")
@click.option("--timeout", type=int, help="Request timeout in seconds")
def cmd(host: str | None = None, timeout: int | None = None) -> None:
    """List Ollama models."""

    logger.debug(__name__)

    cfg = config.load()
    host = host or cfg["host"]
    timeout = timeout or cfg["timeout"]

    try:
        r = requests.get(f"{host}/api/tags", timeout=timeout)
        r.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
    models = r.json().get("models", [])

    if not models:
        click.echo("No models installed")
        return

    console = Console()
    table = Table(
        box=box.SIMPLE,
        pad_edge=False,
        show_edge=False,
        header_style="",
    )

    table.add_column("NAME")
    table.add_column("ID")
    table.add_column("SIZE", justify="right")
    table.add_column("MODIFIED", justify="right")

    for m in models:
        name = m["name"][0:30]
        id = m["digest"][0:12]
        modified = fmt_date(m["modified_at"])
        size = fmt_size(m["size"])

        table.add_row(name, id, size, modified)

    console.print(table)
