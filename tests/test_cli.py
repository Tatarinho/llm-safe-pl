"""Smoke tests for the Typer CLI entry point."""

from typer.testing import CliRunner

from llm_safe_pl import __version__
from llm_safe_pl.cli import app


def test_cli_help_exits_zero() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "llm-safe-pl" in result.output


def test_cli_no_args_shows_help() -> None:
    result = CliRunner().invoke(app, [])
    assert "Usage" in result.output


def test_cli_version_flag_prints_version() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_short_version_flag_prints_version() -> None:
    result = CliRunner().invoke(app, ["-V"])
    assert result.exit_code == 0
    assert __version__ in result.output
