# llm-safe-pl

[![PyPI version](https://img.shields.io/pypi/v/llm-safe-pl.svg)](https://pypi.org/project/llm-safe-pl/)
[![Python versions](https://img.shields.io/pypi/pyversions/llm-safe-pl.svg)](https://pypi.org/project/llm-safe-pl/)
[![Tests](https://github.com/Tatarinho/llm-safe-pl/actions/workflows/tests.yml/badge.svg)](https://github.com/Tatarinho/llm-safe-pl/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Reversible PII anonymization for Polish documents, designed for LLM workflows.

> **Status: alpha (v0.1.0).** Core regex + checksum detection, anonymization, deanonymization, and the CLI are implemented and tested (280+ tests, ~99% coverage). The optional spaCy NER recognizer for PERSON / ORGANIZATION / LOCATION is scheduled for v0.1.1. See [CHANGELOG.md](CHANGELOG.md) and [Roadmap](#roadmap).

---

## Why this exists

When you send a Polish document to an LLM (OpenAI, Anthropic, a local model), you're exposing PESEL numbers, NIPs, ID card numbers, addresses, and names to a third party. Existing PII tools either focus on English data, flag every 11-digit string as a PESEL (false positives), or provide one-way redaction that breaks when you need to post-process the LLM's response.

`llm-safe-pl` is built around the full round-trip:

1. **Anonymize** — detect Polish PII, replace with stable tokens, return a reversible mapping.
2. **Call the LLM** — the request contains no raw PII.
3. **Deanonymize** — restore original values in the response using the saved mapping.

Checksum validation (PESEL, NIP, REGON, Luhn, IBAN mod-97) is first-class, so valid-looking-but-wrong numbers are rejected before they become false positives.

## Installation

Core install — stdlib + `typer` only:

```bash
pip install llm-safe-pl
```

Optional spaCy-based NER (Phase 6, not yet released):

```bash
pip install "llm-safe-pl[ner]"
python -m spacy download pl_core_news_lg
```

Requires Python 3.10+.

## Quick example — Python API

```python
from llm_safe_pl import Shield

shield = Shield()

result = shield.anonymize(
    "Jan Kowalski ma PESEL 44051401359, NIP 526-000-12-46, email jan@example.pl."
)
# result.text    -> "Jan Kowalski ma PESEL [PESEL_001], NIP [NIP_001], email [EMAIL_001]."
# result.mapping -> reversible Mapping object (JSON-serializable)
# result.matches -> tuple[Match, ...] for audit

# Safe to send to an LLM now.
# response = call_any_llm(result.text)

restored = shield.deanonymize(result.text)
# "Jan Kowalski ma PESEL 44051401359, NIP 526-000-12-46, email jan@example.pl."
```

The same value always maps to the same token within a `Shield` instance, including across multiple `anonymize()` calls. Formatted identifiers (e.g. `526-000-12-46`) round-trip exactly — the dashes are preserved.

PERSON detection (`Jan Kowalski` in the example) requires `pip install "llm-safe-pl[ner]"` and is part of Phase 6. Without the extra, names remain visible and structured identifiers (PESEL, NIP, IBAN, etc.) are tokenized.

## Quick example — CLI

```bash
# Detect PII without modifying the file (JSON or tab-separated output)
llm-safe detect document.txt
llm-safe detect document.txt --format text

# Anonymize: writes rewritten text and a reversible mapping
llm-safe anonymize document.txt -o anon.txt -m mapping.json

# Restore original values (prints to stdout, or use -o FILE)
llm-safe deanonymize anon.txt -m mapping.json
```

The CLI reads UTF-8 (with or without BOM) and UTF-16 (when a BOM is present), so files produced by PowerShell's default `>` redirection work without manual conversion. Output is always canonical UTF-8.

## What's supported

| PII type | Format examples | Checksum validated |
|----------|-----------------|-------------------|
| PESEL | `44051401359` | ✅ |
| NIP | `5260001246`, `526-000-12-46` | ✅ |
| REGON | `123456785` (9-digit), `12345678500001` (14-digit) | ✅ |
| ID card (dowód) | `ABC123456` | regex only |
| Passport | `AB1234567` | regex only |
| Phone | `+48 600 123 456`, `600-123-456` | — |
| Email | `user@example.pl` | — |
| IBAN | `PL61109010140000071219812874` (bare or 4-digit-grouped) | ✅ (mod-97, ~80 countries) |
| Credit card | `4532 0151 1283 0366` (13-19 digits, various groupings) | ✅ (Luhn) |
| Person / Organization / Location | via optional `[ner]` extra (Phase 6) | — |

## Public API

These are the only names exported from `llm_safe_pl`:

```python
from llm_safe_pl import Shield, Match, Mapping, AnonymizeResult, PIIType
```

Anything else is an implementation detail and may change without a major version bump.

## Key design choices

- **Minimal dependencies.** Detection, anonymization, and mapping run on stdlib alone; `typer` (used by the CLI) is the only required install-time dep. Heavy features (spaCy, Faker, pdfplumber) are opt-in extras.
- **Checksums written from scratch.** PESEL, NIP, REGON, Luhn, mod-97 IBAN — the library's core value, not outsourced.
- **Reversibility is a contract.** Every `anonymize()` call returns a `Mapping` that enables perfect restoration, preserving source formatting (dashes, spaces).
- **Polish-first.** Native handling of Polish identifiers and, via the `[ner]` extra, Polish names and addresses through `pl_core_news_lg`.

## More examples and documentation

- [`examples/basic.py`](examples/basic.py) — minimal programmatic use.
- [`examples/openai_integration.py`](examples/openai_integration.py) — full round-trip against OpenAI.
- [`examples/anthropic_integration.py`](examples/anthropic_integration.py) — same for the Anthropic API.
- [`docs/quickstart.md`](docs/quickstart.md) — 5-minute tour.
- [`docs/detectors.md`](docs/detectors.md) — detector behavior reference.
- [`docs/llm_workflow.md`](docs/llm_workflow.md) — the anonymize → LLM → deanonymize pattern in depth.
- [`docs/limitations.md`](docs/limitations.md) — **read before shipping to production.** What the library does not do, and what it may miss.

## Development

```bash
git clone https://github.com/Tatarinho/llm-safe-pl.git
cd llm-safe-pl
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -e ".[dev]"
```

CI runs these four gates — run them the same way locally:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

The 80% coverage gate is enforced in `pyproject.toml`.

## Roadmap

- **Phase 0** — Scaffolding: packaging, CI, locked public API surface, tests green. **Done.**
- **Phase 1** — `models.py`: `Match`, `Mapping`, `AnonymizeResult`, `PIIType`. **Done.**
- **Phase 2** — Checksum validators: PESEL, NIP, REGON, Luhn, mod-97 IBAN. **Done.**
- **Phase 3** — Nine regex + checksum detectors. **Done.**
- **Phase 4** — `Anonymizer` / `Deanonymizer` with consistent tokens. **Done.**
- **Phase 5** — `Shield` facade + CLI subcommands. **Done.**
- **Phase 6** — Optional spaCy NER recognizer. *Next — planned for v0.1.1.*
- **v0.2.0+** — Faker-based fake substitution, PDF/DOCX parsing, broader IBAN detector scope.

## Non-goals

- Not a SaaS, browser extension, or GUI — this is a Python library.
- Not a legal compliance product. The library is a technical tool; compliance is the user's responsibility. See [`docs/limitations.md`](docs/limitations.md).
- Not optimized for non-Polish text.
- Not reimplementing PDF parsing, HTTP servers, or GUI frameworks that belong in separate libraries.

## License

MIT. See [LICENSE](LICENSE).
