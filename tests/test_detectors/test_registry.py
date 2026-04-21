"""Tests for the DEFAULT_DETECTORS registry."""

from llm_safe_pl.detectors import DEFAULT_DETECTORS
from llm_safe_pl.detectors.base import Detector
from llm_safe_pl.models import PIIType


class TestDefaultDetectors:
    def test_covers_all_nine_regex_detector_types(self) -> None:
        types = {d.pii_type for d in DEFAULT_DETECTORS}
        assert types == {
            PIIType.PESEL,
            PIIType.NIP,
            PIIType.REGON,
            PIIType.ID_CARD,
            PIIType.PASSPORT,
            PIIType.PHONE,
            PIIType.EMAIL,
            PIIType.IBAN,
            PIIType.CREDIT_CARD,
        }

    def test_every_entry_is_a_detector(self) -> None:
        for d in DEFAULT_DETECTORS:
            assert isinstance(d, Detector)
            assert isinstance(d.name, str)
            assert d.name  # non-empty

    def test_detector_names_are_unique(self) -> None:
        names = [d.name for d in DEFAULT_DETECTORS]
        assert len(names) == len(set(names))
