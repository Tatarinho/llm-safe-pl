"""Tests for the typed exception hierarchy in ``llm_safe_pl.errors``."""

from __future__ import annotations

import pytest

from llm_safe_pl.errors import (
    DetectorError,
    InputSizeError,
    LlmSafeError,
    MappingError,
)


class TestHierarchy:
    def test_llm_safe_error_subclasses_exception(self) -> None:
        assert issubclass(LlmSafeError, Exception)
        assert not issubclass(LlmSafeError, ValueError)

    def test_mapping_error_is_value_error(self) -> None:
        assert issubclass(MappingError, LlmSafeError)
        assert issubclass(MappingError, ValueError)

    def test_input_size_error_is_value_error(self) -> None:
        assert issubclass(InputSizeError, LlmSafeError)
        assert issubclass(InputSizeError, ValueError)

    def test_detector_error_is_runtime_error(self) -> None:
        assert issubclass(DetectorError, LlmSafeError)
        assert issubclass(DetectorError, RuntimeError)


class TestExceptCompat:
    def test_mapping_error_caught_as_value_error(self) -> None:
        with pytest.raises(ValueError):
            raise MappingError("x")

    def test_input_size_error_caught_as_value_error(self) -> None:
        with pytest.raises(ValueError):
            raise InputSizeError("x")

    def test_mapping_error_caught_as_llm_safe_error(self) -> None:
        with pytest.raises(LlmSafeError):
            raise MappingError("x")

    def test_input_size_error_caught_as_llm_safe_error(self) -> None:
        with pytest.raises(LlmSafeError):
            raise InputSizeError("x")

    def test_detector_error_caught_as_llm_safe_error(self) -> None:
        with pytest.raises(LlmSafeError):
            raise DetectorError("pesel")


class TestDetectorError:
    def test_detector_name_attribute(self) -> None:
        e = DetectorError("pesel")
        assert e.detector_name == "pesel"

    def test_message_does_not_include_implicit_text(self) -> None:
        e = DetectorError("pesel")
        # The message includes the detector name only — never input text.
        assert str(e) == "detector 'pesel' failed"

    def test_does_not_accept_extra_args(self) -> None:
        # Signature is exactly (detector_name); a caller that tries to attach
        # text or a cause via extra args should fail loudly.
        with pytest.raises(TypeError):
            DetectorError("pesel", "44051401359")  # type: ignore[call-arg]
