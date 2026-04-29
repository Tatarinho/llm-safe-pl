"""Verify that importing llm_safe_pl emits the v0.2.1 deprecation warning."""

from __future__ import annotations

import importlib

import pytest


def test_import_emits_deprecation_warning() -> None:
    """``import llm_safe_pl`` must fire a DeprecationWarning pointing at the
    successor packages. The warning is the user-visible signal that this
    package is end-of-life; if it stops firing, the tombstone is broken."""
    import llm_safe_pl

    with pytest.warns(DeprecationWarning, match=r"pii-veil"):
        importlib.reload(llm_safe_pl)


def test_deprecation_warning_mentions_migration_doc() -> None:
    """The warning text must point users at MIGRATION.md so they can find
    the symbol map without scraping the README."""
    import llm_safe_pl

    with pytest.warns(DeprecationWarning) as captured:
        importlib.reload(llm_safe_pl)

    messages = [str(w.message) for w in captured]
    assert any("MIGRATION.md" in m for m in messages), messages
