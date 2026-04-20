"""Command-line interface. Subcommands land in Phase 5."""

import typer

app = typer.Typer(
    help="llm-safe-pl — reversible PII anonymization for Polish documents.",
    no_args_is_help=True,
)


@app.callback()
def _main() -> None:
    """Anchor callback so the Typer app is valid before any subcommands exist."""


if __name__ == "__main__":
    app()
