"""show command"""

import logging

import json

import math

import click
import requests

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hej import CONTEXT_SETTINGS, config
from hej.api import api_error

logger = logging.getLogger(__name__)


def _print_license(license_text: str) -> None:
    """Print the license.
    Args:
        license_text: Raw license text.
    """
    Console().print(license_text.strip())


def _print_modelfile(modelfile: str) -> None:
    """Print the modelfile.
    Args:
        modelfile: Raw modelfile content.
    """
    Console().print(modelfile.strip())


def _print_parameters(params: dict) -> None:
    """Print inference parameters.
    Args:
        params: API response dict containing a ``"parameters"`` key.
    """
    # param_str = params.get("parameters", "")
    stop_params = []
    for line in params.splitlines():
        line = line.strip()
        if line.startswith("stop"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                stop_params.append(parts[1].strip())
    if stop_params:
        Console().print("\n".join(f"stop {s}" for s in stop_params))


def _print_template(template: str) -> None:
    """Print the template.
    Args:
        template: Raw template content.
    """
    Console().print(template.strip())


def simple_report(params: dict):
    """Print a simplified model report similar to ollama show <model>"""
    details = params.get("details", {})
    model_info = params.get("model_info", {})
    capabilities = params.get("capabilities", [])
    param_str = params.get("parameters", "")
    license_text = params.get("license", "")
    architecture = details.get("family", "unknown")
    param_size = details.get("parameter_size", "unknown")
    context_len = model_info.get("llama.context_length", "unknown")
    embed_len = model_info.get("llama.embedding_length", "unknown")
    quantization = details.get("quantization_level", "unknown")
    if isinstance(context_len, int):
        context_len = f"{context_len:,}"
    if isinstance(embed_len, int):
        embed_len = f"{embed_len:,}"
    caps = capabilities if capabilities else ["none"]
    stop_params = []
    for line in param_str.splitlines():
        line = line.strip()
        if line.startswith("stop"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                stop_params.append(parts[1].strip())
    license_lines = license_text.strip().splitlines()
    first_license_line = license_lines[0] if license_lines else ""
    second_license_line = license_lines[1] if len(license_lines) > 1 else ""
    print("  Model")
    print(f"    architecture         {architecture}")
    print(f"    parameters           {param_size}")
    print(f"    context length       {context_len}")
    print(f"    embedding length     {embed_len}")
    print(f"    quantization         {quantization}")
    print()
    print("  Capabilities")
    for cap in caps:
        print(f"    {cap}")
    print()
    print("  Parameters")
    for stop in stop_params:
        print(f"    stop    {stop}")
    print()
    print("  License")
    if first_license_line:
        print(f"    {first_license_line}")
    if second_license_line:
        print(f"    {second_license_line}")
    print("    ...")


@click.command("show", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--host", help="Ollama server URL")
@click.option("-v", "--verbose", is_flag=True, help="Include full model info from API")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON")
@click.option("--jsonc", "json_compact", is_flag=True, help="Output compact raw JSON")
@click.option("--full", "full", is_flag=True, help="Show full formatted report")
@click.option("--modelfile", is_flag=True, help="Show modelfile")
@click.option("--template", is_flag=True, help="Show template")
@click.option("--license", "show_license", is_flag=True, help="Show license")
@click.option("--parameters", is_flag=True, help="Show parameters")
def cmd(
    model,
    host,
    verbose,
    json_output,
    json_compact,
    full,
    modelfile,
    template,
    show_license,
    parameters,
):
    """Show information for a MODEL"""

    logger.debug("show.cmd(%r)", model)
    cfg = config.load()
    host = host or cfg["host"]
    timeout = cfg["timeout"]

    try:
        r = requests.post(
            f"{host}/api/show",
            json={"model": model, "verbose": verbose},
            timeout=timeout,
        )

        r.raise_for_status()

    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        api_error(e, host)

    data = r.json()

    if json_output:
        click.echo(json.dumps(data, indent=2))
        return

    if json_compact:
        click.echo(json.dumps(data, separators=(",", ":")))
        return

    if show_license:
        _print_license(data.get("license", ""))
        return

    if modelfile:
        _print_modelfile(data.get("modelfile", ""))
        return

    if template:
        _print_template(data.get("template", ""))
        return

    if parameters:
        _print_parameters(data.get("parameters", ""))
        return

    if full:
        _print_license(data.get("license", ""))
        _print_modelfile(data.get("modelfile", ""))
        _print_template(data.get("template", ""))
        _print_parameters(data.get("parameters", ""))
        return

    simple_report(data)
