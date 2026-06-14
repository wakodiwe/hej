"""Progress display utilities using Rich."""

import json
import logging
from contextlib import contextmanager

import click
import requests
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from hej.api import api_error

logger = logging.getLogger(__name__)


@contextmanager
def loading(message: str = "Processing..."):
    """Show a spinner while a task is running.

    Args:
        message: Description text to display next to the spinner.
    """
    from rich.text import Text

    class PlainTimeColumn(TimeElapsedColumn):
        """A time column that does not show a spinner prefix."""

        def render(self, task):
            """Render elapsed time without spinner prefix."""
            elapsed = task.finished_time if task.finished else task.elapsed
            if elapsed is None:
                return Text("0.0s")
            return Text(f"- {elapsed:.1f}s")

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        PlainTimeColumn(),
        transient=True,
    )
    with progress:
        progress.add_task(description=message, total=None)
        yield


@contextmanager
def wake_progress(model: str):
    """Show a loading indicator while waking a model.

    Displays ``<spinner> Waking <model> <elapsed>`` while loading,
    then clears when the context exits.
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    )
    with progress:
        progress.add_task(description=f"Waking {model}", total=None)
        yield


def stream_operation(
    endpoint: str,
    model: str,
    host: str,
    timeout: int,
    verb: str = "Processing",
    payload: dict | None = None,
) -> None:
    """POST to *endpoint* with streaming, showing a Rich progress bar.

    Iterates JSON lines from the response. Lines with a ``"digest"`` key
    drive a download-style progress bar.  All other lines are printed as
    status text via ``click.echo``.

    If *payload* is ``None``, defaults to ``{"model": model}``.

    Args:
        endpoint: API endpoint path (e.g. ``"/api/pull"``).
        model: Model name.
        host: Ollama server URL.
        timeout: Request timeout in seconds.
        verb: Action verb for display (e.g. ``"Pulling"``, ``"Pushing"``).
        payload: Optional POST payload; defaults to ``{"model": model}``.

    Raises:
        requests.RequestException: On HTTP or connection errors.
    """
    if payload is None:
        payload = {"model": model}
    try:
        with requests.post(
            f"{host}{endpoint}", json=payload, stream=True, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                transient=True,
            )
            task_id = None
            with progress:
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("skipping malformed line: %r", line)
                        continue
                    status = data.get("status", "")
                    if "digest" in data:
                        total = data.get("total", 0)
                        completed = data.get("completed", 0)
                        if task_id is None:
                            task_id = progress.add_task(f"{verb} {model}", total=total)
                        progress.update(task_id, completed=completed)
                        if completed >= total and total > 0:
                            progress.update(task_id, completed=total)
                    else:
                        if status:
                            click.echo(status)
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
