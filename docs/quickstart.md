# Quickstart

Five-minute tour from zero to a working anonymize → deanonymize round-trip.

## Install

```bash
pip install llm-safe-pl
```

Core install is ~2 MB and depends on stdlib + `typer`. Python 3.10 or newer.

## The core idea

`llm-safe-pl` is built around one workflow:

```
your document  ─▶  shield.anonymize()  ─▶  safe prompt
                                                │
                                                ▼
                                         call any LLM
                                                │
                                                ▼
your document  ◀─  shield.deanonymize()  ◀─  LLM response
```

Between the two Shield calls, no raw PII leaves your process.

## Python API

```python
from llm_safe_pl import Shield

shield = Shield()

# 1. Anonymize.
result = shield.anonymize(
    "Anna Nowak ma PESEL 44051401359 i email anna@example.pl."
)

print(result.text)
# Anna Nowak ma PESEL [PESEL_001] i email [EMAIL_001].

# 2. Send result.text to any LLM — pseudocode.
# response = openai.chat.completions.create(messages=[...])
# llm_output = response.choices[0].message.content

# 3. Deanonymize the response.
llm_output = "User [PESEL_001] can be contacted at [EMAIL_001]."
restored = shield.deanonymize(llm_output)

print(restored)
# User 44051401359 can be contacted at anna@example.pl.
```

A few things to notice:

- The `Shield` holds a shared `Mapping` across every `anonymize()` call. The same value gets the same token even if it appears in multiple documents processed by the same Shield.
- `shield.deanonymize(text)` with no mapping argument uses the Shield's own mapping. Pass an explicit `Mapping` to deanonymize against a saved state.
- Detected PII formats are preserved: `526-000-12-46` stays dashed, `4532 0151 1283 0366` stays spaced. The round-trip reproduces the source byte-for-byte.

## CLI

Everything the Python API does is also available from a shell:

```bash
# Scan for PII.
llm-safe detect document.txt

# Anonymize; writes two files.
llm-safe anonymize document.txt -o anon.txt -m mapping.json

# Restore originals.
llm-safe deanonymize anon.txt -m mapping.json -o restored.txt
```

See [`cli_usage.md`](../examples/cli_usage.md) for more.

## Saving and loading mappings

`Mapping` is JSON-serializable, so you can persist it between runs:

```python
# Save
with open("mapping.json", "w", encoding="utf-8") as f:
    f.write(result.mapping.to_json())

# Load
from llm_safe_pl import Mapping, Shield

with open("mapping.json", encoding="utf-8") as f:
    loaded = Mapping.from_json(f.read())

shield = Shield(mapping=loaded)
# Any anonymize() call will reuse tokens already allocated in `loaded`.
```

## What Shield detects

- PESEL, NIP, REGON (Polish government IDs, all checksum-validated)
- Polish ID card (dowód osobisty), passport (regex-only for v0.1)
- Phone, email, PL IBAN, credit card (Luhn-validated, 13-19 digits)

Person, organization, and location names require the optional `[ner]` extra — planned for v0.1.1.

## Next steps

- [`detectors.md`](detectors.md) — per-PII-type regex and validator details.
- [`llm_workflow.md`](llm_workflow.md) — the round-trip in depth, including LLM prompt templates that avoid token mangling.
- [`limitations.md`](limitations.md) — **required reading** before shipping to production.
- [`../examples/`](../examples/) — runnable scripts for OpenAI and Anthropic integrations.
