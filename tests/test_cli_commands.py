"""End-to-end tests for the CLI subcommands."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from llm_safe_pl.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestAnonymizeCommand:
    def test_writes_anonymized_text_and_mapping(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        input_file.write_text("PESEL 44051401359", encoding="utf-8")
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        result = runner.invoke(
            app,
            [
                "anonymize",
                str(input_file),
                "--output",
                str(output_file),
                "--mapping",
                str(mapping_file),
            ],
        )

        assert result.exit_code == 0
        assert "[PESEL_001]" in output_file.read_text(encoding="utf-8")
        data = json.loads(mapping_file.read_text(encoding="utf-8"))
        assert data["schema_version"] == 1
        assert any(e["token"] == "[PESEL_001]" for e in data["entries"])

    def test_preserves_surrounding_text(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        input_file.write_text("Przed 44051401359 po.", encoding="utf-8")
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        result = runner.invoke(
            app,
            [
                "anonymize",
                str(input_file),
                "-o",
                str(output_file),
                "-m",
                str(mapping_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.read_text(encoding="utf-8") == "Przed [PESEL_001] po."

    def test_missing_required_flags_fails(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        input_file.write_text("x", encoding="utf-8")
        result = runner.invoke(app, ["anonymize", str(input_file)])
        assert result.exit_code != 0


class TestDeanonymizeCommand:
    def test_roundtrip_via_cli(self, runner: CliRunner, tmp_path: Path) -> None:
        original = "PESEL 44051401359 i email jan@example.pl."
        input_file = tmp_path / "in.txt"
        input_file.write_text(original, encoding="utf-8")
        anon_file = tmp_path / "anon.txt"
        mapping_file = tmp_path / "mapping.json"

        anon_result = runner.invoke(
            app,
            [
                "anonymize",
                str(input_file),
                "-o",
                str(anon_file),
                "-m",
                str(mapping_file),
            ],
        )
        assert anon_result.exit_code == 0

        restored_file = tmp_path / "restored.txt"
        deanon_result = runner.invoke(
            app,
            [
                "deanonymize",
                str(anon_file),
                "-m",
                str(mapping_file),
                "-o",
                str(restored_file),
            ],
        )
        assert deanon_result.exit_code == 0
        assert restored_file.read_text(encoding="utf-8") == original

    def test_prints_to_stdout_when_no_output(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "in.txt"
        input_file.write_text("44051401359", encoding="utf-8")
        anon_file = tmp_path / "anon.txt"
        mapping_file = tmp_path / "mapping.json"

        runner.invoke(
            app,
            [
                "anonymize",
                str(input_file),
                "-o",
                str(anon_file),
                "-m",
                str(mapping_file),
            ],
        )

        result = runner.invoke(
            app,
            ["deanonymize", str(anon_file), "-m", str(mapping_file)],
        )
        assert result.exit_code == 0
        assert "44051401359" in result.output


class TestDetectCommand:
    def test_json_format_default(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "in.txt"
        input_file.write_text("PESEL 44051401359", encoding="utf-8")

        result = runner.invoke(app, ["detect", str(input_file)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["type"] == "pesel"
        assert data[0]["value"] == "44051401359"
        assert data[0]["detector"] == "pesel"

    def test_json_format_explicit(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "in.txt"
        input_file.write_text("PESEL 44051401359", encoding="utf-8")

        result = runner.invoke(app, ["detect", str(input_file), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1

    def test_text_format(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "in.txt"
        input_file.write_text("PESEL 44051401359", encoding="utf-8")

        result = runner.invoke(app, ["detect", str(input_file), "--format", "text"])
        assert result.exit_code == 0
        assert "pesel" in result.output
        assert "44051401359" in result.output

    def test_invalid_format_exits_with_code_2(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "in.txt"
        input_file.write_text("hi", encoding="utf-8")

        result = runner.invoke(app, ["detect", str(input_file), "--format", "xml"])
        assert result.exit_code == 2

    def test_detect_empty_file_returns_empty_list(self, runner: CliRunner, tmp_path: Path) -> None:
        input_file = tmp_path / "in.txt"
        input_file.write_text("nothing sensitive here", encoding="utf-8")

        result = runner.invoke(app, ["detect", str(input_file)])
        assert result.exit_code == 0
        assert json.loads(result.output) == []


class TestStdinStdout:
    """CLI accepts `-` as input path (stdin) and deanonymize `-o -` as stdout."""

    def test_anonymize_reads_from_stdin(self, runner: CliRunner, tmp_path: Path) -> None:
        output_file = tmp_path / "out.txt"
        mapping_file = tmp_path / "mapping.json"

        result = runner.invoke(
            app,
            ["anonymize", "-", "-o", str(output_file), "-m", str(mapping_file)],
            input="PESEL 44051401359",
        )

        assert result.exit_code == 0, result.output
        assert "[PESEL_001]" in output_file.read_text(encoding="utf-8")

    def test_deanonymize_reads_from_stdin(self, runner: CliRunner, tmp_path: Path) -> None:
        in_file = tmp_path / "in.txt"
        in_file.write_text("44051401359", encoding="utf-8")
        anon_file = tmp_path / "anon.txt"
        mapping_file = tmp_path / "mapping.json"
        runner.invoke(
            app,
            ["anonymize", str(in_file), "-o", str(anon_file), "-m", str(mapping_file)],
        )
        anon_text = anon_file.read_text(encoding="utf-8")

        result = runner.invoke(
            app,
            ["deanonymize", "-", "-m", str(mapping_file)],
            input=anon_text,
        )

        assert result.exit_code == 0, result.output
        assert "44051401359" in result.output

    def test_deanonymize_explicit_stdout_dash(self, runner: CliRunner, tmp_path: Path) -> None:
        in_file = tmp_path / "in.txt"
        in_file.write_text("44051401359", encoding="utf-8")
        anon_file = tmp_path / "anon.txt"
        mapping_file = tmp_path / "mapping.json"
        runner.invoke(
            app,
            ["anonymize", str(in_file), "-o", str(anon_file), "-m", str(mapping_file)],
        )

        result = runner.invoke(
            app,
            ["deanonymize", str(anon_file), "-m", str(mapping_file), "-o", "-"],
        )

        assert result.exit_code == 0, result.output
        assert "44051401359" in result.output

    def test_detect_reads_from_stdin(self, runner: CliRunner) -> None:
        result = runner.invoke(
            app,
            ["detect", "-"],
            input="PESEL 44051401359",
        )

        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data[0]["value"] == "44051401359"


class TestInputEncoding:
    """CLI read-side tolerates UTF-8 (±BOM) and UTF-16 (±endianness with BOM)."""

    def _run_detect(self, runner: CliRunner, path: Path) -> list[dict[str, object]]:
        result = runner.invoke(app, ["detect", str(path)])
        assert result.exit_code == 0, result.output
        return json.loads(result.output)  # type: ignore[no-any-return]

    def test_utf8_without_bom(self, runner: CliRunner, tmp_path: Path) -> None:
        path = tmp_path / "in.txt"
        path.write_bytes(b"PESEL 44051401359")
        assert self._run_detect(runner, path)[0]["value"] == "44051401359"

    def test_utf8_with_bom(self, runner: CliRunner, tmp_path: Path) -> None:
        path = tmp_path / "in.txt"
        path.write_bytes(b"\xef\xbb\xbfPESEL 44051401359")
        assert self._run_detect(runner, path)[0]["value"] == "44051401359"

    def test_utf16_le_with_bom(self, runner: CliRunner, tmp_path: Path) -> None:
        # Mimics what PowerShell 5.1's `echo ... > file.txt` produces.
        path = tmp_path / "in.txt"
        path.write_bytes("PESEL 44051401359".encode("utf-16"))  # 'utf-16' adds LE BOM
        assert self._run_detect(runner, path)[0]["value"] == "44051401359"

    def test_utf16_be_with_bom(self, runner: CliRunner, tmp_path: Path) -> None:
        path = tmp_path / "in.txt"
        path.write_bytes(b"\xfe\xff" + "PESEL 44051401359".encode("utf-16-be"))
        assert self._run_detect(runner, path)[0]["value"] == "44051401359"

    def test_preserves_polish_diacritics_roundtrip(self, runner: CliRunner, tmp_path: Path) -> None:
        original = "Żółć ma PESEL 44051401359."
        input_file = tmp_path / "in.txt"
        input_file.write_bytes(original.encode("utf-16"))  # UTF-16 LE with BOM
        output_file = tmp_path / "out.txt"
        mapping_file = tmp_path / "mapping.json"

        result = runner.invoke(
            app,
            [
                "anonymize",
                str(input_file),
                "-o",
                str(output_file),
                "-m",
                str(mapping_file),
            ],
        )
        assert result.exit_code == 0

        restored_file = tmp_path / "restored.txt"
        result = runner.invoke(
            app,
            [
                "deanonymize",
                str(output_file),
                "-m",
                str(mapping_file),
                "-o",
                str(restored_file),
            ],
        )
        assert result.exit_code == 0
        assert restored_file.read_text(encoding="utf-8") == original
