# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffolding: `pyproject.toml` (hatchling), GitHub Actions CI, ruff, mypy (strict), pytest with coverage gate.
- Public API surface locked to `Shield`, `Match`, `Mapping`, `AnonymizeResult`, `PIIType` (stubs; implementations land in subsequent phases).
- Optional-dependency groups declared: `[ner]` (spaCy), `[fake]` (Faker), `[pdf]` (pdfplumber), `[all]`, `[dev]`.
- CLI anchor callback on the root Typer app so `llm-safe --help` is valid before any subcommands exist.
- CLI smoke tests covering `--help` and the no-args help path.
- Python 3.14 added to the supported classifier list and CI matrix.
- User-facing `README.md` covering the target API, installation, development workflow, roadmap, and non-goals.
- `CONTRIBUTING.md` describing the pre-1.0 contribution policy, dev setup, required CI gates, and commit style.
- `models.py`: concrete `PIIType` (12 members covering the 9 regex detectors plus PERSON/ORGANIZATION/LOCATION for NER), `Match` (frozen dataclass with `type`, `value`, `start`, `end`, `detector`), `Mapping` (bidirectional value↔token store with per-type counters, schema-versioned JSON serialization, and token format `[TYPE_NNN]`), `AnonymizeResult` (frozen container for text, mapping, matches).
- `tests/test_models.py`: unit tests covering enum membership, Match immutability and hashability, Mapping counter allocation, cross-type independence, Unicode-safe JSON round-trip, schema-version rejection, and AnonymizeResult shape.
- `validators/` package with strict checksum validators: `is_valid_pesel`, `is_valid_nip`, `is_valid_regon` (9- and 14-digit), `is_valid_luhn` (13-19 digit card numbers), `is_valid_iban` (generic mod-97 with SWIFT country-length registry covering ~80 countries).
- `tests/test_validators/` with parametrized fixtures, property tests via `hypothesis` (generator-produces-valid, single-digit-mutation-breaks-validity), and coverage of all reject paths (wrong length, non-digit, lowercase, unknown country, invalid check digits, whitespace).
- `detectors/` package with `Detector` abstract base + `RegexDetector` concrete base and nine regex-based detectors (`PeselDetector`, `NipDetector`, `RegonDetector`, `IdCardDetector`, `PassportDetector`, `PhoneDetector`, `EmailDetector`, `IbanDetector`, `CreditCardDetector`). Checksum-bearing detectors (PESEL, NIP, REGON, IBAN, credit card) call into the Phase 2 validators after stripping formatting; ID card and passport are regex-only in v0.1. `DEFAULT_DETECTORS` is the ordered registry the anonymizer will consume in Phase 4.
- `tests/test_detectors/` with one file per detector plus base and registry tests, covering bare and formatted matches, span correctness, checksum rejection paths, embedded-digit-run rejection, multi-match behavior, and empty/no-match inputs.
- `anonymizer.py`: `Anonymizer` class that runs detectors, resolves overlapping matches with a "longest wins, priority tiebreak" policy, and rewrites text by asking the shared `Mapping` for a token per detection; returns an `AnonymizeResult` with the rewritten text, the mapping reference, and the (sorted) matches tuple.
- `deanonymizer.py`: `Deanonymizer` class that substitutes `[TYPE_NNN]` tokens back with their original values via a single `re.sub` pass. Unknown tokens are left untouched so LLM-hallucinated tokens do not silently restore garbage or crash the round-trip.
- `strategies.py`: `Strategy` enum placeholder with only `TOKEN` in v0.1; the constructor shape is locked so `mask` and `fake` can be added later without an API change.
- `tests/test_anonymizer.py`, `tests/test_deanonymizer.py`, `tests/test_strategies.py`: cover basic replacement, consistent tokens across calls, overlap resolution (same-span priority, longer-wins, non-overlapping and adjacent), Unicode handling, formatting preservation, round-trip through Anonymizer + Deanonymizer, unknown-token passthrough, and shared-mapping semantics for LLM-style token reshuffling.
- `shield.py`: real `Shield` class that bundles a shared `Mapping`, a detector list (defaulting to `DEFAULT_DETECTORS`), an `Anonymizer`, and a `Deanonymizer`. Methods: `anonymize(text)`, `deanonymize(text, mapping=None)` (defaults to the Shield's own mapping), `detect(text)` (returns a sorted tuple of Matches without mutating the mapping), and a `mapping` property. Removes the Phase 0 placeholder.
- `cli.py`: three subcommands replace the bare help-only app — `llm-safe anonymize INPUT -o OUT -m MAPPING.json`, `llm-safe deanonymize INPUT -m MAPPING.json [-o OUT]` (stdout fallback), `llm-safe detect INPUT [-f json|text]`. All I/O is UTF-8 file-based; removes the Phase 0 anchor callback since real commands now register.
- `anonymizer.py`: extracted detection + overlap resolution into a public-ish `detect(text)` method so `Shield.detect` can reuse it without allocating tokens. `anonymize(text)` now delegates to `detect`.
- `tests/test_shield.py` and `tests/test_cli_commands.py`: 23 new tests covering Shield construction variants, shared-mapping semantics, detect-without-allocation, round-trip, CLI exit codes, JSON/text detect formats, stdout fallback on deanonymize, and required-flag enforcement on anonymize.
- CLI input-side encoding tolerance: `_read_text` helper accepts UTF-8 with or without BOM and UTF-16 LE/BE when a BOM is present, so files produced by PowerShell 5.1's default `>` redirection (UTF-16 LE + BOM) work without manual conversion. Output remains canonical UTF-8 without BOM. Files without a BOM that are not UTF-8 still fail loudly — no silent encoding guesses.
- Additional CLI tests covering UTF-8, UTF-8 BOM, UTF-16 LE BOM, UTF-16 BE BOM, and a Polish-diacritics round-trip from a PowerShell-style UTF-16 file.

### Changed

- Coverage configuration now omits `src/llm_safe_pl/__main__.py` (3-line runpy shim, not worth subprocess-based testing).
