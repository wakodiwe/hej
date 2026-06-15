"""session command — manage saved chat sessions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import click

from hej import CONTEXT_SETTINGS
from hej.config import CONFIG_DIR

SESSIONS_DIR = CONFIG_DIR / "sessions"


def _ensure_dir() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(name: str) -> Path:
    return SESSIONS_DIR / f"{name}.json"


def save_session(name: str, model: str, messages: list[dict[str, str]]) -> str:
    _ensure_dir()
    path = _session_path(name)
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "id": name,
        "model": model,
        "created_at": now,
        "messages": messages,
    }
    path.write_text(json.dumps(data, indent=2))
    return str(path)


def load_session(name: str) -> dict[str, Any] | None:
    path = _session_path(name)
    if not path.exists():
        return None
    return cast(dict[str, Any], json.loads(path.read_text()))


@click.group("session", context_settings=CONTEXT_SETTINGS)
def cmd() -> None:
    """Manage saved chat sessions."""


@cmd.command("list", context_settings=CONTEXT_SETTINGS)
def list_() -> None:
    """List all saved sessions."""
    if not SESSIONS_DIR.exists():
        click.echo("No saved sessions")
        return
    names = sorted(p.stem for p in SESSIONS_DIR.iterdir() if p.suffix == ".json")
    if not names:
        click.echo("No saved sessions")
        return
    for name in names:
        data = json.loads((SESSIONS_DIR / f"{name}.json").read_text())
        msg_count = len(data.get("messages", []))
        created = data.get("created_at", "?")[:19].replace("T", " ")
        click.echo(f"{name:20s}  ({msg_count} msgs, {created})")


@cmd.command("load", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
def load(name: str) -> None:
    """Load and resume a saved session."""
    data = load_session(name)
    if data is None:
        click.echo(f"Session '{name}' not found", err=True)
        raise SystemExit(1)
    click.echo(json.dumps(data, indent=2))


@cmd.command("export", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "md"]),
    default="json",
    help="Export format",
)
def export(name: str, fmt: str) -> None:
    """Export a session as JSON or Markdown."""
    data = load_session(name)
    if data is None:
        click.echo(f"Session '{name}' not found", err=True)
        raise SystemExit(1)
    if fmt == "json":
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"# Session: {name}\n")
        click.echo(f"Model: {data.get('model', '?')}")
        click.echo(f"Created: {data.get('created_at', '?')}\n")
        click.echo("---\n")
        for msg in data.get("messages", []):
            role = msg.get("role", "?").upper()
            content = msg.get("content", "")
            click.echo(f"**{role}:** {content}\n")


@cmd.command("delete", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete(name: str, force: bool = False) -> None:
    """Delete a saved session."""
    path = _session_path(name)
    if not path.exists():
        click.echo(f"Session '{name}' not found", err=True)
        raise SystemExit(1)
    if not force:
        click.confirm(f"Delete session '{name}'?", abort=True)
    path.unlink()
    click.echo(f"Deleted session '{name}'")


@cmd.command("search", context_settings=CONTEXT_SETTINGS)
@click.argument("keyword")
def search(keyword: str) -> None:
    """Search saved sessions by content."""
    if not SESSIONS_DIR.exists():
        click.echo("No saved sessions")
        return
    found = False
    for path in sorted(SESSIONS_DIR.iterdir()):
        if path.suffix != ".json":
            continue
        data = json.loads(path.read_text())
        name = path.stem
        for msg in data.get("messages", []):
            if keyword.lower() in msg.get("content", "").lower():
                role = msg.get("role", "?")
                snippet = msg.get("content", "")[:80]
                click.echo(f"{name}  [{role}] {snippet}")
                found = True
                break
    if not found:
        click.echo(f"No sessions match '{keyword}'")
