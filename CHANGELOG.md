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

### Changed

- Coverage configuration now omits `src/llm_safe_pl/__main__.py` (3-line runpy shim, not worth subprocess-based testing).
