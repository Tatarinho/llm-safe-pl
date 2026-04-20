"""Tests for the generic IBAN validator."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from llm_safe_pl.validators.iban import IBAN_LENGTHS, is_valid_iban


def _iban_with_check(country: str, bban: str) -> str:
    # Solve mod-97 for the 2 check digits.
    expected_len = IBAN_LENGTHS[country]
    assert len(country) == 2 and len(bban) == expected_len - 4
    placeholder = bban + country + "00"
    numeric = "".join(str(ord(c) - ord("A") + 10) if c.isalpha() else c for c in placeholder)
    check = 98 - int(numeric) % 97
    return country + f"{check:02d}" + bban


class TestIban:
    @pytest.mark.parametrize(
        "iban",
        [
            "GB82WEST12345698765432",  # UK example from IBAN spec
            "DE89370400440532013000",  # German example
            "FR1420041010050500013M02606",  # French with letter in BBAN
            "MT84MALT011000012345MTLCAST001S",  # Malta — 31 chars
            "NO9386011117947",  # Norway — 15 chars (minimum)
        ],
    )
    def test_known_valid(self, iban: str) -> None:
        assert is_valid_iban(iban)

    def test_generated_pl_iban_is_valid(self) -> None:
        # A valid PL IBAN built via our helper (BBAN of 24 chars for PL).
        iban = _iban_with_check("PL", "1090101400000712198128740000"[:24])
        assert iban.startswith("PL")
        assert len(iban) == 28
        assert is_valid_iban(iban)

    @pytest.mark.parametrize(
        "iban",
        [
            "GB82WEST12345698765431",  # wrong check
            "DE89370400440532013001",  # wrong check
            "PL00000000000000000000000000",  # zero check digits, all-zero BBAN
        ],
    )
    def test_known_invalid_checksum(self, iban: str) -> None:
        assert not is_valid_iban(iban)

    def test_unknown_country_rejected(self) -> None:
        assert not is_valid_iban("XY12345678901234567890")

    def test_wrong_length_for_country_rejected(self) -> None:
        # PL expects 28; give 27.
        assert not is_valid_iban("PL1234567890123456789012345")

    def test_lowercase_rejected(self) -> None:
        # Valid GB IBAN, lowercased — strict validator rejects.
        assert not is_valid_iban("gb82west12345698765432")

    def test_check_digits_non_numeric_rejected(self) -> None:
        # Valid DE IBAN shape but check digits are letters.
        assert not is_valid_iban("DEXY370400440532013000")

    def test_bban_with_invalid_chars_rejected(self) -> None:
        assert not is_valid_iban("DE89370400440532013-00")

    def test_too_short_rejected(self) -> None:
        assert not is_valid_iban("PL")
        assert not is_valid_iban("PL12")
        assert not is_valid_iban("")

    def test_whitespace_inside_rejected(self) -> None:
        assert not is_valid_iban("PL61 1090 1014 0000 0712 1981 2874")

    @given(bban=st.text(alphabet="0123456789", min_size=24, max_size=24))
    def test_generator_pl_produces_valid(self, bban: str) -> None:
        assert is_valid_iban(_iban_with_check("PL", bban))

    @given(
        bban=st.text(alphabet="0123456789", min_size=24, max_size=24),
        position=st.integers(min_value=0, max_value=27),
        delta=st.integers(min_value=1, max_value=9),
    )
    def test_single_digit_mutation_breaks_validity(
        self, bban: str, position: int, delta: int
    ) -> None:
        iban = _iban_with_check("PL", bban)
        ch = iban[position]
        if not ch.isdigit():
            # Position is in the country code; this test focuses on digit positions.
            return
        mutated_digit = (int(ch) + delta) % 10
        mutated = iban[:position] + str(mutated_digit) + iban[position + 1 :]
        assert not is_valid_iban(mutated)
