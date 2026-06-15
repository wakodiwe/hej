"""ps command"""

import logging
from datetime import datetime

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error
from hej.utils import fmt_date, fmt_size

logger = logging.getLogger(__name__)


@click.command("ps", context_settings=CONTEXT_SETTINGS)
@click.option("--host", help="Ollama server URL")
def cmd(host: str | None = None) -> None:
    """List running models"""
    import requests
    from rich.console import Console
    from rich.table import Table

    cfg = config.load()
    host = host or cfg["host"]

    logger.debug("ps host=%s", host)

    try:
        response = requests.get(f"{host}/api/ps", timeout=cfg["timeout"])
        response.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
    models = response.json().get("models", [])

    if not models:
        click.echo("No models in memory")
        return

    table = Table(title="", box=None, pad_edge=False)
    for name in ["MODEL", "UNTIL", "CTX", "SIZE", "PROCESSOR", "ID"]:
        table.add_column(name, no_wrap=True)

    for m in models:
        parts = m["name"].split(":", 1)
        name = parts[0] if len(parts) > 0 else m["name"]
        slug = parts[1] if len(parts) > 1 else "latest"

        expires_at = f'{fmt_date(m["expires_at"])}'

        if fmt_date(m["expires_at"], "date") == fmt_date(str(datetime.today()), "date"):
            expires_at = fmt_date(m["expires_at"], "time")
        else:
            expires_at = fmt_date(m["expires_at"])

        table.add_row(
            f"{name}:{slug}"[0:35],
            expires_at,
            str(m["context_length"]),
            fmt_size(m["size"]),
            "???",
            m["digest"][0:12],
        )

    console = Console()
    console.print(table)
