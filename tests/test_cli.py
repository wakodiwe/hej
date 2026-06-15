from unittest.mock import patch

import requests
from click.testing import CliRunner

from hej.cli import cli


class TestHelp:
    def test_long(self):
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "hej" in result.output

    def test_short_alias(self):
        result = CliRunner().invoke(cli, ["-h"])
        assert result.exit_code == 0
        assert "Usage:" in result.output


class TestNoArgs:
    def test_shows_help(self):
        result = CliRunner().invoke(cli, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output


class TestUnknownCommand:
    def test_fails_with_error(self):
        result = CliRunner().invoke(cli, ["nope"])
        assert result.exit_code != 0
        assert "Error" in result.output


class TestVersion:
    def test_short(self):
        result = CliRunner().invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_output_format(self):
        result = CliRunner().invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip() != ""


class TestStatus:
    def test_output(self):
        result = CliRunner().invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Ollama server" in result.output

    @patch("hej.commands.status.isrunning", return_value=False)
    def test_not_running(self, _mock):
        result = CliRunner().invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "not running" in result.output

    def test_help(self):
        result = CliRunner().invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()


class TestRun:
    def test_help(self):
        result = CliRunner().invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "PROMPT" in result.output

    @patch("hej.commands.run.isrunning", return_value=False)
    def test_no_server(self, _mock):
        result = CliRunner().invoke(cli, ["run", "hello"])
        assert result.exit_code == 1
        assert "not running" in result.output.lower()

    @patch("hej.commands.run.loading")
    @patch("hej.commands.run.generate", return_value=("Mocked response", {}))
    @patch("hej.commands.run.isrunning", return_value=True)
    def test_generate(self, _mock1, _mock2, _mock3):
        result = CliRunner().invoke(cli, ["run", "hello"])
        assert result.exit_code == 0
        assert "Mocked response" in result.output

    @patch("hej.commands.run.isrunning", return_value=True)
    @patch("hej.commands.run.generate", return_value=("ok", {}))
    def test_generate_with_keep_alive(self, mock_gen, _mock_isrunning):
        result = CliRunner().invoke(cli, ["run", "hello", "--keep-alive", "0"])
        assert result.exit_code == 0
        _, kwargs = mock_gen.call_args
        assert kwargs["keep_alive"] == 0

    @patch("hej.commands.run.isrunning", return_value=True)
    @patch("hej.commands.run.generate", return_value=("ok", {}))
    def test_generate_default_keep_alive(self, mock_gen, _mock_isrunning):
        result = CliRunner().invoke(cli, ["run", "hello"])
        assert result.exit_code == 0
        _, kwargs = mock_gen.call_args
        assert kwargs["keep_alive"] is None

    @patch("hej.commands.run.loading")
    @patch("hej.commands.run.generate", return_value=("response", {"eval_count": 42}))
    @patch("hej.commands.run.isrunning", return_value=True)
    def test_generate_with_stats(self, _mock1, _mock2, _mock3):
        result = CliRunner().invoke(cli, ["run", "hello"])
        assert result.exit_code == 0
        assert "response" in result.output
        assert "Tokens: 42" in result.output

    def test_run_help_mentions_keep_alive(self):
        result = CliRunner().invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "keep-alive" in result.output

    @patch(
        "hej.commands.run.config.load",
        return_value={
            "default_model": "phi3",
            "host": "http://localhost:11434",
            "timeout": 600,
            "streaming": True,
            "keep_alive": 0,
            "stats": True,
        },
    )
    @patch("hej.commands.run.loading")
    @patch(
        "hej.commands.run.generate_stream",
        return_value=iter(
            [("token", "Streamed "), ("token", "response"), ("stats", {})]
        ),
    )
    @patch("hej.commands.run.isrunning", return_value=True)
    def test_generate_streaming(self, _mock1, _mock2, _mock3, _mock4):
        result = CliRunner().invoke(cli, ["run", "hello"])
        assert result.exit_code == 0
        assert "Streamed response" in result.output


class TestLs:
    @patch("hej.commands.ls.requests.get")
    def test_ls(self, mock_get):
        mock_get.return_value.json.return_value = {
            "models": [
                {
                    "name": "phi3:latest",
                    "size": 1234,
                    "modified_at": "2024-01-15T10:30:00Z",
                    "digest": "abc123def456",
                    "details": {"quantization_level": "Q4_0", "parameter_size": "3.8B"},
                }
            ]
        }
        result = CliRunner().invoke(cli, ["ls"])
        assert result.exit_code == 0
        assert "phi3" in result.output

    @patch("hej.commands.ls.requests.get")
    def test_ls_empty(self, mock_get):
        mock_get.return_value.json.return_value = {"models": []}
        result = CliRunner().invoke(cli, ["ls"])
        assert result.exit_code == 0
        assert "No models" in result.output

    def test_ls_help(self):
        result = CliRunner().invoke(cli, ["ls", "--help"])
        assert result.exit_code == 0
        assert "List Ollama models" in result.output


class TestPs:
    @patch("hej.commands.ps.requests.get")
    def test_ps(self, mock_get):
        mock_get.return_value.json.return_value = {
            "models": [
                {
                    "name": "llama3.2:latest",
                    "size": 2019393189,
                    "digest": "abc123def456ghi789",
                    "expires_at": "2024-01-15T12:00:00Z",
                    "context_length": 8192,
                    "size_vram": 2019393189,
                    "details": {},
                }
            ]
        }
        result = CliRunner().invoke(cli, ["ps"])
        assert result.exit_code == 0
        assert "llama3.2" in result.output

    @patch("hej.commands.ps.requests.get")
    def test_ps_empty(self, mock_get):
        mock_get.return_value.json.return_value = {"models": []}
        result = CliRunner().invoke(cli, ["ps"])
        assert result.exit_code == 0
        assert "No models in memory" in result.output

    @patch("hej.commands.ps.requests.get")
    def test_ps_today(self, mock_get):
        from datetime import datetime

        today = datetime.today().isoformat()
        mock_get.return_value.json.return_value = {
            "models": [
                {
                    "name": "phi3:latest",
                    "size": 1234,
                    "digest": "abc",
                    "expires_at": today,
                    "context_length": 8192,
                    "size_vram": 1234,
                    "details": {},
                }
            ]
        }
        result = CliRunner().invoke(cli, ["ps"])
        assert result.exit_code == 0

    def test_ps_help(self):
        result = CliRunner().invoke(cli, ["ps", "--help"])
        assert result.exit_code == 0
        assert "List running models" in result.output


class TestShow:
    @patch("hej.commands.show.requests.post")
    def test_show(self, mock_post):
        mock_post.return_value.json.return_value = {
            "details": {
                "family": "llama",
                "parameter_size": "3.8B",
                "quantization_level": "Q4_0",
            },
            "model_info": {
                "llama.context_length": 8192,
                "llama.embedding_length": 4096,
            },
            "capabilities": ["vision", "tools"],
            "parameters": 'stop   "<|endoftext|>"',
            "license": "MIT License\nPermission is hereby granted",
        }
        result = CliRunner().invoke(cli, ["show", "phi3"])
        assert result.exit_code == 0
        assert "architecture" in result.output
        assert "llama" in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_minimal(self, mock_post):
        mock_post.return_value.json.return_value = {
            "details": {},
            "model_info": {},
            "capabilities": [],
            "parameters": "",
            "license": "",
        }
        result = CliRunner().invoke(cli, ["show", "phi3"])
        assert result.exit_code == 0
        assert "unknown" in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_full(self, mock_post):
        mock_post.return_value.json.return_value = {
            "details": {
                "family": "llama",
                "parameter_size": "3.8B",
                "quantization_level": "Q4_0",
            },
            "model_info": {"llama.context_length": 8192},
            "capabilities": ["vision"],
            "parameters": "",
            "license": "",
            "modelfile": "",
            "template": "",
            "tensors": [],
        }
        result = CliRunner().invoke(cli, ["show", "phi3", "--full"])
        assert result.exit_code == 0

    @patch("hej.commands.show.requests.post")
    def test_show_full_with_stop_and_tensors(self, mock_post):
        mock_post.return_value.json.return_value = {
            "details": {
                "family": "llama",
                "parameter_size": "3.8B",
                "quantization_level": "Q4_0",
                "parent_model": "phi3:latest",
                "format": "gguf",
            },
            "model_info": {
                "llama.context_length": 8192,
                "llama.embedding_length": 512,
                "llama.attention.head_count": 32,
                "llama.attention.head_count_kv": 8,
                "llama.block_count": 32,
                "llama.vocab_size": 32000,
            },
            "capabilities": ["vision"],
            "parameters": 'stop "<|endoftext|>"\nstop "<|im_end|>"',
            "license": "MIT",
            "modelfile": "FROM phi3",
            "template": "{{ .Prompt }}",
            "modified_at": "2024-01-15T10:30:00Z",
            "tensors": [
                {"name": "blk.0.attn.weight", "type": "q4_K_M", "shape": [256, 128]},
                {"name": "blk.0.ffn.weight", "type": "f16", "shape": [512, 256]},
            ],
        }
        result = CliRunner().invoke(cli, ["show", "phi3", "--full"])
        assert result.exit_code == 0
        assert "MIT" in result.output
        assert "FROM phi3" in result.output
        assert "{{ .Prompt }}" in result.output
        assert 'stop "<|endoftext|>"' in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_parameters_flag(self, mock_post):
        mock_post.return_value.json.return_value = {
            "parameters": 'stop "<|endoftext|>"',
        }
        result = CliRunner().invoke(cli, ["show", "phi3", "--parameters"])
        assert result.exit_code == 0

    @patch("hej.commands.show.requests.post", side_effect=requests.ConnectionError)
    def test_show_connection_error(self, mock_post):
        result = CliRunner().invoke(cli, ["show", "phi3"])
        assert result.exit_code != 0

    @patch("hej.commands.show.requests.post")
    def test_show_json(self, mock_post):
        mock_post.return_value.json.return_value = {"key": "value"}
        result = CliRunner().invoke(cli, ["show", "phi3", "--json"])
        assert result.exit_code == 0
        assert '"key": "value"' in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_segment_modelfile(self, mock_post):
        mock_post.return_value.json.return_value = {
            "modelfile": "FROM phi3\nSYSTEM hello"
        }
        result = CliRunner().invoke(cli, ["show", "phi3", "--modelfile"])
        assert result.exit_code == 0
        assert "FROM phi3" in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_segment_template(self, mock_post):
        mock_post.return_value.json.return_value = {"template": "{{ .Prompt }}"}
        result = CliRunner().invoke(cli, ["show", "phi3", "--template"])
        assert result.exit_code == 0
        assert "{{ .Prompt }}" in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_segment_license(self, mock_post):
        mock_post.return_value.json.return_value = {"license": "MIT"}
        result = CliRunner().invoke(cli, ["show", "phi3", "--license"])
        assert result.exit_code == 0
        assert "MIT" in result.output

    @patch("hej.commands.show.requests.post")
    def test_show_segment_parameters(self, mock_post):
        mock_post.return_value.json.return_value = {
            "parameters": 'stop "<|endoftext|>"'
        }
        result = CliRunner().invoke(cli, ["show", "phi3", "--parameters"])
        assert result.exit_code == 0

    def test_show_help(self):
        result = CliRunner().invoke(cli, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show information" in result.output
        assert "--full" in result.output
        assert "--json" in result.output


class TestPull:
    @patch("hej.progress.requests.post")
    def test_pull_progress(self, mock_post):
        lines = [
            b'{"status":"pulling manifest"}',
            b'{"status":"pulling digest","digest":"abc","total":100,"completed":30}',
            b'{"status":"pulling digest","digest":"abc","total":100,"completed":60}',
            b'{"status":"pulling digest","digest":"abc","total":100,"completed":100}',
            b'{"status":"success"}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["pull", "phi3"])
        print(result.output)
        assert result.exit_code == 0
        assert "pulling manifest" in result.output
        assert "success" in result.output

    def test_pull_help(self):
        result = CliRunner().invoke(cli, ["pull", "--help"])
        assert result.exit_code == 0
        assert "Download a model" in result.output


class TestPush:
    @patch("hej.progress.requests.post")
    def test_push_progress(self, mock_post):
        lines = [
            b'{"status":"pushing manifest"}',
            b'{"status":"uploading digest","digest":"abc","total":100,"completed":30}',
            b'{"status":"uploading digest","digest":"abc","total":100,"completed":100}',
            b'{"status":"success"}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["push", "phi3"])
        assert result.exit_code == 0
        assert "pushing manifest" in result.output
        assert "success" in result.output

    def test_push_help(self):
        result = CliRunner().invoke(cli, ["push", "--help"])
        assert result.exit_code == 0
        assert "Upload a model" in result.output


class TestCreate:
    @patch("hej.progress.requests.post")
    def test_create(self, mock_post):
        lines = [
            b'{"status":"creating model"}',
            b'{"status":"success"}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["create", "my-model", "--from-model", "phi3"])
        assert result.exit_code == 0
        assert "creating model" in result.output
        assert "success" in result.output

    @patch("hej.progress.requests.post")
    def test_create_all_options(self, mock_post):
        lines = [b'{"status":"success"}']
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        args = [
            "create",
            "my-model",
            "--from-model",
            "phi3",
            "--system",
            "You are a helpful assistant",
            "--template",
            "{{ .Prompt }}",
            "--quantize",
            "q4_K_M",
            "--license",
            "MIT",
        ]
        result = CliRunner().invoke(cli, args)
        assert result.exit_code == 0

    def test_create_help(self):
        result = CliRunner().invoke(cli, ["create", "--help"])
        assert result.exit_code == 0
        assert "Create a model" in result.output


class TestCp:
    @patch("hej.commands.cp.requests.post")
    def test_cp(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["cp", "phi3", "phi3-copy"])
        assert result.exit_code == 0
        assert "phi3" in result.output
        assert "phi3-copy" in result.output

    def test_cp_help(self):
        result = CliRunner().invoke(cli, ["cp", "--help"])
        assert result.exit_code == 0
        assert "Copy a model" in result.output


class TestRm:
    @patch("hej.commands.rm.requests.delete")
    def test_rm_force(self, mock_delete):
        mock_delete.return_value.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["rm", "phi3", "--force"])
        assert result.exit_code == 0
        assert "Deleted phi3" in result.output

    @patch("hej.commands.rm.requests.delete")
    def test_rm_confirm_yes(self, mock_delete):
        mock_delete.return_value.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["rm", "phi3"], input="y\n")
        assert result.exit_code == 0
        assert "Deleted phi3" in result.output

    @patch("hej.commands.rm.requests.delete")
    def test_rm_confirm_no(self, mock_delete):
        result = CliRunner().invoke(cli, ["rm", "phi3"], input="n\n")
        assert result.exit_code != 0

    def test_rm_help(self):
        result = CliRunner().invoke(cli, ["rm", "--help"])
        assert result.exit_code == 0
        assert "Delete a model" in result.output


class TestStop:
    @patch("hej.commands.stop.requests.post")
    def test_stop(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None

        result = CliRunner().invoke(cli, ["stop", "phi3"])
        assert result.exit_code == 0
        assert "Stopped phi3" in result.output

    def test_stop_help(self):
        result = CliRunner().invoke(cli, ["stop", "--help"])
        assert result.exit_code == 0
        assert "Stop a running model" in result.output


class TestErrorPaths:
    @patch("hej.commands.cp.requests.post", side_effect=requests.ConnectionError)
    def test_cp_connection_error(self, _mock):
        result = CliRunner().invoke(cli, ["cp", "a", "b"])
        assert result.exit_code != 0

    @patch("hej.commands.rm.requests.delete", side_effect=requests.ConnectionError)
    def test_rm_connection_error(self, _mock):
        result = CliRunner().invoke(cli, ["rm", "phi3", "--force"])
        assert result.exit_code != 0

    @patch("hej.commands.stop.requests.post", side_effect=requests.ConnectionError)
    def test_stop_connection_error(self, _mock):
        result = CliRunner().invoke(cli, ["stop", "phi3"])
        assert result.exit_code != 0

    @patch("hej.commands.ls.requests.get", side_effect=requests.ConnectionError)
    def test_ls_connection_error(self, _mock):
        result = CliRunner().invoke(cli, ["ls"])
        assert result.exit_code != 0

    @patch("hej.commands.ps.requests.get", side_effect=requests.ConnectionError)
    def test_ps_connection_error(self, _mock):
        result = CliRunner().invoke(cli, ["ps"])
        assert result.exit_code != 0


class TestRunStreamingWithLoading:
    @patch(
        "hej.commands.run.config.load",
        return_value={
            "default_model": "phi3",
            "host": "http://localhost:11434",
            "timeout": 600,
            "streaming": True,
            "keep_alive": None,
            "stats": True,
        },
    )
    @patch("hej.commands.run.loading")
    @patch(
        "hej.commands.run.generate_stream",
        return_value=iter(
            [
                ("loading", True),
                ("token", "Hello"),
                ("stats", {"load_duration": 100, "eval_count": 5}),
            ]
        ),
    )
    @patch("hej.commands.run.isrunning", return_value=True)
    def test_streaming_with_load_duration(self, _mock1, _mock2, _mock3, _mock4):
        result = CliRunner().invoke(cli, ["run", "hello"])
        assert result.exit_code == 0
        assert "Hello" in result.output
        assert "Model is up and working" in result.output
