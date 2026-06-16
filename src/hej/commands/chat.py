"""chat command"""

from __future__ import annotations

import json
import logging
from typing import Iterator

import click

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error, extract_metadata, print_stats
from hej.progress import wake_progress
from hej.utils import copy_to_clipboard, open_in_editor

logger = logging.getLogger(__name__)

CHAT_API = "/api/chat"


def chat_stream(
    model: str, messages: list[dict[str, str]], host: str, timeout: int
) -> Iterator[str | tuple[str, dict]]:
    """Yield tokens from the chat API, streaming, return full response."""
    import requests

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
    import requests

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


@click.command("chat", context_settings=CONTEXT_SETTINGS)
@click.option("--host", help="Ollama server URL")
@click.option("-m", "--model", help="Model name")
@click.option("-t", "--template", "template_name", help="System prompt template name")
@click.option("--stream/--no-stream", default=None, help="Stream output")
@click.option("--stats/--no-stats", default=None, help="Show timing stats")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--reset", is_flag=True, help="Clear chat history")
@click.option("--save-as", "save_name", help="Save conversation on exit")
@click.option("--resume", "resume_name", help="Resume saved conversation")
@click.option("--copy", is_flag=True, help="Copy each response to clipboard")
@click.option("--open", "open_editor", is_flag=True, help="Open each response in editor")
def cmd(
    host: str | None = None,
    model: str | None = None,
    template_name: str | None = None,
    stream: bool | None = None,
    stats: bool | None = None,
    timeout: int | None = None,
    reset: bool = False,
    save_name: str | None = None,
    resume_name: str | None = None,
    copy: bool = False,
    open_editor: bool = False,
) -> None:
    """Interactive multi-turn chat"""
    from hej.api import isrunning
    from hej.commands.session import load_session, save_session
    from hej.commands.template import load_template

    cfg = config.load()
    host = host or cfg["host"]
    streaming = stream if stream is not None else cfg["streaming"]
    timeout = timeout or cfg["timeout"]
    model = model or cfg["default_model"]
    stats = stats if stats is not None else cfg["stats"]

    if not isrunning(host):
        click.echo("Error: Ollama server is not running", err=True)
        raise SystemExit(1)

    messages: list[dict[str, str]] = []

    if template_name:
        tmpl = load_template(template_name)
        if tmpl is None:
            click.echo(f"Template '{template_name}' not found", err=True)
            raise SystemExit(1)
        messages.append({"role": "system", "content": tmpl})

    if resume_name:
        data = load_session(resume_name)
        if data is None:
            click.echo(f"Session '{resume_name}' not found", err=True)
            raise SystemExit(1)
        messages = data.get("messages", [])
        model = data.get("model", model)
        if not save_name:
            save_name = resume_name

    if save_name:
        from hej.commands.session import _session_path as _spath

        if _spath(save_name).exists():
            click.echo(f"Resuming existing session '{save_name}'.")

    if reset:
        click.echo("Chat history cleared.")
        return

    click.echo(
        f"Chat mode (model: {model}). Type 'exit' to quit, 'reset' to clear history."
    )
    click.echo("---")

    try:
        while True:
            try:
                from prompt_toolkit import prompt

                user_input = prompt("\n> ", vi_mode=True)
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

            if save_name:
                save_session(save_name, model, messages)

            if streaming:
                click.echo("")
                response = ""
                metadata = {}
                with wake_progress(model):
                    for item in chat_stream(model, messages, host, timeout):
                        if isinstance(item, tuple) and item[0] == "stats":
                            metadata = item[1]
                        else:
                            assert isinstance(item, str)
                            response += item
                            click.echo(item, nl=False)
                click.echo("")
                if stats:
                    print_stats(metadata)
            else:
                with wake_progress(model):
                    response, metadata = chat_single(model, messages, host, timeout)
                click.echo(response)
                if stats:
                    print_stats(metadata)

            messages.append({"role": "assistant", "content": response})

            if copy and response:
                copy_to_clipboard(response)
                click.echo("(copied to clipboard)")
            if open_editor and response:
                open_in_editor(response)

            if save_name:
                save_session(save_name, model, messages)
    except KeyboardInterrupt:
        if save_name:
            save_session(save_name, model, messages)
        raise
