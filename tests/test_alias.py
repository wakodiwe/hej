"""Tests for hej.commands.alias."""

import os
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from hej.cli import cli

ALIASES_PATH = "hej.commands.alias.ALIASES_PATH"


class TestAlias:
    def test_list_empty(self, tmp_path: Path) -> None:
        aliases_file = tmp_path / "aliases.toml"
        with patch(ALIASES_PATH, aliases_file):
            runner = CliRunner()
            result = runner.invoke(cli, ["alias", "list"])
            assert result.exit_code == 0
            assert "No aliases defined" in result.output

    def test_set_and_list(self, tmp_path: Path) -> None:
        aliases_file = tmp_path / "aliases.toml"
        with patch(ALIASES_PATH, aliases_file):
            runner = CliRunner()
            result = runner.invoke(cli, ["alias", "set", "hi", "run hello"])
            assert result.exit_code == 0
            assert "Alias 'hi' set" in result.output
            result = runner.invoke(cli, ["alias", "list"])
            assert "hi" in result.output
            assert "run hello" in result.output

    def test_get(self, tmp_path: Path) -> None:
        aliases_file = tmp_path / "aliases.toml"
        with patch(ALIASES_PATH, aliases_file):
            runner = CliRunner()
            runner.invoke(cli, ["alias", "set", "hi", "run hello"])
            result = runner.invoke(cli, ["alias", "get", "hi"])
            assert result.exit_code == 0
            assert "run hello" in result.output.strip()

    def test_get_missing(self, tmp_path: Path) -> None:
        aliases_file = tmp_path / "aliases.toml"
        with patch(ALIASES_PATH, aliases_file):
            runner = CliRunner()
            result = runner.invoke(cli, ["alias", "get", "nope"])
            assert result.exit_code == 1
            assert "not found" in result.output

    def test_delete(self, tmp_path: Path) -> None:
        aliases_file = tmp_path / "aliases.toml"
        with patch(ALIASES_PATH, aliases_file):
            runner = CliRunner()
            runner.invoke(cli, ["alias", "set", "hi", "run x"])
            result = runner.invoke(cli, ["alias", "delete", "hi", "--force"])
            assert result.exit_code == 0
            assert "deleted" in result.output
            result = runner.invoke(cli, ["alias", "list"])
            assert "No aliases" in result.output

    def test_delete_missing(self, tmp_path: Path) -> None:
        aliases_file = tmp_path / "aliases.toml"
        with patch(ALIASES_PATH, aliases_file):
            runner = CliRunner()
            result = runner.invoke(cli, ["alias", "delete", "nope", "--force"])
            assert result.exit_code == 1
            assert "not found" in result.output


class TestAliasHelp:
    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["alias", "--help"])
        assert result.exit_code == 0
        assert "alias" in result.output.lower()
