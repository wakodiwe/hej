"""run command"""

import logging

logger = logging.getLogger(__name__)

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import generate, generate_stream, isrunning, print_stats
from hej.progress import loading


def _run_streaming(model, prompt, host, timeout, stats=True, keep_alive=None):
    """Stream tokens from the API."""
    stream = generate_stream(model, prompt, host, timeout, keep_alive=keep_alive)

    first = True
    metadata = {}

    with loading("..."):
        for kind, value in stream:
            if kind == "loading":
                pass
            elif kind == "token":
                if first:
                    click.echo(value, nl=False)
                    first = False
                else:
                    click.echo(value, nl=False)
            elif kind == "stats":
                metadata = value

    load_duration = metadata.get("load_duration", 0)
    if load_duration > 0:
        click.echo("")
        click.echo("Model is up and working ...")
    click.echo()
    if stats:
        print_stats(metadata)


def _run_single(model, prompt, host, timeout, stats=True, keep_alive=None):
    """Fetch the full response at once (no streaming)."""
    with loading("Generating response"):
        response, metadata = generate(model, prompt, host, timeout, keep_alive=keep_alive)
    click.echo(response)
    if stats:
        print_stats(metadata)


@click.command("run", context_settings=CONTEXT_SETTINGS)
@click.argument("prompt")
@click.option("--host", help="Ollama server URL")
@click.option("-m", "--model", help="Model name")
@click.option("--stream/--no-stream", default=None, help="Stream output")
@click.option("--stats/--no-stats", default=None, help="Show timing stats")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--keep-alive", type=int, help="Keep model loaded N seconds (0 = unload)")
def cmd(prompt, model, host, stream, stats, timeout, keep_alive):
    """Run a model"""
    logger.debug("run.cmd(%r, model=%r)", prompt, model)

    cfg = config.load()
    host = host or cfg["host"]
    streaming = stream if stream is not None else cfg["streaming"]
    timeout = timeout or cfg["timeout"]
    model = model or cfg["default_model"]
    keep_alive = keep_alive if keep_alive is not None else cfg["keep_alive"]
    stats = stats if stats is not None else cfg["stats"]

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    if streaming:
        _run_streaming(model, prompt, host, timeout, stats=stats, keep_alive=keep_alive)
    else:
        _run_single(model, prompt, host, timeout, stats=stats, keep_alive=keep_alive)
