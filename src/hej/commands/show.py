"""show command"""

import json
import logging
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
    print(f"    architecture        {architecture}")
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


def _print_modelfile(modelfile: str) -> None:
    """Print the modelfile in a Rich Panel.

    Args:
        modelfile: Raw modelfile content.
    """
    Console().print(Panel(modelfile.strip(), title="Modelfile"))


def _print_template(template: str) -> None:
    """Print the template in a Rich Panel.

    Args:
        template: Raw template content.
    """
    Console().print(Panel(template.strip(), title="Template"))


def _print_license(license_text: str) -> None:
    """Print the license in a Rich Panel.

    Args:
        license_text: Raw license text.
    """
    Console().print(Panel(license_text.strip(), title="License"))


def _print_parameters(params: dict) -> None:
    """Print inference parameters in a Rich Panel.

    Args:
        params: API response dict containing a ``"parameters"`` key.
    """
    param_str = params.get("parameters", "")
    stop_params = []
    for line in param_str.splitlines():
        line = line.strip()
        if line.startswith("stop"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                stop_params.append(parts[1].strip())
    if stop_params:
        Console().print(
            Panel("\n".join(f"stop {s}" for s in stop_params), title="Parameters")
        )


def long_report(params: dict):
    """Render a beautifully formatted model report using Rich."""
    console = Console()
    details = params.get("details", {})
    model_info = params.get("model_info", {})
    tensors = params.get("tensors", [])
    capabilities = params.get("capabilities", [])
    modified_at = params.get("modified_at", "")
    param_str = params.get("parameters", "")
    license_text = params.get("license", "")
    modelfile_text = params.get("modelfile", "")
    template_text = params.get("template", "")

    stop_params = []
    for line in param_str.splitlines():
        line = line.strip()
        if line.startswith("stop"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                stop_params.append(parts[1].strip())

    parent_model = details.get("parent_model", "N/A")

    title_text = Text()
    title_text.append("Model Report\n", style="bold cyan")
    title_text.append(f"ollama show  •  {parent_model}", style="dim")
    console.print(Panel(title_text, expand=False, padding=(0, 2)))

    summary_table = Table(title="Model Summary", show_header=False, box=None)
    summary_table.add_column("Property", style="bold yellow")
    summary_table.add_column("Value", style="white")

    summary_data = [
        ("Parent Model", parent_model),
        ("Format", details.get("format", "N/A")),
        ("Family", details.get("family", "N/A")),
        ("Parameter Size", details.get("parameter_size", "N/A")),
        ("Quantization", details.get("quantization_level", "N/A")),
        ("Capabilities", ", ".join(capabilities) if capabilities else "N/A"),
        ("Context Length", _fmt_int(model_info.get("llama.context_length"))),
        ("Vocab Size", _fmt_int(model_info.get("llama.vocab_size"))),
        ("Layers (Blocks)", model_info.get("llama.block_count", "N/A")),
        ("Embedding Dim", _fmt_int(model_info.get("llama.embedding_length"))),
        ("Attention Heads", _fmt_attention(model_info)),
        ("Modified At", modified_at),
    ]
    for prop, val in summary_data:
        summary_table.add_row(prop, str(val))
    console.print(summary_table)
    console.print()

    arch_table = Table(title="Architecture Details", show_header=False, box=None)
    arch_table.add_column("Property", style="bold yellow")
    arch_table.add_column("Value", style="white")
    for key, value in sorted(model_info.items()):
        if isinstance(value, int) and value > 1000:
            value_str = f"{value:,}"
        else:
            value_str = str(value)
        arch_table.add_row(key, value_str)
    console.print(arch_table)
    console.print()

    param_table = Table(title="Inference Parameters", show_header=False, box=None)
    param_table.add_column("Parameter", style="bold yellow")
    param_table.add_column("Value", style="white")
    for stop_val in stop_params:
        param_table.add_row("stop", stop_val)
    if not stop_params:
        param_table.add_row("(none)", "")
    console.print(param_table)
    console.print()

    type_counts: dict[str, int] = {}
    type_elements: dict[str, int] = {}
    total_elements = 0
    for t in tensors:
        dtype = t.get("type", "unknown")
        shape = t.get("shape", [])
        num_el = math.prod(shape) if shape else 0
        type_counts[dtype] = type_counts.get(dtype, 0) + 1
        type_elements[dtype] = type_elements.get(dtype, 0) + num_el
        total_elements += num_el

    if tensors:
        stats_table = Table(title="Tensor Statistics", box=None)
        stats_table.add_column("Type", style="bold cyan")
        stats_table.add_column("Count", justify="right", style="white")
        stats_table.add_column("Total Elements", justify="right", style="white")
        stats_table.add_column("% of Total", justify="right", style="green")
        for dtype in sorted(type_counts.keys()):
            cnt = type_counts[dtype]
            els = type_elements[dtype]
            pct = (els / total_elements * 100) if total_elements else 0
            stats_table.add_row(dtype, f"{cnt:,}", f"{els:,}", f"{pct:.1f}%")
        console.print(stats_table)
        console.print()

        full_table = Table(
            title=f"Full Tensor List ({len(tensors)} tensors)",
            box=None,
        )
        full_table.add_column("#", style="dim", justify="right")
        full_table.add_column("Name", style="cyan")
        full_table.add_column("Type", style="yellow")
        full_table.add_column("Shape", style="white")
        full_table.add_column("Elements", justify="right", style="green")
        for idx, t in enumerate(tensors, start=1):
            name = t.get("name", "")
            dtype = t.get("type", "")
            shape = t.get("shape", [])
            shape_str = f"[{', '.join(str(s) for s in shape)}]"
            num_el = math.prod(shape) if shape else 0
            full_table.add_row(str(idx), name, dtype, shape_str, f"{num_el:,}")
        console.print(full_table)
        console.print()

    seg_table = Table(show_header=False, box=None)
    seg_table.add_column("File", style="bold yellow")
    seg_table.add_column("Info", style="white")
    seg_table.add_row("License", _fmt_len(license_text))
    seg_table.add_row("Modelfile", _fmt_len(modelfile_text))
    seg_table.add_row("Template", _fmt_len(template_text))
    console.print(seg_table)

    footer = Text()
    footer.append(
        "Generated with Rich  •  Data source: ollama show --json", style="dim"
    )
    console.print(Panel(footer, expand=False))


def _fmt_int(val: int | None | str) -> str:
    """Format an integer with thousands separator.

    Args:
        val: Integer, string, or None.

    Returns:
        Formatted string (e.g. ``"8,192"``) or ``"N/A"`` if falsy.
    """
    if isinstance(val, int):
        return f"{val:,}"
    return val if val else "N/A"


def _fmt_attention(model_info: dict) -> str:
    """Format attention head info from model metadata.

    Args:
        model_info: Model info dict from the API.

    Returns:
        Formatted head count string, optionally with KV heads.
    """
    hc = model_info.get("llama.attention.head_count")
    hckv = model_info.get("llama.attention.head_count_kv")
    if hc is not None:
        if hckv is not None:
            return f"{hc:,} (KV: {hckv:,})"
        return f"{hc:,}"
    return "N/A"


def _fmt_len(text: str) -> str:
    """Format a text length for display.

    Args:
        text: Input string.

    Returns:
        ``"N chars"`` or ``"0 chars"`` if empty.
    """
    return f"{len(text):,} chars" if text else "0 chars"


@click.command("show", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--host", help="Ollama server URL")
@click.option("-v", "--verbose", is_flag=True, help="Include full model info from API")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON")
@click.option("--full", is_flag=True, help="Show full formatted report")
@click.option("--modelfile", is_flag=True, help="Show modelfile")
@click.option("--template", is_flag=True, help="Show template")
@click.option("--license", "show_license", is_flag=True, help="Show license")
@click.option("--parameters", is_flag=True, help="Show parameters")
def cmd(
    model,
    host,
    verbose,
    json_output,
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

    if modelfile:
        _print_modelfile(data.get("modelfile", ""))
    elif template:
        _print_template(data.get("template", ""))
    elif show_license:
        _print_license(data.get("license", ""))
    elif parameters:
        _print_parameters(data)
    elif full:
        long_report(data)
    else:
        simple_report(data)
