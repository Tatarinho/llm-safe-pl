"""Guardrail tests for the locked public API surface."""

import llm_safe_pl


def test_public_api_exports_are_importable() -> None:
    from llm_safe_pl import AnonymizeResult, Mapping, Match, PIIType, Shield

    assert Shield is not None
    assert Match is not None
    assert Mapping is not None
    assert AnonymizeResult is not None
    assert PIIType is not None


def test_all_matches_expected_surface() -> None:
    assert set(llm_safe_pl.__all__) == {
        "AnonymizeResult",
        "Mapping",
        "Match",
        "PIIType",
        "Shield",
    }


def test_version_is_defined() -> None:
    assert isinstance(llm_safe_pl.__version__, str)
    assert llm_safe_pl.__version__
