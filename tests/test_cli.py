"""Smoke tests for the Typer CLI entry point."""

from typer.testing import CliRunner

from llm_safe_pl.cli import app


def test_cli_help_exits_zero() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "llm-safe-pl" in result.output


def test_cli_no_args_shows_help() -> None:
    result = CliRunner().invoke(app, [])
    assert "Usage" in result.output
