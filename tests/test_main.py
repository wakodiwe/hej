"""Tests for hej.cli and __main__."""

from unittest.mock import patch

from hej.cli import main


class TestMain:
    @patch("hej.__main__.main")
    def test_module_entry(self, mock_main):
        from hej.__main__ import main as entry_main
        entry_main()
        mock_main.assert_called_once()


class TestCliMain:
    @patch("hej.cli.cli")
    def test_main_calls_cli(self, mock_cli):
        main()
        mock_cli.assert_called_once_with(obj={})
