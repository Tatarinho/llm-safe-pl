"""Tests for EmailDetector."""

import pytest

from llm_safe_pl.detectors.email import EmailDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> EmailDetector:
    return EmailDetector()


class TestEmailDetector:
    def test_metadata(self, detector: EmailDetector) -> None:
        assert detector.name == "email"
        assert detector.pii_type is PIIType.EMAIL

    @pytest.mark.parametrize(
        "email",
        [
            "jan@example.pl",
            "first.last@domain.co.uk",
            "a+b@example.com",
            "user_name@sub.example.org",
        ],
    )
    def test_detects_common_shapes(self, detector: EmailDetector, email: str) -> None:
        matches = list(detector.detect(email))
        assert len(matches) == 1
        assert matches[0].value == email

    def test_detects_in_context(self, detector: EmailDetector) -> None:
        text = "Napisz na jan@example.pl jutro."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "jan@example.pl"

    def test_multiple_matches(self, detector: EmailDetector) -> None:
        text = "Kontakty: a@x.pl oraz b@y.com"
        matches = list(detector.detect(text))
        assert [m.value for m in matches] == ["a@x.pl", "b@y.com"]

    def test_rejects_without_at(self, detector: EmailDetector) -> None:
        assert list(detector.detect("plain.example.com")) == []

    def test_rejects_without_tld(self, detector: EmailDetector) -> None:
        assert list(detector.detect("user@hostname")) == []

    def test_empty_text(self, detector: EmailDetector) -> None:
        assert list(detector.detect("")) == []
