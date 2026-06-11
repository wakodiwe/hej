"""Tests for hej.progress."""

import pytest
import requests
from unittest.mock import patch

from hej.progress import stream_operation


class TestStreamOperation:
    @patch("hej.progress.requests.post")
    def test_empty_lines_skipped(self, mock_post):
        lines = [
            b'',
            b'{"status":"success"}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        stream_operation("/api/pull", "phi3", "http://localhost:11434", 600)

    @patch("hej.progress.requests.post")
    def test_malformed_json_skipped(self, mock_post):
        lines = [
            b'not valid json',
            b'{"status":"success"}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None
        with patch("hej.progress.logger") as mock_logger:
            stream_operation("/api/pull", "phi3", "http://localhost:11434", 600)
            mock_logger.warning.assert_called_once()

    @patch("hej.progress.requests.post", side_effect=requests.ConnectionError)
    def test_connection_error(self, mock_post):
        with pytest.raises(SystemExit):
            stream_operation("/api/pull", "phi3", "http://localhost:11434", 600)

    @patch("hej.progress.requests.post")
    def test_digest_progress(self, mock_post):
        lines = [
            b'{"status":"pulling","digest":"abc","total":100,"completed":30}',
            b'{"status":"pulling","digest":"abc","total":100,"completed":100}',
            b'{"status":"success"}',
        ]
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status.return_value = None

        stream_operation("/api/pull", "phi3", "http://localhost:11434", 600)

    @patch("hej.progress.requests.post")
    def test_custom_payload(self, mock_post):
        mock_resp = mock_post.return_value.__enter__.return_value
        mock_resp.iter_lines.return_value = [b'{"status":"success"}']
        mock_resp.raise_for_status.return_value = None

        stream_operation("/api/pull", "phi3", "http://localhost:11434", 600, payload={"model": "phi3", "custom": True})
