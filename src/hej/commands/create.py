"""create command"""

import logging

logger = logging.getLogger(__name__)

import click

from hej import CONTEXT_SETTINGS, config
from hej.progress import stream_operation


@click.command("create", context_settings=CONTEXT_SETTINGS)
@click.argument("model")
@click.option("--from-model", help="Base model to create from")
@click.option("--system", help="System prompt")
@click.option("--template", help="Prompt template")
@click.option("--quantize", type=click.Choice(["q4_K_M", "q4_K_S", "q8_0"]))
@click.option("--license", help="Model license")
@click.option("--host", help="Ollama server URL")
def cmd(model, from_model, system, template, quantize, license, host):
    """Create a model from a base model"""
    cfg = config.load()
    host = host or cfg["host"]

    payload = {"model": model}
    if from_model:
        payload["from"] = from_model
    if system:
        payload["system"] = system
    if template:
        payload["template"] = template
    if quantize:
        payload["quantize"] = quantize
    if license:
        payload["license"] = license

    stream_operation("/api/create", model, host, cfg["timeout"], verb="creating", payload=payload)
