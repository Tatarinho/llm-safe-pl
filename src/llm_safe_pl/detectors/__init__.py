"""Detectors that find PII in raw text.

``DEFAULT_DETECTORS`` is the ordered list used by the v0.1 anonymizer. Order is
informational today (detectors don't interact here) but will matter in Phase 4
when overlap resolution uses detector priority as a tiebreak.
"""

from llm_safe_pl.detectors.base import Detector, RegexDetector
from llm_safe_pl.detectors.credit_card import CreditCardDetector
from llm_safe_pl.detectors.email import EmailDetector
from llm_safe_pl.detectors.iban import IbanDetector
from llm_safe_pl.detectors.id_card import IdCardDetector
from llm_safe_pl.detectors.nip import NipDetector
from llm_safe_pl.detectors.passport import PassportDetector
from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.detectors.phone import PhoneDetector
from llm_safe_pl.detectors.regon import RegonDetector

DEFAULT_DETECTORS: list[Detector] = [
    PeselDetector(),
    NipDetector(),
    RegonDetector(),
    IdCardDetector(),
    PassportDetector(),
    IbanDetector(),
    EmailDetector(),
    PhoneDetector(),
    CreditCardDetector(),
]

__all__ = [
    "DEFAULT_DETECTORS",
    "CreditCardDetector",
    "Detector",
    "EmailDetector",
    "IbanDetector",
    "IdCardDetector",
    "NipDetector",
    "PassportDetector",
    "PeselDetector",
    "PhoneDetector",
    "RegexDetector",
    "RegonDetector",
]
