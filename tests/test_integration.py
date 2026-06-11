"""Integration tests with a mocked Ollama HTTP server."""

import json

import pytest
import requests
import responses
from click.testing import CliRunner
from hej.cli import cli

HOST = "http://localhost:11434"


class TestLs:
    @responses.activate
    def test_ls(self):
        responses.get(
            f"{HOST}/api/tags",
            json={"models": [{"name": "phi3:latest", "size": 1234,
                              "modified_at": "2024-01-15T10:30:00Z",
                              "digest": "abc123", "details": {}}]},
        )
        result = CliRunner().invoke(cli, ["ls", "--host", HOST])
        assert result.exit_code == 0
        assert "phi3" in result.output

    @responses.activate
    def test_ls_empty(self):
        responses.get(f"{HOST}/api/tags", json={"models": []})
        result = CliRunner().invoke(cli, ["ls", "--host", HOST])
        assert result.exit_code == 0
        assert "No models" in result.output

    @responses.activate
    def test_ls_error(self):
        responses.get(f"{HOST}/api/tags", status=500)
        result = CliRunner().invoke(cli, ["ls", "--host", HOST])
        assert result.exit_code != 0


class TestPs:
    @responses.activate
    def test_ps(self):
        responses.get(
            f"{HOST}/api/ps",
            json={"models": [{"name": "phi3:latest", "size": 1234,
                              "digest": "abc", "expires_at": "2024-01-15T12:00:00Z",
                              "context_length": 8192, "size_vram": 1234,
                              "details": {}}]},
        )
        result = CliRunner().invoke(cli, ["ps", "--host", HOST])
        assert result.exit_code == 0
        assert "phi3" in result.output

    @responses.activate
    def test_ps_empty(self):
        responses.get(f"{HOST}/api/ps", json={"models": []})
        result = CliRunner().invoke(cli, ["ps", "--host", HOST])
        assert result.exit_code == 0
        assert "No models in memory" in result.output


class TestShow:
    @responses.activate
    def test_show(self):
        responses.post(
            f"{HOST}/api/show",
            json={"details": {"family": "llama", "parameter_size": "3.8B",
                              "quantization_level": "Q4_0"},
                  "model_info": {"llama.context_length": 8192},
                  "capabilities": ["vision"], "parameters": "", "license": ""},
        )
        result = CliRunner().invoke(cli, ["show", "phi3", "--host", HOST])
        assert result.exit_code == 0
        assert "llama" in result.output

    @responses.activate
    def test_show_error(self):
        responses.post(f"{HOST}/api/show", status=404)
        result = CliRunner().invoke(cli, ["show", "phi3", "--host", HOST])
        assert result.exit_code != 0


class TestRun:
    @responses.activate
    def test_run(self):
        responses.get(f"{HOST}/api/tags", status=200)
        responses.post(
            f"{HOST}/api/generate",
            json={"response": "Hello world", "total_duration": 0,
                  "eval_count": 3, "eval_duration": 0},
        )
        result = CliRunner().invoke(cli, ["run", "--host", HOST, "--no-stats", "hello"])
        assert result.exit_code == 0
        assert "Hello world" in result.output


class TestCp:
    @responses.activate
    def test_cp(self):
        responses.post(f"{HOST}/api/copy", status=200)
        result = CliRunner().invoke(cli, ["cp", "--host", HOST, "phi3", "phi3-copy"])
        assert result.exit_code == 0
        assert "Copied" in result.output

    @responses.activate
    def test_cp_error(self):
        responses.post(f"{HOST}/api/copy", status=500)
        result = CliRunner().invoke(cli, ["cp", "--host", HOST, "phi3", "phi3-copy"])
        assert result.exit_code != 0


class TestRm:
    @responses.activate
    def test_rm(self):
        responses.delete(f"{HOST}/api/delete", status=200)
        result = CliRunner().invoke(cli, ["rm", "--host", HOST, "phi3", "--force"])
        assert result.exit_code == 0
        assert "Deleted" in result.output

    @responses.activate
    def test_rm_error(self):
        responses.delete(f"{HOST}/api/delete", status=500)
        result = CliRunner().invoke(cli, ["rm", "--host", HOST, "phi3", "--force"])
        assert result.exit_code != 0


class TestStop:
    @responses.activate
    def test_stop(self):
        responses.post(f"{HOST}/api/generate", status=200)
        result = CliRunner().invoke(cli, ["stop", "--host", HOST, "phi3"])
        assert result.exit_code == 0
        assert "Stopped" in result.output

    @responses.activate
    def test_stop_error(self):
        responses.post(f"{HOST}/api/generate", status=500)
        result = CliRunner().invoke(cli, ["stop", "--host", HOST, "phi3"])
        assert result.exit_code != 0


class TestStatus:
    @responses.activate
    def test_running(self):
        responses.get(f"{HOST}/api/tags", status=200)
        result = CliRunner().invoke(cli, ["status", "--host", HOST])
        assert result.exit_code == 0
        assert "running" in result.output

    @responses.activate
    def test_not_running(self):
        result = CliRunner().invoke(cli, ["status", "--host", HOST])
        assert result.exit_code == 0
        assert "not running" in result.output


class TestPull:
    @responses.activate
    def test_pull(self):
        responses.post(
            f"{HOST}/api/pull",
            body=b'{"status":"success"}\n',
        )
        result = CliRunner().invoke(cli, ["pull", "--host", HOST, "phi3"])
        assert result.exit_code == 0
        assert "success" in result.output
