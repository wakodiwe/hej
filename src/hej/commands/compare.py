"""Compare responses across multiple models."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from hej import CONTEXT_SETTINGS, config
from hej.api import generate, isrunning

logger = logging.getLogger(__name__)


def _query_model(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
) -> dict[str, Any]:
    start = time.perf_counter()
    response, _metadata = generate(model, prompt, host, timeout)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {"model": model, "response": response, "elapsed_ms": elapsed_ms}


@click.command("compare", context_settings=CONTEXT_SETTINGS)
@click.argument("prompt")
@click.option(
    "-m",
    "--model",
    "models",
    multiple=True,
    required=True,
    help="Model name (repeat for multiple)",
)
@click.option("--host", help="Ollama server URL")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def cmd(
    prompt: str,
    models: tuple[str, ...],
    host: str | None,
    timeout: int | None,
    format: str,
) -> None:
    """Run the same prompt across multiple models and compare results.

    Examples:
        hej compare "who invented calculus?" -m phi3 -m llama3
        hej compare "hello" -m model1 -m model2 --format json
    """
    cfg = config.load()
    host = host or cfg["host"]
    timeout = timeout or cfg["timeout"]

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    logger.debug("compare models=%s prompt=%r", models, prompt)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(models)) as executor:
        futures = {
            executor.submit(_query_model, model, prompt, host, timeout): model
            for model in models
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                model = futures[future]
                results.append({"model": model, "error": str(e)})

    if format == "json":
        import json

        click.echo(json.dumps(results, indent=2))
    else:
        console = Console()
        table = Table(title=f"Comparison: {prompt[:50]}...")
        table.add_column("Model", style="cyan")
        table.add_column("Response", style="white")
        table.add_column("Time (ms)", justify="right", style="yellow")
        for r in results:
            if "error" in r:
                table.add_row(r["model"], f"[red]Error: {r['error']}[/red]", "-")
            else:
                resp = r["response"]
                if len(resp) > 60:
                    resp = resp[:57] + "..."
                table.add_row(r["model"], resp, str(r.get("elapsed_ms", "?")))
        console.print(table)
