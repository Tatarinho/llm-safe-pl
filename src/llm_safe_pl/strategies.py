"""Anonymization strategies.

v0.1 ships only the ``TOKEN`` strategy, which replaces detected PII with
Mapping-allocated placeholders of the form ``[TYPE_NNN]``. ``mask`` (pure
character replacement) and ``fake`` (Faker-based realistic substitution) are
scheduled for later releases; the enum shape is locked now so the Anonymizer
constructor signature does not have to change when they land.
"""

from enum import Enum


class Strategy(str, Enum):
    TOKEN = "token"
