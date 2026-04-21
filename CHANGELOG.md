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

### Changed

- Coverage configuration now omits `src/llm_safe_pl/__main__.py` (3-line runpy shim, not worth subprocess-based testing).
