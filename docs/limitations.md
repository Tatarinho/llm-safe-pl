# Limitations

Read this before relying on `llm-safe-pl` in production. It is a technical tool, not a legal compliance product, and there are classes of PII it will not catch.

## What v0.1 does not detect

### Person names, organizations, locations (v0.1 core)

Without the `[ner]` extra, names like `Anna Nowak`, `PKN Orlen S.A.`, `Kraków` pass through unchanged. The optional spaCy-based recognizer (planned for v0.1.1) handles these; until then your LLM prompt will contain them.

Workaround for v0.1: detect names yourself before calling `Shield.anonymize`, or wait for v0.1.1.

### Landline phone numbers with area-code parentheses

`PhoneDetector` matches 9-digit mobile numbers with an optional `+48` country prefix and `-` / space separators. It does NOT match:

- `(22) 123-45-67` (2-digit area code in parens)
- `(012) 345 67 89` (leading-zero area code)
- International numbers that are not Polish

If your documents regularly contain landline numbers, plan to either add a custom detector or post-process.

### Addresses (street, city, postal code)

No detector in v0.1 tries to match street addresses or postal codes. Polish postal codes follow `\d{2}-\d{3}` but are often ambiguous with other 5-digit+dash strings. Consider adding a custom detector if addresses appear in your documents.

### Dates of birth

A date like `14 maja 1944` is not detected. The birth date encoded inside a PESEL is not separately extracted.

### Bank account numbers outside IBAN format

`IbanDetector` is strict: 28 chars, starts with a recognized 2-letter country code, passes mod-97. Legacy non-IBAN Polish account numbers (26 raw digits, no country prefix) are not detected.

### Document numbers for other jurisdictions

Polish ID card (`[A-Z]{3}\d{6}`) and passport (`[A-Z]{2}\d{7}`) shapes are the only structured identifiers in this family. EU ID cards, US SSNs, UK NI numbers — none are recognized.

## False positives and false negatives

### Credit card false positives

`CreditCardDetector` accepts any 13-19 digit run that passes Luhn. Random long digit strings pass Luhn with roughly 1-in-10 probability. If your documents contain shipping numbers, order IDs, or other long digit runs, expect occasional misclassification.

Mitigations:

- Use a custom credit card regex restricted to known card-number prefixes (e.g. `^4` for Visa, `^5[1-5]` for MC) if your scope is narrower.
- Run `Shield.detect(text)` and audit matches before committing to automated anonymization.

### ID card / passport false positives

Both are regex-only in v0.1. Any `[A-Z]{3}\d{6}` string (e.g. `ABC123456` as an SKU, part number, or invoice code) is classified as an ID card match. Passport similarly.

Mitigations:

- The real Polish ID card and passport checksums are documented but not yet implemented. Adding them (via `docs/detectors.md` custom detectors) reduces FPs significantly.
- Consider disabling these two detectors if your documents contain many SKU-like codes:

```python
from llm_safe_pl import Shield
from llm_safe_pl.detectors import DEFAULT_DETECTORS
from llm_safe_pl.detectors.id_card import IdCardDetector
from llm_safe_pl.detectors.passport import PassportDetector

safe_set = [d for d in DEFAULT_DETECTORS
            if not isinstance(d, (IdCardDetector, PassportDetector))]
shield = Shield(detectors=safe_set)
```

### Phone detector and 9-digit codes

Any 9-digit run bounded by non-digits can match `PhoneDetector`. Order numbers, internal references, and customer IDs of that length will be tokenized. Phone numbers do not have a checksum to filter by.

## Input format limitations

### Plain text only

v0.1 reads and writes plain text. PDF, DOCX, HTML, Markdown, RTF — none are parsed. Feed pre-extracted text. PDF support is planned for v0.3 via the `[pdf]` extra.

### Encoding

The CLI accepts UTF-8 (with or without BOM) and UTF-16 (with BOM). BOM-less non-UTF-8 files (e.g. Windows-1250 Polish text without a BOM) are rejected with a decode error — the library refuses to guess.

### Whitespace and paragraph boundaries

Detectors are whitespace-sensitive for the phone, IBAN, and credit card formats. A PESEL split across a line break (`44051401\n359`) is not detected.

