"""Tests for the Detector / RegexDetector abstractions."""

import re
from typing import ClassVar

import pytest

from llm_safe_pl.detectors.base import Detector, RegexDetector
from llm_safe_pl.models import PIIType


class _AllXDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.EMAIL
    name: ClassVar[str] = "all_x"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"x+")


class _LongXDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.EMAIL
    name: ClassVar[str] = "long_x"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"x+")

    def _is_valid(self, candidate: str) -> bool:
        return len(candidate) >= 3


class TestDetectorAbstract:
    def test_cannot_instantiate_abstract_detector(self) -> None:
        with pytest.raises(TypeError):
            Detector()  # type: ignore[abstract]


class TestRegexDetector:
    def test_yields_every_regex_match(self) -> None:
        matches = list(_AllXDetector().detect("x xx xxx yyy xxxx"))
        assert [m.value for m in matches] == ["x", "xx", "xxx", "xxxx"]

    def test_applies_validator_hook_to_filter_candidates(self) -> None:
        matches = list(_LongXDetector().detect("x xx xxx yyy xxxx"))
        assert [m.value for m in matches] == ["xxx", "xxxx"]

    def test_populates_match_metadata(self) -> None:
        text = "ab xx cd"
        match = next(iter(_AllXDetector().detect(text)))
        assert match.start == 3
        assert match.end == 5
        assert text[match.start : match.end] == match.value
        assert match.type is PIIType.EMAIL
        assert match.detector == "all_x"

    def test_yields_nothing_when_pattern_misses(self) -> None:
        assert list(_AllXDetector().detect("only y here")) == []

    def test_detect_is_idempotent_per_call(self) -> None:
        detector = _AllXDetector()
        first = list(detector.detect("xx yy xxx"))
        second = list(detector.detect("xx yy xxx"))
        assert first == second
