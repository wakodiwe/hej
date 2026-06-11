"""Tests for hej.api functions."""

from unittest.mock import patch

import pytest
import requests

from hej.api import (
    extract_metadata,
    generate,
    generate_stream,
    isrunning,
    print_stats,
)


class TestIsRunning:
    @patch("hej.api.requests.get")
    def test_running(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        assert isrunning("http://localhost:11434") is True

    @patch("hej.api.requests.get", side_effect=requests.ConnectionError)
    def test_not_running(self, mock_get):
        assert isrunning("http://localhost:11434") is False

    @patch("hej.api.requests.get", side_effect=requests.exceptions.InvalidURL)
    def test_invalid_url(self, mock_get):
        assert isrunning("http://bad") is False


class TestExtractMetadata:
    def test_full(self):
        data = {
            "total_duration": 1_000_000_000,
            "eval_count": 42,
            "eval_duration": 500_000_000,
            "load_duration": 100_000_000,
        }
        result = extract_metadata(data)
        assert result["total_duration_ns"] == 1_000_000_000
        assert result["eval_count"] == 42

    def test_empty(self):
        result = extract_metadata({})
        assert result["eval_count"] is None


class TestPrintStats:
    def test_with_eval_count(self):
        print_stats(
            {
                "eval_count": 42,
                "total_duration_ns": 2_000_000_000,
                "eval_duration_ns": 1_000_000_000,
            }
        )

    def test_without_eval_count(self):
        print_stats({})

    def test_zero_duration(self):
        print_stats({"eval_count": 10})


class TestGenerate:
    @patch("hej.api.requests.post")
    def test_generate_success(self, mock_post):
        mock_post.return_value.json.return_value = {
            "response": "Hello!",
            "total_duration": 1_000_000_000,
        }
        mock_post.return_value.raise_for_status.return_value = None
        text, meta = generate("phi3", "hi", "http://localhost:11434", 600)
        assert text == "Hello!"

    @patch("hej.api.requests.post", side_effect=requests.ConnectionError)
    def test_generate_connection_error(self, mock_post):
        with pytest.raises(SystemExit):
            generate("phi3", "hi", "http://localhost:11434", 600)

    @patch("hej.api.requests.post")
    def test_generate_with_keep_alive(self, mock_post):
        mock_post.return_value.json.return_value = {
            "response": "ok",
            "total_duration": 0,
        }
        mock_post.return_value.raise_for_status.return_value = None
        text, meta = generate("phi3", "hi", "http://localhost:11434", 600, keep_alive=0)
        assert text == "ok"
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["keep_alive"] == 0


class TestGenerateStream:
    @patch("hej.api.requests.post")
    def test_stream_success(self, mock_post):
        lines = [
            b'{"response":"Hello","done":false}',
            b'{"response":" world","done":false}',
            b'{"response":"","done":true,"total_duration":1000,'
            b'"eval_count":2,"eval_duration":500}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        results = list(generate_stream("phi3", "hi", "http://localhost:11434", 600))
        assert ("token", "Hello") in results
        assert ("token", " world") in results
        assert any(t[0] == "stats" for t in results)
        assert any(t[0] == "loading" for t in results)

    @patch("hej.api.requests.post", side_effect=requests.ConnectionError)
    def test_stream_connection_error(self, mock_post):
        with pytest.raises(SystemExit):
            list(generate_stream("phi3", "hi", "http://localhost:11434", 600))

    @patch("hej.api.requests.post")
    def test_stream_with_keep_alive(self, mock_post):
        lines = [
            b'{"response":"ok","done":true,"total_duration":0,'
            b'"eval_count":1,"eval_duration":0}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        results = list(
            generate_stream(
                "phi3", "hi", "http://localhost:11434", 600, keep_alive="10m"
            )
        )
        assert any(t[0] == "token" for t in results)
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["keep_alive"] == "10m"

    @patch("hej.api.requests.post")
    def test_stream_with_empty_lines(self, mock_post):
        lines = [
            b"",
            b'{"response":"ok","done":true,"total_duration":0,'
            b'"eval_count":1,"eval_duration":0}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        results = list(generate_stream("phi3", "hi", "http://localhost:11434", 600))
        tokens = [t for t in results if t[0] == "token"]
        assert len(tokens) == 1

    @patch("hej.api.requests.post")
    def test_stream_skips_malformed(self, mock_post):
        lines = [
            b"not json",
            b'{"response":"ok","done":true,"total_duration":0}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        results = list(generate_stream("phi3", "hi", "http://localhost:11434", 600))
        tokens = [t for t in results if t[0] == "token"]
        assert len(tokens) == 1
