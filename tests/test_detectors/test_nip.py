"""Tests for NipDetector (bare and separator-formatted NIPs)."""

import pytest

from llm_safe_pl.detectors.nip import NipDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> NipDetector:
    return NipDetector()


class TestNipDetector:
    def test_metadata(self, detector: NipDetector) -> None:
        assert detector.name == "nip"
        assert detector.pii_type is PIIType.NIP

    def test_detects_bare_valid_nip(self, detector: NipDetector) -> None:
        matches = list(detector.detect("5260001246"))
        assert len(matches) == 1
        assert matches[0].value == "5260001246"

    @pytest.mark.parametrize(
        "text_value",
        [
            "526-000-12-46",
            "526 000 12 46",
            "526-000 12-46",
        ],
    )
    def test_detects_formatted_nips_and_preserves_formatting(
        self, detector: NipDetector, text_value: str
    ) -> None:
        matches = list(detector.detect(text_value))
        assert len(matches) == 1
        assert matches[0].value == text_value

    def test_span_covers_full_formatted_match(self, detector: NipDetector) -> None:
        text = "NIP: 526-000-12-46."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert text[matches[0].start : matches[0].end] == "526-000-12-46"

    def test_rejects_bare_invalid_checksum(self, detector: NipDetector) -> None:
        assert list(detector.detect("5260001245")) == []

    def test_rejects_formatted_invalid_checksum(self, detector: NipDetector) -> None:
        assert list(detector.detect("526-000-12-45")) == []

    def test_rejects_embedded_in_longer_digit_run(self, detector: NipDetector) -> None:
        assert list(detector.detect("12345678901")) == []

    def test_multiple_matches(self, detector: NipDetector) -> None:
        text = "NIPs: 5260001246 i 7272445205"
        matches = list(detector.detect(text))
        assert [m.value for m in matches] == ["5260001246", "7272445205"]

    def test_empty_text(self, detector: NipDetector) -> None:
        assert list(detector.detect("")) == []
