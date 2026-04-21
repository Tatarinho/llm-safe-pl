# LLM workflow

How to use `llm-safe-pl` with any LLM provider (OpenAI, Anthropic, local models, managed platforms) without leaking PII in prompts or losing information in responses.

## The round-trip

```
┌────────────────┐       ┌──────────────┐       ┌──────────────────┐
│ Original text  │  ──▶  │ anonymize()  │  ──▶  │ Anonymized prompt│
│ with PII       │       │              │       │ safe to transmit │
└────────────────┘       └──────────────┘       └──────────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │   Call any LLM   │
                                                 └──────────────────┘
                                                          │
                                                          ▼
┌────────────────┐       ┌──────────────┐       ┌──────────────────┐
│ Final output   │  ◀──  │ deanonymize()│  ◀──  │ Model response   │
│ PII restored   │       │              │       │ still with tokens│
└────────────────┘       └──────────────┘       └──────────────────┘
```

Only the middle box ever touches the network. Your vendor sees tokens like `[PESEL_001]`, never `44051401359`.

## Why tokens survive the LLM

Modern LLMs treat `[PESEL_001]` as a single semantic unit: a placeholder they should leave alone. In practice, well-prompted models preserve these tokens across summarization, translation, reformatting, and even reordering. A token reappearing in the response (in any order, any number of times) still looks up correctly in the `Mapping`, because `Mapping` is token → value, not position-based.

If the LLM hallucinates a token that was never issued (e.g. `[PESEL_042]` when only `[PESEL_001]` exists), `Deanonymizer` leaves it in place rather than restoring garbage. You'll see the stray token in the output — a clearer signal than silent corruption.

## Prompt advice

Add one line to your system prompt to reduce the chance of the LLM mangling tokens:

> Keep every token of the form `[TYPE_NNN]` intact — do not expand, translate, or rephrase them.

That's it. No further prompt engineering is usually needed.

## Programmatic examples

Minimal shape, provider-agnostic:

```python
from llm_safe_pl import Shield

shield = Shield()

anonymized = shield.anonymize(user_document).text

# ---- any LLM call goes here ----
llm_response = call_llm(anonymized)
# --------------------------------

final = shield.deanonymize(llm_response)
```

Runnable provider-specific scripts:

- [`examples/openai_integration.py`](../examples/openai_integration.py)
- [`examples/anthropic_integration.py`](../examples/anthropic_integration.py)

## Shared Mapping across calls

A Shield is a persistent container. Two documents processed by the same Shield share a Mapping, which means:

- Same value → same token across documents.
- The Mapping grows monotonically. Serialize it if you want to persist state between processes.

If you need isolation between documents, create a fresh `Shield()` per document.

## Saving and loading Mappings

```python
# Save after anonymizing.
shield_state = shield.mapping.to_json()  # str

# Load later (possibly in a different process).
from llm_safe_pl import Mapping, Shield
loaded = Mapping.from_json(shield_state)
shield = Shield(mapping=loaded)

# shield.anonymize(...) reuses tokens already in `loaded`.
# shield.deanonymize(...) can restore any original whose token lives in `loaded`.
```

## What the LLM sees

For input:

```
Klient Anna Nowak (PESEL 44051401359) zamówiła dostawę na email anna@example.pl.
```

The LLM sees:

```
Klient Anna Nowak (PESEL [PESEL_001]) zamówiła dostawę na email [EMAIL_001].
```

(Note `Anna Nowak` remains visible in v0.1 — PERSON detection requires the `[ner]` extra scheduled for v0.1.1.)

After the LLM replies, the token form is reversed back to the original before your code sees the final string.

## Batched processing

```python
shield = Shield()
for document in stream_of_documents():
    result = shield.anonymize(document)
    llm_output = call_llm(result.text)
    final = shield.deanonymize(llm_output)
    yield final
```

The Mapping accumulates across the loop, so if the same PESEL appears in document 1 and document 5, both get `[PESEL_001]`. This can be a feature (cross-document consistency) or a leak of cross-document correlation; create a new Shield per document when you want isolation.

## Caveats

- **PERSON detection is not in v0.1 core.** Names like `Anna Nowak` remain visible. Install `pip install "llm-safe-pl[ner]"` once v0.1.1 ships to opt into spaCy-based NER.
- **The Mapping is your responsibility to protect.** Losing it means losing the ability to deanonymize. Persisting it to disk is the same as persisting PII — secure it accordingly.
- **Nothing here replaces legal review.** The library is a technical tool; GDPR compliance is the user's responsibility. See [`limitations.md`](limitations.md).
