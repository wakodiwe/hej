"""Tests for hej.commands.bench."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from hej.cli import cli


class TestBench:
    @patch("hej.commands.bench.isrunning", return_value=False)
    def test_bench_server_not_running(self, mock_running):
        runner = CliRunner()
        result = runner.invoke(cli, ["bench", "-m", "phi3"])
        assert result.exit_code == 1
        assert "not running" in result.output

    @patch(
        "hej.commands.bench.generate",
        return_value=(
            "response",
            {"eval_count": 5, "total_duration_ns": 1_000_000_000},
        ),
    )
    @patch("hej.commands.bench.isrunning", return_value=True)
    def test_bench_single_model(self, mock_running, mock_generate):
        runner = CliRunner()
        result = runner.invoke(cli, ["bench", "-m", "phi3", "--runs", "2"])
        assert result.exit_code == 0
        assert "phi3" in result.output
        assert "Mean:" in result.output

    @patch(
        "hej.commands.bench.generate",
        return_value=(
            "response",
            {"eval_count": 5, "total_duration_ns": 1_000_000_000},
        ),
    )
    @patch("hej.commands.bench.isrunning", return_value=True)
    def test_bench_csv_output(self, mock_running, mock_generate):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("out.csv")  # ensure import
            result = runner.invoke(
                cli, ["bench", "-m", "phi3", "--runs", "1", "--output", "out.csv"]
            )
        assert result.exit_code == 0
        assert "phi3" in result.output

    @patch("hej.commands.bench.isrunning", return_value=False)
    def test_bench_help(self, mock_running):
        runner = CliRunner()
        result = runner.invoke(cli, ["bench", "--help"])
        assert result.exit_code == 0
        assert "bench" in result.output.lower()
