"""Tests for hej.commands.session."""

from pathlib import Path

from click.testing import CliRunner

from hej.cli import cli
from hej.commands.session import (
    load_session,
    save_session,
)


class TestSaveSession:
    def test_saves_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        path = save_session(
            "test-session", "phi3", [{"role": "user", "content": "hello"}]
        )
        assert Path(path).exists()
        data = load_session("test-session")
        assert data is not None
        assert data["model"] == "phi3"
        assert data["id"] == "test-session"
        assert data["messages"] == [{"role": "user", "content": "hello"}]

    def test_creates_dir_if_missing(self, tmp_path, monkeypatch):
        new_dir = tmp_path / "sessions"
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", new_dir)
        assert not new_dir.exists()
        save_session("new", "phi3", [])
        assert new_dir.exists()

    def test_multiple_messages(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        msgs = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        save_session("multi", "phi3", msgs)
        data = load_session("multi")
        assert len(data["messages"]) == 2


class TestLoadSession:
    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        assert load_session("nope") is None

    def test_loads_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("exists", "phi3", [{"role": "user", "content": "hello"}])
        data = load_session("exists")
        assert data is not None
        assert data["messages"][0]["content"] == "hello"


class TestSessionList:
    def test_lists_sessions(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("alpha", "phi3", [{"role": "user", "content": "a"}])
        save_session("beta", "phi3", [{"role": "user", "content": "b"}])
        result = CliRunner().invoke(cli, ["session", "list"])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output
        assert "1 msgs" in result.output

    def test_empty_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["session", "list"])
        assert result.exit_code == 0
        assert "No saved sessions" in result.output

    def test_dir_missing(self, tmp_path, monkeypatch):
        missing = tmp_path / "nonexistent"
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", missing)
        result = CliRunner().invoke(cli, ["session", "list"])
        assert result.exit_code == 0
        assert "No saved sessions" in result.output


class TestSessionLoad:
    def test_load_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("my-session", "phi3", [{"role": "user", "content": "hi"}])
        result = CliRunner().invoke(cli, ["session", "load", "my-session"])
        assert result.exit_code == 0
        assert "phi3" in result.output
        assert "hi" in result.output

    def test_load_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["session", "load", "nope"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestSessionExport:
    def test_export_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("ex", "phi3", [{"role": "user", "content": "hello"}])
        result = CliRunner().invoke(
            cli, ["session", "export", "ex", "--format", "json"]
        )
        assert result.exit_code == 0
        assert '"model": "phi3"' in result.output

    def test_export_md(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("ex", "phi3", [{"role": "user", "content": "hello"}])
        result = CliRunner().invoke(cli, ["session", "export", "ex", "--format", "md"])
        assert result.exit_code == 0
        assert "USER" in result.output
        assert "hello" in result.output

    def test_export_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["session", "export", "nope"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestSessionDelete:
    def test_delete_force(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("del", "phi3", [])
        result = CliRunner().invoke(cli, ["session", "delete", "del", "--force"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert not (tmp_path / "del.json").exists()

    def test_delete_confirm_yes(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("del2", "phi3", [])
        result = CliRunner().invoke(cli, ["session", "delete", "del2"], input="y\n")
        assert result.exit_code == 0

    def test_delete_confirm_no(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("del3", "phi3", [])
        result = CliRunner().invoke(cli, ["session", "delete", "del3"], input="n\n")
        assert result.exit_code != 0

    def test_delete_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["session", "delete", "nope", "--force"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestSessionSearch:
    def test_search_finds_match(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session(
            "s1", "phi3", [{"role": "user", "content": "how about the weather?"}]
        )
        save_session("s2", "phi3", [{"role": "user", "content": "what is AI?"}])
        result = CliRunner().invoke(cli, ["session", "search", "weather"])
        assert result.exit_code == 0
        assert "s1" in result.output
        assert "weather" in result.output
        assert "s2" not in result.output

    def test_search_no_match(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", tmp_path)
        save_session("s1", "phi3", [{"role": "user", "content": "hello"}])
        result = CliRunner().invoke(cli, ["session", "search", "nope"])
        assert result.exit_code == 0
        assert "No sessions match" in result.output

    def test_search_empty_dir(self, tmp_path, monkeypatch):
        missing = tmp_path / "nonexistent"
        monkeypatch.setattr("hej.commands.session.SESSIONS_DIR", missing)
        result = CliRunner().invoke(cli, ["session", "search", "foo"])
        assert result.exit_code == 0
        assert "No saved sessions" in result.output


class TestSessionHelp:
    def test_help(self):
        result = CliRunner().invoke(cli, ["session", "--help"])
        assert result.exit_code == 0
        assert "Manage saved chat sessions" in result.output

    def test_list_help(self):
        result = CliRunner().invoke(cli, ["session", "list", "--help"])
        assert result.exit_code == 0

    def test_load_help(self):
        result = CliRunner().invoke(cli, ["session", "load", "--help"])
        assert result.exit_code == 0

    def test_export_help(self):
        result = CliRunner().invoke(cli, ["session", "export", "--help"])
        assert result.exit_code == 0

    def test_delete_help(self):
        result = CliRunner().invoke(cli, ["session", "delete", "--help"])
        assert result.exit_code == 0

    def test_search_help(self):
        result = CliRunner().invoke(cli, ["session", "search", "--help"])
        assert result.exit_code == 0
