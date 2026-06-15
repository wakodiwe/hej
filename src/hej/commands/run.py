"""Execute a single prompt against an Ollama model.

Dispatches to either streaming or single-response mode based on
config/CLI flags.  Handles server health check, model wake-up
indicator, and timing stats display.

Examples:
    hej run "hello world"
    hej run -m llama3 "explain quantum physics"
    hej run --stream "write a poem"
    hej run --no-stats "quick question"

Raises:
    SystemExit: If the Ollama server is not reachable.
"""

import logging

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import generate, generate_stream, isrunning, print_stats
from hej.progress import wake_progress

logger = logging.getLogger(__name__)


def _run_streaming(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
    stats: bool = True,
    keep_alive: int | str | None = None,
) -> None:
    """Stream tokens from the API."""
    stream = generate_stream(model, prompt, host, timeout, keep_alive=keep_alive)

    metadata: dict = {}

    with wake_progress(model):
        try:
            kind, value = next(stream)
        except StopIteration:
            return

    for kind, value in stream:
        if kind == "token":
            click.echo(value, nl=False)
        elif kind == "stats":
            assert isinstance(value, dict)
            metadata = value

    click.echo()
    if stats:
        print_stats(metadata)


def _run_single(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
    stats: bool = True,
    keep_alive: int | str | None = None,
) -> None:
    """Fetch the full response at once (no streaming)."""
    with wake_progress(model):
        response, metadata = generate(
            model, prompt, host, timeout, keep_alive=keep_alive
        )
    click.echo(response)
    if stats:
        print_stats(metadata)


@click.command("run", context_settings=CONTEXT_SETTINGS)
@click.argument("prompt")
@click.option("--host", help="Ollama server URL")
@click.option("-m", "--model", help="Model name")
@click.option("-t", "--template", "template_name", help="Prompt template name")
@click.option("--stream/--no-stream", default=None, help="Stream output")
@click.option("--stats/--no-stats", default=None, help="Show timing stats")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--keep-alive", type=int, help="Keep model loaded N seconds (0 = unload)")
def cmd(
    prompt: str,
    model: str | None = None,
    template_name: str | None = None,
    host: str | None = None,
    stream: bool | None = None,
    stats: bool | None = None,
    timeout: int | None = None,
    keep_alive: int | None = None,
) -> None:
    """Run a model"""
    from hej.commands.template import apply_template, load_template

    logger.debug("run.cmd(%r, model=%r)", prompt, model)

    cfg = config.load()
    host = host or cfg["host"]
    streaming = stream if stream is not None else cfg["streaming"]
    timeout = timeout or cfg["timeout"]
    model = model or cfg["default_model"]
    keep_alive = keep_alive if keep_alive is not None else cfg["keep_alive"]
    stats = stats if stats is not None else cfg["stats"]

    if template_name:
        tmpl = load_template(template_name)
        if tmpl is None:
            click.echo(f"Template '{template_name}' not found", err=True)
            raise SystemExit(1)
        prompt = apply_template(tmpl, prompt)

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    if streaming:
        _run_streaming(model, prompt, host, timeout, stats=stats, keep_alive=keep_alive)
    else:
        _run_single(model, prompt, host, timeout, stats=stats, keep_alive=keep_alive)
