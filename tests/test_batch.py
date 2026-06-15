"""Tests for hej.commands.batch."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from hej.cli import cli


class TestBatch:
    @patch("hej.commands.batch.generate")
    @patch("hej.commands.batch.isrunning", return_value=True)
    def test_batch_multiple_prompts(self, mock_running, mock_generate):
        mock_generate.side_effect = ["Response 1", "Response 2"]
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("prompts.txt").write_text("prompt1\nprompt2\n")
            result = runner.invoke(
                cli,
                ["batch", "-i", "prompts.txt", "-m", "phi3"],
            )
        assert result.exit_code == 0
        assert "Response 1" in result.output
        assert "Response 2" in result.output

    @patch("hej.commands.batch.isrunning", return_value=False)
    def test_batch_server_not_running(self, mock_running):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("prompts.txt").write_text("hello\n")
            result = runner.invoke(
                cli,
                ["batch", "-i", "prompts.txt"],
            )
        assert result.exit_code == 1
        assert "not running" in result.output

    @patch("hej.commands.batch.generate")
    @patch("hej.commands.batch.isrunning", return_value=True)
    def test_batch_empty_input(self, mock_running, mock_generate):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("empty.txt").write_text("\n\n\n")
            result = runner.invoke(
                cli,
                ["batch", "-i", "empty.txt", "-m", "phi3"],
            )
        assert result.exit_code == 1
        assert "No prompts" in result.output

    @patch("hej.commands.batch.generate")
    @patch("hej.commands.batch.isrunning", return_value=True)
    def test_batch_output_file(self, mock_running, mock_generate):
        mock_generate.return_value = "Test response"
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("prompts.txt").write_text("test\n")
            result = runner.invoke(
                cli,
                ["batch", "-i", "prompts.txt", "-o", "results.jsonl", "-m", "phi3"],
            )
            assert result.exit_code == 0
            assert Path("results.jsonl").exists()
            content = Path("results.jsonl").read_text()
            assert "Test response" in content

    @patch("hej.commands.batch.generate")
    @patch("hej.commands.batch.isrunning", return_value=True)
    def test_batch_concurrency(self, mock_running, mock_generate):
        mock_generate.return_value = "response"
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("prompts.txt").write_text("p1\np2\np3\np4\n")
            result = runner.invoke(
                cli,
                ["batch", "-i", "prompts.txt", "-c", "2", "-m", "phi3"],
            )
        assert result.exit_code == 0
        assert mock_generate.call_count == 4


class TestBatchHelp:
    def test_help(self):
        result = CliRunner().invoke(cli, ["batch", "--help"])
        assert result.exit_code == 0
        assert "batch" in result.output.lower()
