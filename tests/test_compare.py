"""Tests for hej.commands.compare."""

from unittest.mock import patch

from click.testing import CliRunner

from hej.cli import cli


class TestCompare:
    @patch("hej.commands.compare.generate")
    @patch("hej.commands.compare.isrunning", return_value=True)
    def test_compare_single_model(self, mock_running, mock_generate):
        mock_generate.return_value = "Hello from model"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["compare", "hello", "-m", "phi3"],
        )
        assert result.exit_code == 0
        assert "phi3" in result.output

    @patch("hej.commands.compare.generate")
    @patch("hej.commands.compare.isrunning", return_value=True)
    def test_compare_multiple_models(self, mock_running, mock_generate):
        mock_generate.side_effect = ["Response A", "Response B"]
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["compare", "test", "-m", "model1", "-m", "model2"],
        )
        assert result.exit_code == 0
        assert "model1" in result.output
        assert "model2" in result.output

    @patch("hej.commands.compare.isrunning", return_value=False)
    def test_compare_server_not_running(self, mock_running):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["compare", "test", "-m", "phi3"],
        )
        assert result.exit_code == 1
        assert "not running" in result.output

    @patch("hej.commands.compare.generate")
    @patch("hej.commands.compare.isrunning", return_value=True)
    def test_compare_json_format(self, mock_running, mock_generate):
        mock_generate.return_value = "Test response"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["compare", "test", "-m", "phi3", "--format", "json"],
        )
        assert result.exit_code == 0
        assert "model" in result.output
        assert "response" in result.output


class TestCompareHelp:
    def test_help(self):
        result = CliRunner().invoke(cli, ["compare", "--help"])
        assert result.exit_code == 0
        assert "compare" in result.output.lower()
