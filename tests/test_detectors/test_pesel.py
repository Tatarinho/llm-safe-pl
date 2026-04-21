"""Tests for PeselDetector."""

import pytest

from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> PeselDetector:
    return PeselDetector()


class TestPeselDetector:
    def test_metadata(self, detector: PeselDetector) -> None:
        assert detector.name == "pesel"
        assert detector.pii_type is PIIType.PESEL

    def test_detects_bare_valid_pesel(self, detector: PeselDetector) -> None:
        matches = list(detector.detect("44051401359"))
        assert len(matches) == 1
        m = matches[0]
        assert m.value == "44051401359"
        assert (m.start, m.end) == (0, 11)
        assert m.type is PIIType.PESEL
        assert m.detector == "pesel"

    def test_detects_pesel_in_context(self, detector: PeselDetector) -> None:
        text = "Pan Jan, PESEL 44051401359, urodzony w 1944."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "44051401359"
        assert text[matches[0].start : matches[0].end] == "44051401359"

    def test_rejects_invalid_checksum(self, detector: PeselDetector) -> None:
        assert list(detector.detect("PESEL: 44051401358")) == []

    @pytest.mark.parametrize("bad", ["1234567890", "123456789012", "4405140135A"])
    def test_rejects_wrong_shape(self, detector: PeselDetector, bad: str) -> None:
        assert list(detector.detect(bad)) == []

    def test_does_not_match_embedded_in_longer_digit_run(self, detector: PeselDetector) -> None:
        assert list(detector.detect("1234567890123")) == []

    def test_multiple_matches(self, detector: PeselDetector) -> None:
        text = "Dwa PESEL-e: 44051401359 oraz 92010100003."
        matches = list(detector.detect(text))
        assert [m.value for m in matches] == ["44051401359", "92010100003"]

    def test_empty_text(self, detector: PeselDetector) -> None:
        assert list(detector.detect("")) == []

    def test_no_digits(self, detector: PeselDetector) -> None:
        assert list(detector.detect("nothing here but prose")) == []
