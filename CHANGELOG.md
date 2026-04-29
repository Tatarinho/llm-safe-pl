# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> No further releases planned. `llm-safe-pl` is end-of-life as of v0.2.1.
> Code merged to `main` after v0.2.1 (typed exception hierarchy in
> `llm_safe_pl.errors`, regression-corpus scaffolding under `tests/corpora/`,
> typed errors raised from `Mapping.from_dict` / `Shield.anonymize`) is
> preserved in the source tree but will not ship to PyPI. Equivalent
> functionality lives in [`pii-veil`](https://pypi.org/project/pii-veil/) and
> [`pii-core`](https://pypi.org/project/pii-core/).

## [0.2.1] - 2026-04-29

Final release. `llm-safe-pl` is deprecated and will receive no further updates.

The work continues in the [`pii-toolkit`](https://github.com/Tatarinho/pii-toolkit)
family on PyPI:

- [`pii-veil`](https://pypi.org/project/pii-veil/) — reversible anonymization
  for LLM workflows (successor to `Shield` / `Anonymizer`).
- [`pii-core`](https://pypi.org/project/pii-core/) — multi-language detection
  and checksum validation (successor to `llm_safe_pl.detectors` and
  `llm_safe_pl.validators`).
- [`pii-presidio`](https://pypi.org/project/pii-presidio/) — Microsoft Presidio
  plugin with multi-language recognizers.

See [`MIGRATION.md`](MIGRATION.md) for the symbol-by-symbol migration map.

### Changed

- `import llm_safe_pl` now emits a `DeprecationWarning` pointing to the
  successor packages and the migration guide. The 0.2.0 API surface is
  unchanged — existing pinned installs keep working without code changes.
- `Development Status` classifier moved from `3 - Alpha` to `7 - Inactive`.
- Package description and README rewritten with a deprecation banner and
  migration links.

### Added

- `MIGRATION.md` — symbol-by-symbol map from `llm_safe_pl.*` to the
  `pii-toolkit` packages.
- `tests/test_deprecation.py` — asserts the import-time
  `DeprecationWarning` fires.

## [0.2.0] - 2026-04-26

Service-pack release: a large algorithmic-perf fix and a security/hardening
sweep on the public API. Same library, same nine detectors, same checksums —
just much faster on large documents and stricter about untrusted inputs.

### Added

- `Shield.reset()`: discard the accumulated Mapping (counters and entries) without rebuilding the Shield. Use between unrelated documents or users to prevent cross-document token leakage on `deanonymize`. Detector list and `max_input_bytes` are preserved.
- `Shield(max_input_bytes=...)` constructor option: refuses inputs whose UTF-8 byte length exceeds the cap. Default unbounded; recommended for pipelines that ingest untrusted text since `Shield.anonymize` allocates O(n) memory in input size.
- CLI `--force` flag on `anonymize` and `deanonymize`: required to overwrite an existing output or mapping file. Without it the command refuses with a clear error instead of silently clobbering.
- CLI `--max-bytes` flag on every subcommand (default 64 MiB): refuses pathologically large stdin or file inputs without crashing the process.
- `Shield` docstring documents thread-safety and the cross-document leakage class.
- `tests/test_security_hardening.py`: 24 new tests covering `Mapping.from_dict` validation paths, `Anonymizer` constructor enforcement, `Shield` input-size guard and reset behavior, and `Detector.__init_subclass__` enforcement.
- `tests/test_overlap_property.py`: Hypothesis-driven property test asserting the new bisect-based overlap resolution is set-equivalent to the previous quadratic algorithm over arbitrary match sets.

### Changed

- `Anonymizer._resolve_overlaps` now uses a `bisect_left`-based neighbor check instead of a linear `any(...)` scan over `taken`. Worst-case complexity drops from O(n²) to O(n log n) for the lookup; per-call insertion remains O(n) due to list shifts. On a 100 KiB synthetic document with ~4900 candidate matches the median `Shield.anonymize()` latency drops from ~1700 ms to ~70 ms (≈25× faster); 1 MiB inputs that previously timed the harness out now complete in ~1.5 s. Output is byte-identical to the previous algorithm.
- `Mapping.from_dict` now validates every field at runtime: token shape (`[TYPE_NNN]`), token-prefix vs declared type, counter coverage of issued tokens, and the scalar types of values and counters. **Breaking** for callers that previously fed malformed JSON and relied on lenient acceptance — those calls now raise `ValueError`.
- `Anonymizer.__init__` now rejects:
  - Detector lists with duplicate `name` attributes (previously silently overwrote the priority dict and broke overlap-resolution determinism).
  - `Strategy` values other than `Strategy.TOKEN` (the only implemented strategy in v0.1; passing anything else previously was a silent no-op). The strategy is also stored on the instance now, ready for future `MASK` / `FAKE` dispatch.
- `Detector` base class now enforces `pii_type` and `name` presence at class-definition time via `__init_subclass__`. Subclasses missing either previously instantiated successfully and crashed on first `detect()` call.
- CLI `anonymize` / `deanonymize` now refuse to overwrite an existing output or mapping file unless `--force` is passed. **Breaking** for scripts that relied on auto-overwrite — add `--force` to preserve previous behavior.
- CLI `detect --format` is now case-insensitive (`JSON`, `Json`, `json` all accepted); previously only lowercase worked.
- `Mapping` now uses `__slots__` and `Mapping.token_for` uses an f-string instead of `str.format`. Internal performance polish; no API change.
- `Anonymizer` now caches the priority dict in `__init__` instead of rebuilding it on every `_resolve_overlaps` call. Internal; no API change.
- `__version__` (in `__init__.py`) now falls back to a `"0.0.0+local"` sentinel when `importlib.metadata.version("llm-safe-pl")` raises `PackageNotFoundError`. This keeps `import llm_safe_pl` working when the source tree is loaded via `PYTHONPATH` without an editable install — useful for development workflows and CI checkout-only steps.
- `examples/cli_usage.md` updated for the new `--force` and `--max-bytes` flags.
- `docs/quickstart.md`, `docs/limitations.md`, and `README.md` updated to mention the new `Shield.reset` and `max_input_bytes` capabilities and to call out the breaking CLI behavior.

### Fixed

- Removed silent failure modes when a custom detector subclass omitted required class variables (now raised at class-definition time, see `Detector.__init_subclass__` change above).

### Migration notes for 0.1.x → 0.2.0

The two changes that may surprise existing users:

1. **CLI overwrite now requires `--force`.** A cron job that runs
   `llm-safe anonymize doc.txt -o out.txt -m map.json` daily will now fail on
   the second run because `out.txt` already exists. Add `-f` / `--force`:
   `llm-safe anonymize doc.txt -o out.txt -m map.json --force`.
2. **`Mapping.from_dict` now raises on malformed JSON** that previously
   loaded leniently. If you persist mappings from one process and load them
   in another, mappings produced by 0.1.0 still load cleanly in 0.2.0
   (round-trip is preserved); only hand-crafted or tampered JSON triggers
   the new errors.

If neither applies to you, 0.2.0 is a drop-in upgrade with a 25× speedup on
larger documents and the new `Shield.reset()` / `max_input_bytes` options
available when you want them.

## [0.1.0] - 2026-04-22

### Added

- User-facing `README.md` rewritten for the v0.1.0 release with working examples, supported-PII table, and an up-to-date roadmap.
- `examples/`: `basic.py`, `openai_integration.py`, `anthropic_integration.py`, and `cli_usage.md`.
- `docs/`: `quickstart.md`, `detectors.md`, `llm_workflow.md`, `limitations.md`.
- `benchmarks/throughput.py`: rough docs-per-second baseline for regression detection.
- `[project.urls]` in `pyproject.toml` (Homepage, Repository, Issues, Changelog) so the PyPI sidebar is populated on first publish.
- `llm-safe --version` / `-V` flag: prints the canonical `__version__` and exits.
- CLI stdin/stdout pipeline support — every subcommand accepts `-` as the input path (read from stdin); `deanonymize --output -` means explicit stdout. `--mapping` remains file-only. `examples/cli_usage.md` updated with a Stdin/stdout section.
- Round-trip property tests (`tests/test_roundtrip_property.py`) driven by Hypothesis — two strategies (arbitrary safe text; interleaved valid PII samples) verify `deanonymize(anonymize(x).text) == x`.
- `Concurrency and thread safety` section in `docs/limitations.md` plus a matching paragraph on the `Mapping` docstring documenting non-thread-safety and safe-usage patterns.

### Changed

- Version bumped from `0.1.0.dev0` to `0.1.0`.
- `__version__` now derives from installed package metadata (`importlib.metadata.version("llm-safe-pl")`) instead of a hardcoded literal, so `pyproject.toml` is the single source of truth.
- Dropped unused `self._strategy` storage in `Anonymizer`; the constructor keeps the `strategy` parameter for forward-compat with future MASK/FAKE variants (see `strategies.py`).
- Tightened the README "dependencies" bullet — `typer` is a required install-time dep (used by the CLI); the core modules remain stdlib-only.
- Fixed the `<your-user>` placeholder in the README clone URL to the actual GitHub org (`Tatarinho`).

## [0.1.0.dev0] - unreleased

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
