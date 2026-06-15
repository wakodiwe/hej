"""Batch process multiple prompts against an Ollama model."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import generate, isrunning

logger = __import__("logging").getLogger(__name__)


def _process_prompt(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
) -> dict[str, Any]:
    """Process a single prompt and return result with metadata."""
    start = time.perf_counter()
    response = generate(model, prompt, host, timeout)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {
        "prompt": prompt,
        "response": response,
        "model": model,
        "elapsed_ms": elapsed_ms,
    }


@click.command("batch", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--input",
    "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input file (one prompt per line)",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file (JSONL). Default: stdout",
)
@click.option("-m", "--model", help="Model name")
@click.option("--host", help="Ollama server URL")
@click.option(
    "--concurrency", "-c", type=int, default=1, help="Number of parallel requests"
)
@click.option("--timeout", type=int, help="Request timeout in seconds")
def cmd(
    input_file: str,
    output_file: str | None,
    model: str | None,
    host: str | None,
    concurrency: int,
    timeout: int | None,
) -> None:
    """Run multiple prompts from a file and save results.

    Input: one prompt per line. Output: JSONL (one JSON object per line).

    Examples:
        hej batch -i prompts.txt -o results.jsonl
        hej batch -i prompts.txt -c 4 -m llama3
    """
    cfg = config.load()
    host = host or cfg["host"]
    model = model or cfg["default_model"]
    timeout = timeout or cfg["timeout"]

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    prompts = [
        line.strip()
        for line in Path(input_file).read_text().splitlines()
        if line.strip()
    ]
    if not prompts:
        click.echo("Error: No prompts found in input file", err=True)
        raise SystemExit(1)

    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_process_prompt, model, p, host, timeout): p
            for p in prompts
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                click.echo(json.dumps(result))
            except Exception as e:
                prompt = futures[future]
                error_result = {
                    "prompt": prompt,
                    "error": str(e),
                    "model": model,
                }
                results.append(error_result)
                click.echo(json.dumps(error_result), err=True)

    if output_file:
        with open(output_file, "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        click.echo(f"Wrote {len(results)} results to {output_file}")
