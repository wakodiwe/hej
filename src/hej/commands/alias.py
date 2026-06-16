"""alias command — manage custom shortcuts."""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path

import click

from hej import CONTEXT_SETTINGS
from hej.config import CONFIG_DIR

logger = logging.getLogger(__name__)

ALIASES_PATH = CONFIG_DIR / "aliases.toml"


def _ensure_file() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not ALIASES_PATH.exists():
        ALIASES_PATH.write_text("")


def _load_aliases() -> dict[str, str]:
    _ensure_file()
    if ALIASES_PATH.stat().st_size == 0:
        return {}
    try:
        data = tomllib.loads(ALIASES_PATH.read_text())
        return {k: v for k, v in data.items() if isinstance(v, str)}
    except Exception:
        return {}


def _save_aliases(aliases: dict[str, str]) -> None:
    _ensure_file()
    lines = [
        f'{k} = "{v.replace(chr(34), chr(92) + chr(34))}"\n'
        for k, v in aliases.items()
    ]
    ALIASES_PATH.write_text("".join(lines))


@click.group("alias", context_settings=CONTEXT_SETTINGS)
def cmd() -> None:
    """Manage command aliases."""


@cmd.command("list", context_settings=CONTEXT_SETTINGS)
def _list() -> None:
    """List all aliases."""
    aliases = _load_aliases()
    if not aliases:
        click.echo("No aliases defined")
        return
    for name, value in sorted(aliases.items()):
        click.echo(f"{name} = {value}")


@cmd.command("set", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
@click.argument("command")
def _set(name: str, command: str) -> None:
    """Create or update an alias."""
    aliases = _load_aliases()
    aliases[name] = command
    _save_aliases(aliases)
    click.echo(f"Alias '{name}' set to: {command}")


@cmd.command("get", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
def _get(name: str) -> None:
    """Show an alias."""
    aliases = _load_aliases()
    if name not in aliases:
        click.echo(f"Alias '{name}' not found", err=True)
        raise SystemExit(1)
    click.echo(aliases[name])


@cmd.command("delete", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def _delete(name: str, force: bool) -> None:
    """Delete an alias."""
    aliases = _load_aliases()
    if name not in aliases:
        click.echo(f"Alias '{name}' not found", err=True)
        raise SystemExit(1)
    if not force:
        click.confirm(f"Delete alias '{name}'?", abort=True)
    del aliases[name]
    _save_aliases(aliases)
    click.echo(f"Alias '{name}' deleted")
