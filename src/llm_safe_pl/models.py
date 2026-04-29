"""Core data types: PIIType, Match, Mapping, AnonymizeResult.

Mapping is the only non-frozen type here — it accumulates state while a Shield
processes documents. Everything else is an immutable value object.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from llm_safe_pl.errors import MappingError

_TOKEN_SHAPE = re.compile(r"^\[([A-Z][A-Z_]*)_(\d+)\]$")


class PIIType(str, Enum):
    """Categories of personally identifiable information the library can handle.

    NER-sourced types (PERSON, ORGANIZATION, LOCATION) are included from v0.1
    even though the NER recognizer ships behind the ``[ner]`` extra — the enum
    describes what a Match can be, not what the current install can detect.
    """

    PESEL = "pesel"
    NIP = "nip"
    REGON = "regon"
    ID_CARD = "id_card"
    PASSPORT = "passport"
    PHONE = "phone"
    EMAIL = "email"
    IBAN = "iban"
    CREDIT_CARD = "credit_card"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"


@dataclass(frozen=True, slots=True)
class Match:
    """A single PII detection: what was found, where, and by whom."""

    type: PIIType
    value: str
    start: int
    end: int
    detector: str


class Mapping:
    """Bidirectional store of original PII values and their anonymization tokens.

    Tokens follow the format ``[TYPE_NNN]`` with a zero-padded 3-digit counter
    that grows beyond 3 digits without wrapping (e.g. ``[PESEL_1000]``). Within
    a single Mapping, the same (type, value) pair always yields the same token.

    Not thread-safe: ``token_for`` mutates the forward/reverse dicts and the
    per-type counter without locking. Do not share a Mapping (or the Shield
    that owns it) across threads unless the caller serializes writes.
    """

    __slots__ = ("_counters", "_forward", "_reverse")

    SCHEMA_VERSION = 1

    def __init__(self) -> None:
        self._forward: dict[tuple[PIIType, str], str] = {}
        self._reverse: dict[str, tuple[PIIType, str]] = {}
        self._counters: dict[PIIType, int] = {}

    def token_for(self, value: str, pii_type: PIIType) -> str:
        key = (pii_type, value)
        existing = self._forward.get(key)
        if existing is not None:
            return existing
        counter = self._counters.get(pii_type, 0) + 1
        self._counters[pii_type] = counter
        token = f"[{pii_type.value.upper()}_{counter:03d}]"
        self._forward[key] = token
        self._reverse[token] = (pii_type, value)
        return token

    def value_for(self, token: str) -> str | None:
        entry = self._reverse.get(token)
        return entry[1] if entry is not None else None

    def __len__(self) -> int:
        return len(self._reverse)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "counters": {t.value: n for t, n in self._counters.items()},
            "entries": [
                {"token": token, "type": pii_type.value, "value": value}
                for token, (pii_type, value) in self._reverse.items()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Mapping:
        """Load a Mapping from its JSON-dict shape with strict validation.

        Raises :class:`~llm_safe_pl.errors.MappingError` on any of: wrong schema
        version, malformed token shape, type/token-prefix mismatch, counters
        that don't cover their entries, non-int counter values, missing
        required fields. ``MappingError`` subclasses ``ValueError`` so existing
        ``except ValueError`` code keeps catching it.

        Validation matters because Mapping JSON is the cross-process trust
        boundary — a tampered file should fail loudly, not silently corrupt
        the Mapping.
        """
        if not isinstance(data, dict):
            raise MappingError(f"Mapping.from_dict expected a dict, got {type(data).__name__}")
        version = data.get("schema_version")
        if version != cls.SCHEMA_VERSION:
            raise MappingError(f"Unsupported mapping schema version: {version!r}")

        raw_counters = data.get("counters", {})
        if not isinstance(raw_counters, dict):
            raise MappingError(f"counters must be a dict, got {type(raw_counters).__name__}")
        counters: dict[PIIType, int] = {}
        for t, n in raw_counters.items():
            if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                raise MappingError(f"counter for {t!r} must be a non-negative int, got {n!r}")
            try:
                counters[PIIType(t)] = n
            except ValueError as exc:
                raise MappingError(f"unknown PII type in counters: {t!r}") from exc

        raw_entries = data.get("entries")
        if raw_entries is None:
            raise MappingError("Mapping.from_dict requires an 'entries' field")
        if not isinstance(raw_entries, list):
            raise MappingError(f"entries must be a list, got {type(raw_entries).__name__}")

        m = cls()
        m._counters = counters
        max_per_type: dict[PIIType, int] = {}
        for entry in raw_entries:
            if not isinstance(entry, dict):
                raise MappingError(f"each entry must be a dict, got {type(entry).__name__}")
            for required in ("token", "type", "value"):
                if required not in entry:
                    raise MappingError(f"entry missing required field {required!r}: {entry!r}")
            token = entry["token"]
            value = entry["value"]
            if not isinstance(token, str) or not isinstance(value, str):
                raise MappingError(f"entry token and value must be strings: {entry!r}")
            try:
                pii_type = PIIType(entry["type"])
            except ValueError as exc:
                raise MappingError(
                    f"unknown PII type in entry {entry!r}: {entry['type']!r}"
                ) from exc
            shape = _TOKEN_SHAPE.fullmatch(token)
            if shape is None:
                raise MappingError(f"token {token!r} does not match [TYPE_NNN] shape")
            token_type_prefix = shape.group(1)
            if token_type_prefix != pii_type.value.upper():
                raise MappingError(f"token {token!r} prefix does not match type {pii_type.value!r}")
            counter_n = int(shape.group(2))
            prev = max_per_type.get(pii_type, 0)
            if counter_n > prev:
                max_per_type[pii_type] = counter_n
            m._forward[(pii_type, value)] = token
            m._reverse[token] = (pii_type, value)

        for pii_type, observed_max in max_per_type.items():
            declared = counters.get(pii_type, 0)
            if declared < observed_max:
                raise MappingError(
                    f"counter for {pii_type.value!r} is {declared} but entry "
                    f"counter {observed_max} was issued"
                )
        return m

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> Mapping:
        return cls.from_dict(json.loads(raw))


@dataclass(frozen=True, slots=True)
class AnonymizeResult:
    """Result of a single ``Shield.anonymize()`` call: text, mapping, audit trail."""

    text: str
    mapping: Mapping
    matches: tuple[Match, ...]
