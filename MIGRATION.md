# Migrating from `llm-safe-pl` to `pii-toolkit`

`llm-safe-pl` is deprecated as of v0.2.1. Its successors live in the
[`pii-toolkit`](https://github.com/Tatarinho/pii-toolkit) family on PyPI:

- [`pii-veil`](https://pypi.org/project/pii-veil/) — reversible anonymization
  for LLM workflows (the `Shield` / `Anonymizer` half of the old library).
- [`pii-core`](https://pypi.org/project/pii-core/) — detectors and checksum
  validators, language-aware and zero-dependency (the `detectors.*` and
  `validators.*` half).
- [`pii-presidio`](https://pypi.org/project/pii-presidio/) — Microsoft
  Presidio plugin (new; was never part of `llm-safe-pl`).

This document is a one-stop migration map. The 0.2.0 public API maps cleanly
onto the new packages — most projects only need to change imports.

## Install

```bash
pip uninstall llm-safe-pl
pip install pii-veil
```

`pii-veil` depends on `pii-core`, so the detectors and checksums come along
automatically. Only install `pii-core` directly if you need detectors or
validators without the LLM-workflow surface.

## Top-level imports

The five public names that 0.2.0 exposed at the package root all have
direct equivalents in `pii-veil`:

| Before (`llm-safe-pl 0.2.x`) | After (`pii-veil 0.1.x`) |
|---|---|
| `from llm_safe_pl import Shield` | `from pii_veil import Shield` |
| `from llm_safe_pl import Match` | `from pii_veil import Match` |
| `from llm_safe_pl import Mapping` | `from pii_veil import Mapping` |
| `from llm_safe_pl import AnonymizeResult` | `from pii_veil import AnonymizeResult` |
| `from llm_safe_pl import PIIType` | `from pii_veil import PIIType` |

`Match` and `PIIType` are re-exported from `pii-core` (where they're
canonically defined). `from pii_core import Match, PIIType` works too.

## Detector classes

Detectors moved to `pii-core` and adopted a language-prefixed naming scheme
(`Pl*` for Polish, no prefix for cross-language). `Detector` and
`RegexDetector` keep their names.

| Before (`llm_safe_pl.detectors`) | After (`pii_core`) |
|---|---|
| `Detector` | `Detector` |
| `RegexDetector` | `RegexDetector` |
| `PeselDetector` | `PlPeselDetector` |
| `NipDetector` | `PlNipDetector` |
| `RegonDetector` | `PlRegonDetector` |
| `IdCardDetector` | `PlIdCardDetector` |
| `PassportDetector` | `PlPassportDetector` |
| `PhoneDetector` | `PlPhoneDetector` |
| `IbanDetector` | `PlIbanDetector` |
| `EmailDetector` | `EmailDetector` (cross-language) |
| `CreditCardDetector` | `CreditCardDetector` (cross-language) |

`pii_core.DEFAULT_DETECTORS` is the equivalent of the old default registry,
in the same priority order as 0.2.0.

`pii-core` also adds two opt-in Polish detectors that were never in
`llm-safe-pl`: `PlKrsDetector` (KRS court-register numbers) and
`PlPostalCodeDetector` (XX-XXX). They're excluded from `DEFAULT_DETECTORS`
because the raw patterns collide with ordinary text — pass them explicitly
if you want them.

## Checksum validators

Names are unchanged; only the import path moves.

| Before (`llm_safe_pl.validators`) | After (`pii_core`) |
|---|---|
| `is_valid_pesel` | `is_valid_pesel` |
| `is_valid_nip` | `is_valid_nip` |
| `is_valid_regon` | `is_valid_regon` |
| `is_valid_iban` | `is_valid_iban` |
| `is_valid_luhn` | `is_valid_luhn` |
| `IBAN_LENGTHS` (registry) | `IBAN_LENGTHS` |

```python
# Before
from llm_safe_pl.validators import is_valid_pesel

# After
from pii_core import is_valid_pesel
```

## Code samples

### Anonymize → call LLM → deanonymize

```python
# Before (llm-safe-pl 0.2.x)
from llm_safe_pl import Shield

shield = Shield(max_input_bytes=1_000_000)
result = shield.anonymize(text)
response = call_llm(result.text)
restored = shield.deanonymize(response)

# After (pii-veil 0.1.x)
from pii_veil import Shield

shield = Shield(max_input_bytes=1_000_000)
result = shield.anonymize(text)
response = call_llm(result.text)
restored = shield.deanonymize(response)
```

The `Shield` API is intentionally identical — `anonymize`, `deanonymize`,
`reset`, `max_input_bytes`, and the `AnonymizeResult` shape (`.text`,
`.mapping`, `.matches`) all carry over.

### Custom detector list

```python
# Before
from llm_safe_pl import Shield
from llm_safe_pl.detectors import PeselDetector, NipDetector

shield = Shield(detectors=[PeselDetector(), NipDetector()])

# After
from pii_veil import Shield
from pii_core import PlPeselDetector, PlNipDetector

shield = Shield(detectors=[PlPeselDetector(), PlNipDetector()])
```

### Persisting and reloading a Mapping

```python
# Before
from llm_safe_pl import Mapping
import json

with open("mapping.json", "w") as f:
    json.dump(result.mapping.to_dict(), f)

with open("mapping.json") as f:
    mapping = Mapping.from_dict(json.load(f))

# After — same shape, same methods, different import
from pii_veil import Mapping
import json

with open("mapping.json", "w") as f:
    json.dump(result.mapping.to_dict(), f)

with open("mapping.json") as f:
    mapping = Mapping.from_dict(json.load(f))
```

Mapping JSON written by `llm-safe-pl 0.2.x` loads as-is in `pii-veil 0.1.x`
via `Mapping.from_dict`. Round-trip persistence across the migration is
supported.

## CLI

The CLI entry point changed from `llm-safe` to `pii-veil`. Subcommands and
flags are the same.

| Before | After |
|---|---|
| `llm-safe detect FILE` | `pii-veil detect FILE` |
| `llm-safe anonymize FILE -o OUT -m MAP` | `pii-veil anonymize FILE -o OUT -m MAP` |
| `llm-safe deanonymize FILE -m MAP` | `pii-veil deanonymize FILE -m MAP` |
| `--force`, `--max-bytes`, `--format` | unchanged |

## Mapping JSON compatibility

Mapping files produced by `llm-safe-pl 0.2.x` load without modification in
`pii-veil 0.1.x`. There's no schema change — only the producing/consuming
package name moved.

## Reporting issues during migration

The `Tatarinho/llm-safe-pl` repository is archived; new issues are no longer
accepted there. File migration bugs and questions against
[`Tatarinho/pii-toolkit`](https://github.com/Tatarinho/pii-toolkit/issues)
instead.
