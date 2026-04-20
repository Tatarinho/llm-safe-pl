# llm-safe-pl

Reversible PII anonymization for Polish documents, designed for LLM workflows.

> **Status: pre-alpha (v0.1.0.dev0).** The public API surface is locked; implementations are being added incrementally. The package installs and imports cleanly, but the detectors, validators, and anonymizer are not yet wired up. See [Roadmap](#roadmap) and [CHANGELOG.md](CHANGELOG.md).

---

## Why this exists

When you send a Polish document to an LLM (OpenAI, Anthropic, a local model), you're exposing PESEL numbers, NIPs, ID card numbers, addresses, and names to a third party. Existing PII tools either focus on English data, flag every 11-digit string as a PESEL (false positives), or provide one-way redaction that breaks when you need to post-process the LLM's response.

`llm-safe-pl` is built around the full round-trip:

1. **Anonymize** — detect Polish PII, replace with stable tokens, return a reversible mapping.
2. **Call the LLM** — the request contains no raw PII.
3. **Deanonymize** — restore original values in the response using the saved mapping.

Checksum validation (PESEL, NIP, REGON, Luhn, IBAN mod-97) is first-class, so valid-looking-but-wrong numbers are rejected before they become false positives.

## Installation

Core install — stdlib + `typer` only, ~2 MB:

```bash
pip install llm-safe-pl
```

With the optional spaCy NER recognizer for persons / organizations / locations:

```bash
pip install "llm-safe-pl[ner]"
python -m spacy download pl_core_news_lg
```

Everything at once:

```bash
pip install "llm-safe-pl[all]"
```

Requires Python 3.10+.

## Target API (locked, not yet functional)

The public surface — `Shield`, `Match`, `Mapping`, `AnonymizeResult`, `PIIType` — is frozen as of v0.1.0.dev0. Anything not in `__all__` is an implementation detail and may change without a major version bump.

```python
from llm_safe_pl import Shield

shield = Shield()
result = shield.anonymize(
    "Jan Kowalski, PESEL 44051401359, tel. +48 600 123 456"
)
# result.text    -> "[PERSON_001], PESEL [PESEL_001], tel. [PHONE_001]"
# result.mapping -> reversible mapping (serializable to JSON)
# result.matches -> list[Match] for audit

# Send result.text to OpenAI, Anthropic, a local model — anywhere.
llm_response = "... response containing [PERSON_001] ..."

final = shield.deanonymize(llm_response, result.mapping)
```

The same value always maps to the same token within a `Shield` instance, so `Jan Kowalski` referenced twice in a document gets the same `[PERSON_001]` both times.

## CLI (planned)

```bash
llm-safe anonymize document.txt --output anon.txt --mapping mapping.json
llm-safe deanonymize anon.txt --mapping mapping.json
llm-safe detect document.txt --format json
```

Subcommands land in Phase 5. Today only `llm-safe --help` works.

## Key design choices

- **Zero external dependencies in the core.** Detection, anonymization, and mapping run on stdlib alone. Heavy features (spaCy, Faker, pdfplumber) are opt-in extras.
- **Checksums written from scratch.** PESEL, NIP, REGON, Luhn, mod-97 IBAN — the library's core value, not outsourced.
- **Reversibility is a contract.** Every `anonymize()` call returns a `Mapping` that enables perfect restoration.
- **Polish-first.** Native handling of Polish identifiers and, via the `[ner]` extra, Polish names and addresses through `pl_core_news_lg`.

## Scope of v0.1

**In:** 9 regex-based detectors with checksum validation (PESEL, NIP, REGON, ID card, passport, Polish phone, email, PL IBAN, credit card); `Anonymizer` / `Deanonymizer` / `Shield` classes; `Mapping` with JSON serialization; optional spaCy NER; CLI via Typer; >80% test coverage.

**Deferred to v0.2+:** Faker-based fake substitution, PDF/DOCX parsing, LLM-as-detector fallback, REST API, Docker image, non-Polish languages.

## Development

```bash
git clone https://github.com/<your-user>/llm-safe-pl.git
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

The 80% coverage gate is enforced in `pyproject.toml` and fails the build if it drops.

## Roadmap

- **Phase 0** — Scaffolding: packaging, CI, locked public API surface, tests green. **Done.**
- **Phase 1** — `models.py`: real `Match`, `Mapping`, `AnonymizeResult`, full `PIIType` enum. **Next.**
- **Phase 2** — Checksum validators: PESEL, NIP, REGON, Luhn, mod-97 IBAN.
- **Phase 3** — Nine regex + checksum detectors.
- **Phase 4** — `Anonymizer` / `Deanonymizer` with consistent tokens.
- **Phase 5** — `Shield` facade + CLI subcommands.
- **Phase 6** — Optional spaCy NER recognizer.
- **Release** — v0.1.0 to PyPI.

## Non-goals

- Not a SaaS, browser extension, or GUI — this is a Python library.
- Not a legal compliance product. The library is a technical tool; compliance is the user's responsibility.
- Not optimized for non-Polish text.
- Not reimplementing PDF parsing, HTTP servers, or GUI frameworks that belong in separate libraries.

## License

MIT. See [LICENSE](LICENSE).