## Threat model

`llm-safe-pl` protects against one specific scenario: **a Polish-language document leaves your process and reaches a third party (typically an LLM vendor) along with the identifiers it contains.** The library rewrites structured identifiers into tokens before egress and restores them locally after the response returns.

### What it defends against

- A passive LLM vendor (or anyone reading prompt/response logs) learning the raw value of a PESEL, NIP, REGON, IBAN, card number, ID card, passport, phone, or email from the prompt text.
- The same leak via a log aggregator, a debug dump, or an accidental commit of a document you processed — if you ran `Shield.anonymize` first, the dumped text contains tokens, not originals.

### What it does NOT defend against

- **An attacker who has both the anonymized text and the `Mapping` file.** The Mapping is a lookup table from tokens back to PII. Treat it with the same sensitivity as the original data — don't commit it, don't send it to the vendor, don't log it.
- **Inference from residual context.** Dates, employment history, relationships, medical descriptions, rare diagnoses, or any cluster of small facts can re-identify an individual even with every PESEL and NIP tokenized. Redaction is one layer; linkability analysis is another.
- **PII types the library does not detect.** Names, organizations, and locations without the `[ner]` extra; street addresses, landline phones with parens, dates of birth, legacy bank account formats, non-Polish identifiers. See the rest of this document for the full list.
- **Active adversaries inside your process.** If a compromised dependency or malicious import runs before `Shield.anonymize`, the raw document is already in memory.
- **Side channels outside the prompt body.** Request metadata, IP address, timing, response-size-based inference, retained billing records.

### Assumptions

- The Mapping never leaves the process boundary that owns the original PII.
- The caller has validated that the document classes they run through `Shield` fall inside the scope of the nine built-in detectors (plus NER if `[ner]` is installed).
- The LLM vendor is a passive adversary — it may log, cache, or train on prompts, but is not specifically targeting your workflow.

If any of those assumptions is wrong for your deployment, the library alone does not close the gap.

## Concurrency and thread safety

Neither `Mapping` nor `Shield` is thread-safe. `Mapping.token_for` mutates a shared counter and two dicts without synchronization, so concurrent `anonymize()` calls on the same `Shield` can corrupt state, drop tokens, or produce duplicate tokens for distinct values.

If you need to run anonymization from multiple threads:

- Use one `Shield` per thread (each with its own `Mapping`). This is the simplest correct option.
- Or serialize access to a shared `Shield` with an external lock (e.g. `threading.Lock`).

Across processes, persist and reload per-worker `Mapping`s via `Mapping.to_json` / `Mapping.from_json` when you need consistent tokens for the same input.

## Legal and compliance limitations

`llm-safe-pl` is a **technical tool for redacting specific patterns of data before it leaves your process**. It is not:

- A GDPR compliance product.
- A certification or guarantee that the output is anonymous in a legal sense.
- A replacement for an organization's privacy and security review.

The library's detection is imperfect (see above). Using it does not transfer responsibility from you to the library author. You remain the data controller.

Specific concerns worth flagging to your legal/compliance team:

1. **Residual identifiability.** Unredacted context (dates, addresses, employment history) can still identify an individual. PII redaction is one layer; linkability analysis is another.
2. **LLM provider data retention.** Even with redacted prompts, the vendor may log your queries. Check their retention policy and DPA.
3. **Mapping file as a secret.** The Mapping is effectively a lookup table from tokens back to PII. Protect it with the same rigor as the original data.

## What happens when detection fails silently

If a PII item in your text is not matched by any detector:

- It will NOT be anonymized.
- It WILL be sent to the LLM as-is.
- It WILL appear in the final output.

Always run `Shield.detect(text)` (or `llm-safe detect file.txt`) on representative sample data before trusting automated processing. If something in the sample is missing from the detection list, it will also be missing in production.

## Reporting issues

If you find a class of Polish PII that we should detect but don't, open an issue with:

- Anonymized example(s) — synthetic test data, not real PII.
- The format / regex shape.
- Whether it has a checksum we could validate.

See [`CONTRIBUTING.md`](../CONTRIBUTING.md).
