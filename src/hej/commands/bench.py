"""Benchmark model performance."""

from __future__ import annotations

import logging

import statistics
import time
from typing import Any

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import generate, isrunning

logger = logging.getLogger(__name__)


def _bench_run(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
) -> dict[str, Any]:
    start = time.perf_counter()
    response, metadata = generate(model, prompt, host, timeout)
    elapsed = time.perf_counter() - start
    return {
        "elapsed_s": elapsed,
        "total_duration_ns": metadata.get("total_duration_ns"),
        "eval_count": metadata.get("eval_count"),
        "response_len": len(response),
    }


@click.command("bench", context_settings=CONTEXT_SETTINGS)
@click.option(
    "-m",
    "--model",
    "models",
    multiple=True,
    help="Model name (repeat for multiple; default: config default)",
)
@click.option(
    "-p", "--prompt", default="hello", show_default=True, help="Benchmark prompt"
)
@click.option(
    "--runs", type=int, default=3, show_default=True, help="Number of runs per model"
)
@click.option("--host", help="Ollama server URL")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--output", type=click.Path(), help="Write results as CSV")
def cmd(
    models: tuple[str, ...],
    prompt: str,
    runs: int,
    host: str | None,
    timeout: int | None,
    output: str | None,
) -> None:
    """Benchmark model latency and throughput.

    Runs a prompt multiple times and reports mean/median/stdev timing.

    Examples:
        hej bench -m phi3 --runs 5 -p "hello world"
        hej bench -m phi3 -m llama3 --runs 3 --output results.csv
    """
    cfg = config.load()
    host = host or cfg["host"]
    timeout = timeout or cfg["timeout"]

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    if not models:
        models = (cfg["default_model"],)

    logger.debug("bench models=%s runs=%d prompt=%r", models, runs, prompt)
    all_results: list[dict[str, Any]] = []

    for model in models:
        click.echo(f"Benchmarking {model}... ", nl=False)
        timings: list[float] = []
        for i in range(runs):
            result = _bench_run(model, prompt, host, timeout)
            timings.append(result["elapsed_s"])
            result["model"] = model
            result["run"] = i + 1
            all_results.append(result)
        click.echo("done")

        mean = statistics.mean(timings)
        stdev = statistics.stdev(timings) if len(timings) > 1 else 0.0
        median = statistics.median(timings)
        click.echo(f"  Mean:   {mean:.3f}s")
        click.echo(f"  Median: {median:.3f}s")
        click.echo(f"  Stdev:  {stdev:.3f}s")
        click.echo(f"  Fastest: {min(timings):.3f}s")
        click.echo(f"  Slowest: {max(timings):.3f}s")

    if output:
        import csv

        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "model",
                    "run",
                    "elapsed_s",
                    "eval_count",
                    "total_duration_ns",
                    "response_len",
                ],
            )
            writer.writeheader()
            writer.writerows(all_results)
        click.echo(f"Results written to {output}")
