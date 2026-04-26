"""Command-line interface with anonymize, deanonymize, and detect subcommands.

File I/O is tolerant on read (UTF-8 with or without BOM, and UTF-16 LE/BE
when a BOM is present — this matters on Windows where PowerShell 5.1 writes
UTF-16 LE by default) and strict on write (UTF-8 without BOM, the canonical
modern default). Files without a BOM that are not UTF-8 are rejected
loudly — silent guessing at encodings leaks data.

All three subcommands accept ``-`` as the input path to read from stdin;
``deanonymize --output -`` additionally means "write to stdout" (equivalent
to omitting ``--output``). ``detect`` always prints to stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from llm_safe_pl import __version__
from llm_safe_pl.models import Mapping
from llm_safe_pl.shield import Shield

app = typer.Typer(
    help="llm-safe-pl — reversible PII anonymization for Polish documents.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """llm-safe-pl — reversible PII anonymization for Polish documents."""


_DEFAULT_MAX_BYTES = 64 * 1024 * 1024  # 64 MiB; protects against unbounded stdin


def _read_text(source: Path, max_bytes: int = _DEFAULT_MAX_BYTES) -> str:
    """Read text from a file path, or from stdin when ``source`` is ``-``.

    Accepts UTF-8 (±BOM) and UTF-16 (±endianness) with BOM in either case.
    Refuses inputs larger than ``max_bytes`` to prevent unbounded memory use.
    """
    if str(source) == "-":
        data = sys.stdin.buffer.read(max_bytes + 1)
    else:
        size = source.stat().st_size
        if size > max_bytes:
            raise typer.BadParameter(
                f"{source} is {size} bytes; --max-bytes={max_bytes}",
            )
        data = source.read_bytes()
    if len(data) > max_bytes:
        raise typer.BadParameter(
            f"input exceeds --max-bytes={max_bytes}",
        )
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def _check_overwrite(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise typer.BadParameter(
            f"{path} exists; pass --force to overwrite",
        )


@app.command("anonymize")
def anonymize_cmd(
    input_file: Annotated[Path, typer.Argument(help="Text file to anonymize (use - for stdin).")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Path for the anonymized text.")],
    mapping: Annotated[
        Path, typer.Option("--mapping", "-m", help="Path to write the Mapping JSON.")
    ],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite output and mapping files if they exist."),
    ] = False,
    max_bytes: Annotated[
        int, typer.Option("--max-bytes", help="Refuse inputs larger than this many bytes.")
    ] = _DEFAULT_MAX_BYTES,
) -> None:
    """Anonymize a text file; writes rewritten text and a reversible mapping."""
    _check_overwrite(output, force)
    _check_overwrite(mapping, force)
    text = _read_text(input_file, max_bytes=max_bytes)
    shield = Shield()
    result = shield.anonymize(text)
    output.write_text(result.text, encoding="utf-8")
    mapping.write_text(result.mapping.to_json(), encoding="utf-8")


@app.command("deanonymize")
def deanonymize_cmd(
    input_file: Annotated[Path, typer.Argument(help="Anonymized text file (use - for stdin).")],
    mapping: Annotated[
        Path,
        typer.Option("--mapping", "-m", help="Mapping JSON produced by `anonymize`."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write restored text here (stdout if omitted or -)."),
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Overwrite output file if it exists.")
    ] = False,
    max_bytes: Annotated[
        int, typer.Option("--max-bytes", help="Refuse inputs larger than this many bytes.")
    ] = _DEFAULT_MAX_BYTES,
) -> None:
    """Deanonymize a text file using a saved mapping."""
    if output is not None and str(output) != "-":
        _check_overwrite(output, force)
    text = _read_text(input_file, max_bytes=max_bytes)
    loaded_mapping = Mapping.from_json(_read_text(mapping, max_bytes=max_bytes))
    shield = Shield(mapping=loaded_mapping)
    restored = shield.deanonymize(text)
    if output is None or str(output) == "-":
        typer.echo(restored)
    else:
        output.write_text(restored, encoding="utf-8")


@app.command("detect")
def detect_cmd(
    input_file: Annotated[Path, typer.Argument(help="File to scan for PII (use - for stdin).")],
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format: json or text.")
    ] = "json",
    max_bytes: Annotated[
        int, typer.Option("--max-bytes", help="Refuse inputs larger than this many bytes.")
    ] = _DEFAULT_MAX_BYTES,
) -> None:
    """Detect PII without anonymizing; prints to stdout."""
    text = _read_text(input_file, max_bytes=max_bytes)
    shield = Shield()
    matches = shield.detect(text)
    fmt = output_format.lower()
    if fmt == "json":
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
    elif fmt == "text":
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
