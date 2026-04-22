"""Round-trip property tests: ``deanonymize(anonymize(x).text) == x``.

These exercise the top-level Shield contract that users actually rely on.
The text generator excludes ``[`` and ``]`` so hypothesis cannot synthesize
strings that collide with token shapes like ``[PESEL_001]`` — collision
semantics on malicious input are the deanonymizer's unit-test territory,
not this property.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from llm_safe_pl import Shield

_VALID_PESEL = "44051401359"
_VALID_NIP = "5260001246"
_VALID_NIP_DASHED = "526-000-12-46"
_VALID_REGON_9 = "123456785"
_VALID_IBAN = "PL61109010140000071219812874"
_VALID_CARD = "4532015112830366"
_VALID_EMAIL = "user@example.pl"
_VALID_PHONE = "+48 600 123 456"

_pii_samples = st.sampled_from(
    [
        _VALID_PESEL,
        _VALID_NIP,
        _VALID_NIP_DASHED,
        _VALID_REGON_9,
        _VALID_IBAN,
        _VALID_CARD,
        _VALID_EMAIL,
        _VALID_PHONE,
    ]
)

_safe_text = st.text(alphabet=st.characters(blacklist_characters="[]"), max_size=200)


@given(_safe_text)
def test_roundtrip_preserves_arbitrary_text(original: str) -> None:
    shield = Shield()
    result = shield.anonymize(original)
    restored = shield.deanonymize(result.text)
    assert restored == original


@given(st.lists(st.one_of(_safe_text, _pii_samples), max_size=20))
def test_roundtrip_with_embedded_pii(parts: list[str]) -> None:
    original = " ".join(parts)
    shield = Shield()
    result = shield.anonymize(original)
    restored = shield.deanonymize(result.text)
    assert restored == original
