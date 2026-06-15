"""Tests for hej.commands.template."""

from click.testing import CliRunner

from hej.cli import cli
from hej.commands.template import (
    apply_template,
    load_template,
)


class TestApplyTemplate:
    def test_with_input_placeholder(self):
        result = apply_template("Summarize: {input}", "some text")
        assert result == "Summarize: some text"

    def test_without_placeholder_appends(self):
        result = apply_template("You are helpful.", "hello")
        assert result == "You are helpful.\n\nhello"

    def test_empty_template(self):
        result = apply_template("", "hello")
        assert result == "\n\nhello"


class TestLoadTemplate:
    def test_loads_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "summarize.txt").write_text("Summarize: {input}")
        result = load_template("summarize")
        assert result == "Summarize: {input}"

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        assert load_template("nope") is None


class TestTemplateCreate:
    def test_create_with_content(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        result = CliRunner().invoke(
            cli, ["template", "create", "summarize", "--content", "Summarize: {input}"]
        )
        assert result.exit_code == 0
        assert "Created template 'summarize'" in result.output
        assert (tmp_path / "summarize.txt").read_text() == "Summarize: {input}"

    def test_create_duplicate_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "dup.txt").write_text("existing")
        result = CliRunner().invoke(
            cli, ["template", "create", "dup", "--content", "new"]
        )
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_create_empty_aborts(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        result = CliRunner().invoke(
            cli, ["template", "create", "empty", "--content", ""]
        )
        assert result.exit_code != 0


class TestTemplateList:
    def test_lists_templates(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / "c.json").write_text("{}")
        result = CliRunner().invoke(cli, ["template", "list"])
        assert result.exit_code == 0
        assert "a" in result.output
        assert "b" in result.output
        assert "c" not in result.output

    def test_empty_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["template", "list"])
        assert result.exit_code == 0
        assert "No templates" in result.output

    def test_dir_missing(self, tmp_path, monkeypatch):
        missing = tmp_path / "nonexistent"
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", missing)
        result = CliRunner().invoke(cli, ["template", "list"])
        assert result.exit_code == 0
        assert "No templates" in result.output


class TestTemplateShow:
    def test_show_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "hello.txt").write_text("Hello world")
        result = CliRunner().invoke(cli, ["template", "show", "hello"])
        assert result.exit_code == 0
        assert "Hello world" in result.output

    def test_show_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["template", "show", "nope"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestTemplateDelete:
    def test_delete_force(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "del.txt").write_text("bye")
        result = CliRunner().invoke(cli, ["template", "delete", "del", "--force"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert not (tmp_path / "del.txt").exists()

    def test_delete_confirm_yes(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "del2.txt").write_text("bye")
        result = CliRunner().invoke(cli, ["template", "delete", "del2"], input="y\n")
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_delete_confirm_no(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        (tmp_path / "del3.txt").write_text("bye")
        result = CliRunner().invoke(cli, ["template", "delete", "del3"], input="n\n")
        assert result.exit_code != 0

    def test_delete_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hej.commands.template.TEMPLATES_DIR", tmp_path)
        result = CliRunner().invoke(cli, ["template", "delete", "nope", "--force"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestTemplateHelp:
    def test_help(self):
        result = CliRunner().invoke(cli, ["template", "--help"])
        assert result.exit_code == 0
        assert "Manage prompt templates" in result.output

    def test_create_help(self):
        result = CliRunner().invoke(cli, ["template", "create", "--help"])
        assert result.exit_code == 0
        assert "Create" in result.output

    def test_list_help(self):
        result = CliRunner().invoke(cli, ["template", "list", "--help"])
        assert result.exit_code == 0

    def test_show_help(self):
        result = CliRunner().invoke(cli, ["template", "show", "--help"])
        assert result.exit_code == 0

    def test_delete_help(self):
        result = CliRunner().invoke(cli, ["template", "delete", "--help"])
        assert result.exit_code == 0
