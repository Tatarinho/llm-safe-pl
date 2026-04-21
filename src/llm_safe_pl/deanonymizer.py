"""Reverse anonymization: substitute tokens with their original values.

Tokens not present in the provided Mapping are left untouched in the output.
This matters for LLM round-trips: a model may hallucinate a token that was
never issued, and silently inserting garbage (or raising mid-stream) would be
worse than leaving the token visible so the caller notices.
"""

from __future__ import annotations

import re

from llm_safe_pl.models import Mapping

_TOKEN_RE = re.compile(r"\[[A-Z_]+_\d+\]")


class Deanonymizer:
    """Rewrite a string by replacing Mapping tokens with their original values."""

    def deanonymize(self, text: str, mapping: Mapping) -> str:
        def replace(match: re.Match[str]) -> str:
            token = match.group(0)
            value = mapping.value_for(token)
            return value if value is not None else token

        return _TOKEN_RE.sub(replace, text)
