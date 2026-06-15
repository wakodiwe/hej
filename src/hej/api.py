"""Ollama methods."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Iterator

import click

logger = logging.getLogger(__name__)


def api_error(e: Exception, host: str = "") -> None:
    """Print a user-facing error message and exit.

    Args:
        e: The exception that occurred.
        host: The Ollama server host URL (used in connection error messages).
    """
    import requests

    if isinstance(e, requests.ConnectionError):
        logger.error("Connection error to %s: %s", host, e)
        click.echo(f"Error: cannot connect to Ollama server at {host}", err=True)
    elif isinstance(e, requests.Timeout):
        logger.error("Request timed out: %s", e)
        click.echo("Error: request timed out", err=True)
    elif isinstance(e, requests.HTTPError):
        try:
            resp = e.response
            msg = resp.json().get("error", str(e)) if resp is not None else str(e)
        except ValueError:
            logger.exception("Failed to parse error response JSON")
            msg = str(e)
        click.echo(f"Error: {msg}", err=True)
    else:
        logger.error("Unexpected error: %s", e)
        click.echo(f"Error: {e}", err=True)
    sys.exit(1)


def print_stats(metadata: dict) -> None:
    """Print timing stats line if metadata contains eval_count.

    Args:
        metadata: Response metadata dictionary from :func:`extract_metadata`.
    """
    eval_count = metadata.get("eval_count")
    if not eval_count:
        return
    total_ns = metadata.get("total_duration_ns", 0)
    eval_ns = metadata.get("eval_duration_ns", 0)
    duration_s = total_ns / 1e9 if total_ns else 0
    speed = eval_count / (eval_ns / 1e9) if eval_ns else 0
    click.echo("")
    click.echo(
        f"Duration: {duration_s:.1f}s  |  Tokens: {eval_count}"
        f"  |  Speed: {speed:.1f} tok/s"
    )


def isrunning(host: str) -> bool:
    """Test if the ollama server at *host* is running.

    Args:
        host: Ollama server URL.

    Returns:
        True if the server responds within 5 seconds.
    """
    import requests

    try:
        requests.get(f"{host}/api/tags", timeout=5)
        return True
    except (requests.ConnectionError, requests.exceptions.InvalidURL):
        return False


def extract_metadata(data: dict) -> dict:
    """Extract timing metadata from an Ollama API response.

    Args:
        data: Raw API response dictionary.

    Returns:
        Dictionary with keys ``total_duration_ns``, ``eval_count``,
        ``eval_duration_ns``, and ``load_duration``.
    """
    return {
        "total_duration_ns": data.get("total_duration"),
        "eval_count": data.get("eval_count"),
        "eval_duration_ns": data.get("eval_duration"),
        "load_duration": data.get("load_duration", 0),
    }


def generate(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
    keep_alive: int | str | None = None,
) -> tuple[str, dict]:
    """Send a prompt to ollama and return (response_text, metadata).

    Args:
        model: Model name.
        prompt: Prompt text.
        host: Ollama server URL.
        timeout: Request timeout in seconds.
        keep_alive: Keep-alive duration or None.

    Returns:
        Tuple of (response text, metadata dict).
    """
    import requests

    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    logger.debug("POST %s/api/generate model=%s timeout=%d", host, model, timeout)
    try:
        resp = requests.post(
            f"{host}/api/generate",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
    data = resp.json()
    return data["response"], extract_metadata(data)


def generate_stream(
    model: str,
    prompt: str,
    host: str,
    timeout: int,
    keep_alive: int | str | None = None,
) -> Iterator[tuple[str, object]]:
    """Yield ("token", str) chunks, then ("stats", dict) on completion.

    First yield is ("loading", bool) indicating if model was loaded from disk.

    Args:
        model: Model name.
        prompt: Prompt text.
        host: Ollama server URL.
        timeout: Request timeout in seconds.
        keep_alive: Keep-alive duration or None.

    Yields:
        Tuples of (str, object) — see description above.
    """
    import requests

    payload: dict = {"model": model, "prompt": prompt, "stream": True}
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    logger.debug("POST %s/api/generate (stream) model=%s timeout=%d", host, model, timeout)
    try:
        with requests.post(
            f"{host}/api/generate",
            json=payload,
            stream=True,
            timeout=timeout,
        ) as resp:
            resp.raise_for_status()
            first = True
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("skipping malformed line: %r", line)
                    continue
                if first:
                    first = False
                    load_duration = data.get("load_duration", 0)
                    yield ("loading", load_duration > 0)
                token = data.get("response", "")
                if token:
                    yield ("token", token)
                if data.get("done"):
                    yield ("stats", extract_metadata(data))
                    break
    except requests.RequestException as e:
        api_error(e, host)
