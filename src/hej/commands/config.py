"""config command — view and manage configuration."""

import logging
import os
import subprocess

import click
from rich import box
from rich.console import Console
from rich.table import Table

from hej import CONTEXT_SETTINGS, config

logger = logging.getLogger(__name__)

SAMPLE_CONFIG = """\
# hej configuration
# See `hej config --help` for details.

default_model = "phi3"
host = "http://localhost:11434"
timeout = 600
streaming = false
stats = true
"""


def _ensure_config_dir():
    """Create the config directory if it doesn't exist."""
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _key_source(key: str) -> str:
    """Return where *key* gets its value: ``"env"``, ``"conf"``, or ``"default"``."""
    env_var = config.ENV_MAP.get(key)
    if env_var and os.environ.get(env_var):
        return "env"
    cfg_path = config._find_config()
    if cfg_path is not None:
        try:
            with open(cfg_path, "rb") as f:
                import tomllib

                cfg_data = tomllib.load(f)
            if key in cfg_data:
                return "conf"
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            pass
    return "default"


@click.command("config", context_settings=CONTEXT_SETTINGS)
@click.option("-w", "--write", "write_", is_flag=True, help="Write config to file")
@click.option("--pretty", is_flag=True, help="Show effective config with sources")
@click.option("--path", is_flag=True, help="Show config file path")
@click.option("--edit", is_flag=True, help="Open config in $EDITOR")
def cmd(write_, pretty, path, edit):
    """View and manage hej configuration."""
    logger.debug("config.cmd()")

    if path:
        click.echo(str(config.CONFIG_PATH))
        return

    if write_:
        if config.CONFIG_PATH.exists():
            click.confirm(f"Overwrite {config.CONFIG_PATH}?", abort=True)
        _ensure_config_dir()
        config.CONFIG_PATH.write_text(SAMPLE_CONFIG)
        click.echo(f"Wrote config to {config.CONFIG_PATH}")
        return

    if edit:
        editor = os.environ.get("EDITOR", "vi")
        if not config.CONFIG_PATH.exists():
            _ensure_config_dir()
            config.CONFIG_PATH.write_text(SAMPLE_CONFIG)
        subprocess.call([editor, str(config.CONFIG_PATH)])
        return

    if pretty:
        _show_pretty()
    else:
        click.echo(SAMPLE_CONFIG, nl=False)


def _show_pretty():
    """Display where each value comes from."""
    console = Console(no_color=True, highlight=False)
    cfg = config.load()

    t = Table(title="Config", box=box.SIMPLE, show_edge=False, pad_edge=False)
    for h in ["Key", "Value", "Source"]:
        t.add_column(h)
    for key in config.DEFAULTS:
        t.add_row(key, repr(cfg[key]), _key_source(key))
    console.print(t)
