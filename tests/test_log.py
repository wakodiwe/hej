"""Tests for hej.log."""

import logging

from hej.log import _ColorFormatter, setup


class TestSetup:
    def test_quiet(self):
        setup(quiet=True)
        root = logging.getLogger()
        assert root.level == logging.ERROR

    def test_verbose_info(self):
        setup(verbosity=1)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_verbose_debug(self):
        setup(verbosity=2)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_no_color(self):
        setup(color=False)
        root = logging.getLogger()
        assert len(root.handlers) > 0

    def test_default(self):
        setup()
        root = logging.getLogger()
        assert root.level == logging.WARNING


class TestColorFormatter:
    def test_format(self):
        fmt = _ColorFormatter("%(levelname)s %(message)s")
        record = logging.LogRecord("test", logging.WARNING, "", 0, "msg", (), None)
        output = fmt.format(record)
        assert "\033[33m" in output
        assert "\033[0m" in output

    def test_unknown_level(self):
        fmt = _ColorFormatter("%(levelname)s %(message)s")
        record = logging.LogRecord("test", logging.DEBUG, "", 0, "msg", (), None)
        record.levelname = "TRACE"
        output = fmt.format(record)
        assert "TRACE" in output
