"""Command-line interface with anonymize, deanonymize, and detect subcommands.

File I/O is tolerant on read (UTF-8 with or without BOM, and UTF-16 LE/BE
when a BOM is present — this matters on Windows where PowerShell 5.1 writes
UTF-16 LE by default) and strict on write (UTF-8 without BOM, the canonical
modern default). Files without a BOM that are not UTF-8 are rejected
loudly — silent guessing at encodings leaks data.

``deanonymize`` prints to stdout when ``--output`` is omitted; ``detect``
always prints to stdout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from llm_safe_pl.models import Mapping
from llm_safe_pl.shield import Shield

app = typer.Typer(
    help="llm-safe-pl — reversible PII anonymization for Polish documents.",
    no_args_is_help=True,
)


def _read_text(path: Path) -> str:
    """Read a text file, accepting UTF-8 (±BOM) and UTF-16 (±endianness) with BOM."""
    data = path.read_bytes()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


@app.command("anonymize")
def anonymize_cmd(
    input_file: Annotated[Path, typer.Argument(help="Text file to anonymize.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Path for the anonymized text.")],
    mapping: Annotated[
        Path, typer.Option("--mapping", "-m", help="Path to write the Mapping JSON.")
    ],
) -> None:
    """Anonymize a text file; writes rewritten text and a reversible mapping."""
    text = _read_text(input_file)
    shield = Shield()
    result = shield.anonymize(text)
    output.write_text(result.text, encoding="utf-8")
    mapping.write_text(result.mapping.to_json(), encoding="utf-8")


@app.command("deanonymize")
def deanonymize_cmd(
    input_file: Annotated[Path, typer.Argument(help="Anonymized text file.")],
    mapping: Annotated[
        Path,
        typer.Option("--mapping", "-m", help="Mapping JSON produced by `anonymize`."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write restored text here (stdout if omitted)."),
    ] = None,
) -> None:
    """Deanonymize a text file using a saved mapping."""
    text = _read_text(input_file)
    loaded_mapping = Mapping.from_json(_read_text(mapping))
    shield = Shield(mapping=loaded_mapping)
    restored = shield.deanonymize(text)
    if output is not None:
        output.write_text(restored, encoding="utf-8")
    else:
        typer.echo(restored)


@app.command("detect")
def detect_cmd(
    input_file: Annotated[Path, typer.Argument(help="File to scan for PII.")],
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format: json or text.")
    ] = "json",
) -> None:
    """Detect PII without anonymizing; prints to stdout."""
    text = _read_text(input_file)
    shield = Shield()
    matches = shield.detect(text)
    if output_format == "json":
        data = [
            {
                "type": m.type.value,
                "value": m.value,
                "start": m.start,
                "end": m.end,
                "detector": m.detector,
            }
            for m in matches
        ]
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    elif output_format == "text":
        for m in matches:
            typer.echo(f"{m.type.value}\t{m.start}-{m.end}\t{m.value}")
    else:
        typer.echo(
            f"Unknown format: {output_format!r}. Expected 'json' or 'text'.",
            err=True,
        )
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
