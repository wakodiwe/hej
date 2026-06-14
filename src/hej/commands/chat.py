"""chat command"""

from __future__ import annotations

import json
import logging
from typing import Iterator

import click
import requests

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error, extract_metadata, print_stats
from hej.progress import loading

logger = logging.getLogger(__name__)

CHAT_API = "/api/chat"


def chat_stream(
    model: str, messages: list[dict[str, str]], host: str, timeout: int
) -> Iterator[str | tuple[str, dict]]:
    """Yield tokens from the chat API, streaming, return full response."""
    payload: dict = {"model": model, "messages": messages, "stream": True}
    full_response = []

    try:
        with requests.post(
            f"{host}{CHAT_API}", json=payload, stream=True, timeout=timeout
        ) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = data.get("message", {})
                content = msg.get("content", "")
                if content:
                    full_response.append(content)
                    yield content
                if data.get("done"):
                    yield ("stats", data)
                    break
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)


def chat_single(
    model: str, messages: list[dict[str, str]], host: str, timeout: int
) -> tuple[str, dict]:
    """Send chat request without streaming, return (content, metadata)."""
    payload: dict = {"model": model, "messages": messages, "stream": False}
    try:
        resp = requests.post(f"{host}{CHAT_API}", json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        content = msg.get("content", "")
        metadata = extract_metadata(data)
        return content, metadata
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)
        return "", {}


@click.command("chat", context_settings=CONTEXT_SETTINGS)
@click.option("--host", help="Ollama server URL")
@click.option("-m", "--model", help="Model name")
@click.option("--stream/--no-stream", default=None, help="Stream output")
@click.option("--stats/--no-stats", default=None, help="Show timing stats")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--reset", is_flag=True, help="Clear chat history")
def cmd(host, model, stream, stats, timeout, reset):
    """Interactive multi-turn chat"""
    from hej.api import isrunning

    cfg = config.load()
    host = host or cfg["host"]
    streaming = stream if stream is not None else cfg["streaming"]
    timeout = timeout or cfg["timeout"]
    model = model or cfg["default_model"]
    stats = stats if stats is not None else cfg["stats"]

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    messages = []

    if reset:
        click.echo("Chat history cleared.")
        return

    click.echo(
        f"Chat mode (model: {model}). Type 'exit' to quit, 'reset' to clear history."
    )
    click.echo("---")

    while True:
        try:
            from prompt_toolkit import prompt
            user_input = prompt("\n> ", vi_mode=True)
            # user_input = input("\n> ")
        except EOFError:
            break

        if user_input.lower() in ("exit", "quit", "q"):
            break

        if user_input.lower() == "reset":
            messages = []
            click.echo("Chat history cleared.")
            continue

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})

        if streaming:
            click.echo("")
            response = ""
            metadata = {}
            with loading(f"Loading model {model} ..."):
                for item in chat_stream(model, messages, host, timeout):
                    if isinstance(item, tuple) and item[0] == "stats":
                        metadata = item[1]
                    else:
                        response += item
                        click.echo(item, nl=False)
            click.echo("")
            if stats:
                print_stats(metadata)
        else:
            with loading("Generating response"):
                response, metadata = chat_single(model, messages, host, timeout)
            click.echo(response)
            if stats:
                print_stats(metadata)

        messages.append({"role": "assistant", "content": response})
