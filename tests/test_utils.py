"""Tests for hej.utils."""

import pytest

from hej.utils import fmt_date, fmt_size


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
