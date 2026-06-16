"""Tests for hej.utils."""

from pathlib import Path

import pytest

from hej.utils import copy_to_clipboard, fmt_date, fmt_size, open_in_editor


class TestFmtDate:
    def test_datetime(self):
        result = fmt_date("2024-01-15T10:30:00")
        assert result == "15.01.24, 10:30"

    def test_date(self):
        result = fmt_date("2024-01-15T10:30:00", format_type="date")
        assert result == "15.01.24"

    def test_time(self):
        result = fmt_date("2024-01-15T10:30:00", format_type="time")
        assert result == "10:30"

    def test_invalid_format(self):
        result = fmt_date("2024-01-15T10:30:00", format_type="invalid")
        assert result == ""

    def test_invalid_date_string(self):
        result = fmt_date("not-a-date")
        assert result == ""

    def test_invalid_date_string_logs(self, caplog):
        import logging

        caplog.set_level(logging.WARNING)
        fmt_date("garbage")
        assert "invalid date string" in caplog.text


class TestFmtSize:
    def test_zero(self):
        assert fmt_size(0) == "0.0B"

    def test_bytes(self):
        assert fmt_size(500) == "500.0B"

    def test_kilobytes(self):
        assert fmt_size(2048) == "2.0K"

    def test_megabytes(self):
        assert fmt_size(1048576) == "1.0M"

    def test_gigabytes(self):
        assert fmt_size(1073741824) == "1.0G"

    def test_terabytes(self):
        assert fmt_size(1099511627776) == "1.0T"

    def test_petabytes(self):
        assert fmt_size(1125899906842624) == "1.0P"

    def test_exabytes(self):
        assert fmt_size(1152921504606846976) == "1.0E"

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            fmt_size(-1)

    def test_beyond_exabytes(self):
        result = fmt_size(2**70)
        assert result.endswith("E")


class TestCopyToClipboard:
    def test_no_tool_found(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("shutil.which", lambda _: None)
            assert copy_to_clipboard("hello") is False

    def test_with_xclip(self) -> None:
        import subprocess

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("shutil.which", lambda x: x if x == "xclip" else None)
            orig = subprocess.run

            def fake_run(cmd, **kw):
                assert cmd == ["xclip", "-selection", "clipboard"]
                assert kw.get("input") == "hello"
                return orig(["true"])

            mp.setattr("subprocess.run", fake_run)
            assert copy_to_clipboard("hello") is True


class TestOpenInEditor:
    def test_no_editor(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("EDITOR", raising=False)
            mp.delenv("VISUAL", raising=False)
            mp.setattr("shutil.which", lambda _: None)
            assert open_in_editor("text") is False

    def test_with_editor(self) -> None:
        import subprocess

        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("EDITOR", "cat")
            mp.setattr("shutil.which", lambda x: x if x == "cat" else None)

            def fake_call(args, **kw):
                Path(args[-1]).unlink(missing_ok=True)
                return 0

            mp.setattr("subprocess.call", fake_call)
            assert open_in_editor("hello") is True
