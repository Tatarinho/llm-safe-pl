# Detectors

Reference for every detector in `DEFAULT_DETECTORS`. Each row documents the regex shape, accepted format variants, and whether a checksum validator filters candidates before they become `Match` objects.

| PII type | Class | Regex shape | Validator | Format variants |
|----------|-------|-------------|-----------|------------------|
| PESEL | `PeselDetector` | `\b\d{11}\b` | `is_valid_pesel` (mod-10 weighted sum) | bare 11 digits only |
| NIP | `NipDetector` | `\b\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b` | `is_valid_nip` (mod-11; rejects check=10) | `5260001246`, `526-000-12-46`, `526 000 12 46`, mixed |
| REGON | `RegonDetector` | `\b\d{14}\b|\b\d{9}\b` | `is_valid_regon` (9- or 14-digit, mod-11 with 10→0 collapse) | bare only |
| ID card | `IdCardDetector` | `\b[A-Z]{3}\d{6}\b` | none (regex-only in v0.1) | uppercase letters + digits |
| Passport | `PassportDetector` | `\b[A-Z]{2}\d{7}\b` | none (regex-only in v0.1) | uppercase letters + digits |
| Phone | `PhoneDetector` | 9 digits with optional `+48` prefix and optional `-` / space separators | none | `600123456`, `600 123 456`, `600-123-456`, `+48600123456`, `+48 600 123 456`, `+48-600-123-456` |
| Email | `EmailDetector` | practical RFC-5322 subset | none | standard email syntax |
| IBAN | `IbanDetector` | Polish prefix; bare 28 chars or `PL` + 2 digits + six groups of 4 digits separated by spaces | `is_valid_iban` (mod-97; SWIFT country length registry for ~80 countries) | `PL61109010140000071219812874`, `PL61 1090 1014 0000 0712 1981 2874` |
| Credit card | `CreditCardDetector` | bare 13-19 digits, `\d{4}-\d{4}-\d{4}-\d{1-7}`, or Amex 4-6-5 | `is_valid_luhn` | `4532015112830366`, `4532 0151 1283 0366`, `4532-0151-1283-0366`, `3782 822463 10005` |

NER-sourced types (PERSON, ORGANIZATION, LOCATION) are members of `PIIType` but their detector ships with the optional `[ner]` extra in v0.1.1. Without that extra, these enum values simply never appear in a `Match`.

## Detection pipeline

When you call `shield.anonymize(text)` or `shield.detect(text)`:

1. Every detector in `DEFAULT_DETECTORS` runs independently against the full text.
2. Raw matches are collected into one list.
3. Overlaps are resolved with a "longest wins, priority tiebreak" greedy pass:
   - Sort key: `(-length, start, detector_priority)` where priority is each detector's index in the list.
   - Iterate in sort order, take a match only if it doesn't overlap any already-taken match.
4. The kept matches are sorted by `start` and returned.
5. (Only for `anonymize`) Each kept match gets a token allocated via `Mapping.token_for(value, type)`, and the text is rewritten.

Examples of how overlap resolution plays out:

- **Same span, different detectors** — e.g. a 14-digit string that happens to pass both REGON and Luhn checksums. REGON wins because `RegonDetector` is earlier in `DEFAULT_DETECTORS` than `CreditCardDetector`.
- **Different spans, overlapping** — e.g. `ABC` and `ABCDEF` both matching. The longer match wins.
- **Adjacent but not overlapping** — both kept; the anonymizer rewrites them independently.

## Formatting preservation

`Match.value` always contains the exact substring from the source text. When the anonymizer rewrites, it looks up that exact value in the Mapping. When you deanonymize, you get the exact value back — including dashes, spaces, or whatever formatting was in the original.

For checksum-bearing detectors, the validator is called on a digits-only normalization of the match (e.g. `526-000-12-46` becomes `5260001246` before `is_valid_nip`). This lets formatted identifiers be checksum-validated without losing the source formatting.

## Customizing detector lists

Pass your own list to `Shield` if you want to disable some detectors or add custom ones:

```python
from llm_safe_pl.detectors import PeselDetector, EmailDetector
from llm_safe_pl import Shield

shield = Shield(detectors=[PeselDetector(), EmailDetector()])
# Now only PESEL and email are detected.
```

To write a custom detector, subclass `RegexDetector`:

```python
import re
from typing import ClassVar
from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType

class MyIdDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.ID_CARD
    name: ClassVar[str] = "my_id"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\bMYID-\d{6}\b")

    def _is_valid(self, candidate: str) -> bool:
        return True  # or invoke your own checksum
```

Note: this uses internals (`llm_safe_pl.detectors.base.RegexDetector`) that are not part of the locked `__all__` and may change in a minor release. For v0.1 they're stable; we'll re-promise in v1.0.
