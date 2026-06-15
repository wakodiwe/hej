"""template command — manage reusable prompt templates."""

from pathlib import Path

import click

from hej import CONTEXT_SETTINGS
from hej.config import CONFIG_DIR

TEMPLATES_DIR = CONFIG_DIR / "templates"


def _ensure_dir() -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def _template_path(name: str) -> Path:
    return TEMPLATES_DIR / f"{name}.txt"


def apply_template(template_content: str, user_input: str) -> str:
    if "{input}" in template_content:
        return template_content.replace("{input}", user_input)
    return template_content + "\n\n" + user_input


def load_template(name: str) -> str | None:
    path = _template_path(name)
    if not path.exists():
        return None
    return path.read_text()


@click.group("template", context_settings=CONTEXT_SETTINGS)
def cmd() -> None:
    """Manage prompt templates."""


@cmd.command("create", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
@click.option("--content", help="Template content (or omit for interactive)")
def create(name: str, content: str | None = None) -> None:
    """Create a new prompt template."""
    _ensure_dir()
    path = _template_path(name)
    if path.exists():
        click.echo(f"Template '{name}' already exists", err=True)
        raise SystemExit(1)
    if content is not None:
        if not content.strip():
            click.echo("Empty template, aborted.", err=True)
            raise SystemExit(1)
        text = content
    else:
        click.echo(f"Enter template content for '{name}' (Ctrl-D to save):")
        try:
            edited = click.edit("", extension=".txt")
        except click.ClickException:
            edited = None
        if not edited or not edited.strip():
            click.echo("Empty template, aborted.", err=True)
            raise SystemExit(1)
        text = edited.strip()
    path.write_text(text)
    click.echo(f"Created template '{name}'")


@cmd.command("list", context_settings=CONTEXT_SETTINGS)
def list_() -> None:
    """List all prompt templates."""
    if not TEMPLATES_DIR.exists():
        click.echo("No templates found")
        return
    names = sorted(p.stem for p in TEMPLATES_DIR.iterdir() if p.suffix == ".txt")
    if not names:
        click.echo("No templates found")
        return
    for n in names:
        click.echo(n)


@cmd.command("show", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
def show(name: str) -> None:
    """Show a template's content."""
    content = load_template(name)
    if content is None:
        click.echo(f"Template '{name}' not found", err=True)
        raise SystemExit(1)
    click.echo(content)


@cmd.command("delete", context_settings=CONTEXT_SETTINGS)
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete(name: str, force: bool = False) -> None:
    """Delete a prompt template."""
    path = _template_path(name)
    if not path.exists():
        click.echo(f"Template '{name}' not found", err=True)
        raise SystemExit(1)
    if not force:
        click.confirm(f"Delete template '{name}'?", abort=True)
    path.unlink()
    click.echo(f"Deleted template '{name}'")
