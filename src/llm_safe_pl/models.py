"""Core data types: PIIType, Match, Mapping, AnonymizeResult.

Mapping is the only non-frozen type here — it accumulates state while a Shield
processes documents. Everything else is an immutable value object.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    """

    SCHEMA_VERSION = 1
    _TOKEN_FORMAT = "[{type}_{counter:03d}]"

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
        token = self._TOKEN_FORMAT.format(type=pii_type.value.upper(), counter=counter)
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
        version = data.get("schema_version")
        if version != cls.SCHEMA_VERSION:
            raise ValueError(f"Unsupported mapping schema version: {version!r}")
        m = cls()
        m._counters = {PIIType(t): int(n) for t, n in data.get("counters", {}).items()}
        for entry in data["entries"]:
            token = entry["token"]
            pii_type = PIIType(entry["type"])
            value = entry["value"]
            m._forward[(pii_type, value)] = token
            m._reverse[token] = (pii_type, value)
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
