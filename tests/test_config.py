"""Tests for hej.config."""

from unittest.mock import mock_open, patch

from hej.config import (
    DEFAULTS,
    _find_config,
    _parse_duration,
    _resolve_host,
    _validate,
    load,
)


class TestParseDuration:
    def test_plain_integer(self):
        assert _parse_duration("120") == 120

    def test_invalid(self):
        assert _parse_duration("hello") is None

    def test_empty(self):
        assert _parse_duration("") is None


class TestResolveHost:
    def test_adds_http_when_missing(self):
        assert _resolve_host("0.0.0.0:11434") == "http://0.0.0.0:11434"

    def test_preserves_http(self):
        assert _resolve_host("http://foo:11434") == "http://foo:11434"

    def test_preserves_https(self):
        assert _resolve_host("https://foo:11434") == "https://foo:11434"

    def test_empty_string(self):
        assert _resolve_host("") == ""

    def test_strips_trailing_slash(self):
        assert _resolve_host("http://foo:11434/") == "http://foo:11434"

    def test_raises_on_spaces(self):
        import pytest

        with pytest.raises(ValueError, match="Invalid host"):
            _resolve_host("bad host:11434")


class TestValidate:
    def test_passes_good_config(self):
        cfg = DEFAULTS.copy()
        result = _validate(cfg)
        assert result == cfg

    def test_resets_bad_timeout(self):
        cfg = DEFAULTS.copy()
        cfg["timeout"] = 0
        result = _validate(cfg)
        assert result["timeout"] == DEFAULTS["timeout"]

    def test_resets_empty_host(self):
        cfg = DEFAULTS.copy()
        cfg["host"] = ""
        result = _validate(cfg)
        assert result["host"] == DEFAULTS["host"]


class TestFindConfig:
    @patch("hej.config.CONFIG_PATH")
    def test_finds_existing(self, mock_path):
        mock_path.exists.return_value = True
        assert _find_config() is not None

    @patch("hej.config.CONFIG_PATH")
    def test_returns_none_when_missing(self, mock_path):
        mock_path.exists.return_value = False
        assert _find_config() is None


class TestLoad:
    @patch("hej.config._find_config", return_value=None)
    def test_no_config_no_env_returns_defaults(self, mock_find):
        result = load()
        assert result == DEFAULTS

    @patch("hej.config._find_config")
    def test_config_overrides_defaults(self, mock_find):
        mock_find.return_value.exists.return_value = True
        toml_data = b'default_model = "llama3"\nhost = "http://other:11434"'
        with patch("builtins.open", mock_open(read_data=toml_data)):
            result = load()
        assert result["default_model"] == "llama3"
        assert result["host"] == "http://other:11434"
        assert result["timeout"] == 600
        assert result["streaming"] is False
        assert result["stats"] is True
        assert result["keep_alive"] is None

    @patch("hej.config._find_config")
    def test_partial_config_merges_with_defaults(self, mock_find):
        mock_find.return_value.exists.return_value = True
        toml_data = b"timeout = 30"
        with patch("builtins.open", mock_open(read_data=toml_data)):
            result = load()
        assert result["timeout"] == 30
        assert result["default_model"] == "phi3"
        assert result["host"] == "http://localhost:11434"

    @patch("hej.config._find_config")
    def test_config_bad_timeout_resets_to_default(self, mock_find):
        mock_find.return_value.exists.return_value = True
        toml_data = b"timeout = -5"
        with patch("builtins.open", mock_open(read_data=toml_data)):
            result = load()
        assert result["timeout"] == DEFAULTS["timeout"]

    @patch("hej.config._find_config")
    def test_malformed_toml_returns_defaults(self, mock_find):
        mock_find.return_value.exists.return_value = True
        toml_data = b"this is not valid toml ====="
        with patch("builtins.open", mock_open(read_data=toml_data)):
            result = load()
        assert result == DEFAULTS

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_host_overrides_default(self, mock_find):
        with patch.dict("os.environ", {"OLLAMA_HOST": "0.0.0.0:11434"}):
            result = load()
        assert result["host"] == "http://0.0.0.0:11434"

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_host_bad_url_ignored(self, mock_find):
        with patch.dict("os.environ", {"OLLAMA_HOST": "bad host"}):
            result = load()
        assert result["host"] == DEFAULTS["host"]

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_timeout_seconds(self, mock_find):
        with patch.dict("os.environ", {"OLLAMA_LOAD_TIMEOUT": "120"}):
            result = load()
        assert result["timeout"] == 120

    @patch("hej.config._find_config", return_value=None)
    def test_invalid_env_var_timeout_ignored(self, mock_find):
        with patch.dict("os.environ", {"OLLAMA_LOAD_TIMEOUT": "not-a-number"}):
            result = load()
        assert result["timeout"] == 600

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_keep_alive(self, mock_find):
        with patch.dict("os.environ", {"OLLAMA_KEEP_ALIVE": "10m"}):
            result = load()
        assert result.get("keep_alive") == "10m"

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_hej_default_model(self, mock_find):
        with patch.dict("os.environ", {"HEJ_DEFAULT_MODEL": "custom"}):
            result = load()
        assert result["default_model"] == "custom"

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_hej_streaming(self, mock_find):
        with patch.dict("os.environ", {"HEJ_STREAMING": "true"}):
            result = load()
        assert result["streaming"] is True

    @patch("hej.config._find_config", return_value=None)
    def test_env_var_hej_stats(self, mock_find):
        with patch.dict("os.environ", {"HEJ_STATS": "false"}):
            result = load()
        assert result["stats"] is False

    @patch("hej.config._find_config")
    def test_env_var_overrides_config_file(self, mock_find):
        mock_find.return_value.exists.return_value = True
        toml_data = b'host = "http://config-host:11434"'
        with patch("builtins.open", mock_open(read_data=toml_data)):
            with patch.dict("os.environ", {"OLLAMA_HOST": "http://env-host:11434"}):
                result = load()
        assert result["host"] == "http://env-host:11434"
