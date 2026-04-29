# llm-safe-pl

> ## ⚠️ DEPRECATED — use `pii-toolkit` instead
>
> **`llm-safe-pl` is end-of-life as of v0.2.1 (2026-04-29).** No further
> features, fixes, or security updates will be released. The library has been
> superseded by the [`pii-toolkit`](https://github.com/Tatarinho/pii-toolkit)
> family on PyPI:
>
> | Was | Now |
> |---|---|
> | `llm_safe_pl.Shield`, `Anonymizer`, `Deanonymizer` | [`pii-veil`](https://pypi.org/project/pii-veil/) |
> | `llm_safe_pl.detectors.*` | [`pii-core`](https://pypi.org/project/pii-core/) |
> | `llm_safe_pl.validators.*` (checksums) | [`pii-core`](https://pypi.org/project/pii-core/) |
> | Microsoft Presidio integration | [`pii-presidio`](https://pypi.org/project/pii-presidio/) |
>
> See [`MIGRATION.md`](MIGRATION.md) for a full symbol-by-symbol map and
> before/after code samples.
>
> v0.2.1 is a **deprecation tombstone**: the public API still works exactly as
> it did in 0.2.0, but `import llm_safe_pl` now emits a `DeprecationWarning`.
> Existing pinned installs keep functioning; you just won't get any new
> releases. Migrate at your own pace.

[![PyPI version](https://img.shields.io/pypi/v/llm-safe-pl.svg)](https://pypi.org/project/llm-safe-pl/)
[![Python versions](https://img.shields.io/pypi/pyversions/llm-safe-pl.svg)](https://pypi.org/project/llm-safe-pl/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Why `pii-toolkit` replaces this

`llm-safe-pl` started as a Polish-only reversible-anonymization library.
Building it surfaced a cleaner three-package architecture:

- **`pii-core`** — language-agnostic detectors and checksum validators with
  zero runtime dependencies. Polish detectors (PESEL, NIP, REGON, Polish IBAN,
  ID card, passport) ship out of the box alongside multi-language ones.
- **`pii-veil`** — the reversible `Shield`-style facade for LLM workflows,
  layered on top of `pii-core`. Same round-trip contract (`anonymize` →
  call LLM → `deanonymize`) you had in `llm-safe-pl`.
- **`pii-presidio`** — optional Microsoft Presidio plugin for projects that
  already standardize on Presidio's recognizer ecosystem.

The split lets each piece evolve independently: detectors without dragging in
the LLM-workflow surface, the LLM workflow without locking in any one
detection backend, and Presidio integration without infecting the dependency
tree of users who don't use it.

## Migrating

The fastest path:

```bash
pip uninstall llm-safe-pl
pip install pii-veil
```

Then update imports:

```python
# Before (llm-safe-pl 0.2.x)
from llm_safe_pl import Shield

# After (pii-veil)
from pii_veil import Shield
```

Polish detectors are part of `pii-core`'s default registry and are auto-loaded
by `pii-veil` — no extra setup needed for the common case. For the full map
including `Match`, `Mapping`, `AnonymizeResult`, `PIIType`, individual
detector classes, and checksum validators, see [`MIGRATION.md`](MIGRATION.md).

The CLI is replaced by `pii-veil`'s CLI; same subcommands (`detect`,
`anonymize`, `deanonymize`).

## Reporting issues

Issues against `llm-safe-pl` are no longer accepted. If you hit a bug while
migrating, please open it against the relevant successor package:

- [`pii-toolkit/issues`](https://github.com/Tatarinho/pii-toolkit/issues)

---

# Legacy documentation (v0.2.0)

The original v0.2.0 documentation is preserved below for users still on
pinned installs. Nothing in this section will receive further updates.

## What this library does

Reversible PII anonymization for Polish documents, designed for LLM workflows.

When you send a Polish document to an LLM (OpenAI, Anthropic, a local model),
you're exposing PESEL numbers, NIPs, ID card numbers, addresses, and names to
a third party. `llm-safe-pl` is built around the full round-trip:

1. **Anonymize** — detect Polish PII, replace with stable tokens, return a
   reversible mapping.
2. **Call the LLM** — the request contains no raw PII.
3. **Deanonymize** — restore original values in the response using the saved
   mapping.

Checksum validation (PESEL, NIP, REGON, Luhn, IBAN mod-97) is first-class, so
valid-looking-but-wrong numbers are rejected before they become false
positives.

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

## Quick example — CLI

```bash
# Detect PII without modifying the file
llm-safe detect document.txt

# Anonymize: writes rewritten text and a reversible mapping
llm-safe anonymize document.txt -o anon.txt -m mapping.json --force

# Restore original values
llm-safe deanonymize anon.txt -m mapping.json
```

## What's supported (v0.2.0)

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

## License

MIT. See [LICENSE](LICENSE).
