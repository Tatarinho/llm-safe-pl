# Exception hierarchy

`llm-safe-pl` exposes a small typed hierarchy from `llm_safe_pl.errors` (also
re-exported from the top-level package). All library errors descend from
`LlmSafeError`; specific subclasses also inherit from a relevant builtin so
existing `except ValueError` code keeps catching them.

```
Exception
└── LlmSafeError
    ├── MappingError      (also subclass of ValueError)
    ├── InputSizeError    (also subclass of ValueError)
    └── DetectorError     (also subclass of RuntimeError)
```

## When each is raised

| Class             | Raised by                                       | Builtin compat   |
|-------------------|-------------------------------------------------|------------------|
| `MappingError`    | `Mapping.from_dict` / `from_json` validation    | `ValueError`     |
| `InputSizeError`  | `Shield.anonymize` / `detect` exceeding `max_input_bytes` | `ValueError` |
| `DetectorError`   | Reserved for detector-dispatch failures; the class is exported but not yet raised internally | `RuntimeError` |

## Why typed classes

A bare `ValueError` doesn't tell the caller whether the problem is hostile
mapping JSON, an oversized input, or a bug — they all look the same in
`except`. The typed hierarchy lets handlers branch on cause:

```python
from llm_safe_pl import InputSizeError, MappingError, Shield

shield = Shield(max_input_bytes=1_000_000)
try:
    result = shield.anonymize(text)
except InputSizeError:
    # Caller-side: trim or reject the input.
    ...
except MappingError:
    # Hostile or corrupt persisted Mapping — treat as integrity failure.
    ...
```

## `DetectorError` deliberately drops context

`DetectorError.__init__` accepts only `detector_name` — never the input text or
an exception cause. Both can carry PII; surfacing them in a stack trace is the
class of leak the typed wrapper exists to prevent. Use `raise DetectorError(name) from None`
when re-raising a wrapped detector failure.
