"""Tests for IbanDetector (Polish IBAN, bare and 4-digit-grouped)."""

import pytest

from llm_safe_pl.detectors.iban import IbanDetector
from llm_safe_pl.models import PIIType
from llm_safe_pl.validators.iban import IBAN_LENGTHS


def _valid_pl_iban_bare() -> str:
    bban = "1090101400000712198128"[:24].ljust(24, "0")
    placeholder = bban + "PL" + "00"
    numeric = "".join(str(ord(c) - ord("A") + 10) if c.isalpha() else c for c in placeholder)
    check = 98 - int(numeric) % 97
    return "PL" + f"{check:02d}" + bban


@pytest.fixture
def detector() -> IbanDetector:
    return IbanDetector()


class TestIbanDetector:
    def test_metadata(self, detector: IbanDetector) -> None:
        assert detector.name == "iban"
        assert detector.pii_type is PIIType.IBAN

    def test_detects_bare_valid(self, detector: IbanDetector) -> None:
        iban = _valid_pl_iban_bare()
        assert len(iban) == IBAN_LENGTHS["PL"]
        matches = list(detector.detect(iban))
        assert len(matches) == 1
        assert matches[0].value == iban

    def test_detects_spaced_valid(self, detector: IbanDetector) -> None:
        bare = _valid_pl_iban_bare()
        spaced = bare[:4] + " " + " ".join(bare[i : i + 4] for i in range(4, 28, 4))
        matches = list(detector.detect(spaced))
        assert len(matches) == 1
        assert matches[0].value == spaced

    def test_detects_in_context(self, detector: IbanDetector) -> None:
        bare = _valid_pl_iban_bare()
        text = f"Konto: {bare} (główne)"
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == bare

    def test_rejects_invalid_check_digits(self, detector: IbanDetector) -> None:
        # Flip the first check digit in a valid bare IBAN.
        bare = _valid_pl_iban_bare()
        broken = bare[:2] + ("1" if bare[2] != "1" else "2") + bare[3:]
        assert list(detector.detect(broken)) == []

    def test_rejects_wrong_length(self, detector: IbanDetector) -> None:
        assert list(detector.detect("PL1234567890123456789012345")) == []  # 27 chars

    def test_rejects_non_polish_prefix(self, detector: IbanDetector) -> None:
        # Even a valid-looking DE IBAN must not match — the detector regex is PL-only.
        assert list(detector.detect("DE89370400440532013000")) == []

    def test_empty_text(self, detector: IbanDetector) -> None:
        assert list(detector.detect("")) == []
