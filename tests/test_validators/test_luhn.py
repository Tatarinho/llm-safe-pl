"""Tests for the Luhn credit-card checksum validator."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from llm_safe_pl.validators.luhn import is_valid_luhn


def _luhn_with_check(body: str) -> str:
    # Compute the check digit that makes body + d pass Luhn.
    total = 0
    for position, ch in enumerate(reversed(body)):
        digit = int(ch)
        # The check digit we're appending will sit at position 0 from the right after we append,
        # so the body digits shift to positions 1..len(body) — we double positions 1, 3, 5, ...
        if position % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return body + str((10 - total % 10) % 10)


class TestLuhn:
    @pytest.mark.parametrize(
        "number",
        [
            "4532015112830366",
            "4111111111111111",
            "5555555555554444",
            "378282246310005",
            "6011111111111117",
            "30569309025904",
        ],
    )
    def test_known_valid(self, number: str) -> None:
        assert is_valid_luhn(number)

    @pytest.mark.parametrize(
        "number",
        [
            "4532015112830367",
            "4111111111111112",
            "1234567890123456",
        ],
    )
    def test_known_invalid(self, number: str) -> None:
        assert not is_valid_luhn(number)

    @pytest.mark.parametrize("length", [0, 1, 10, 12, 20, 25])
    def test_wrong_length(self, length: int) -> None:
        assert not is_valid_luhn("1" * length)

    def test_non_digit_rejected(self) -> None:
        assert not is_valid_luhn("4532-0151-1283-0366")
        assert not is_valid_luhn("4532 0151 1283 0366")
        assert not is_valid_luhn("4532015112830a66")

    def test_empty_rejected(self) -> None:
        assert not is_valid_luhn("")

    def test_all_zeros_of_card_length_is_valid_by_checksum(self) -> None:
        # Luhn doesn't reject all-zero strings within the valid length window.
        # Detectors are expected to filter these semantically.
        assert is_valid_luhn("0" * 16)

    @given(body=st.text(alphabet="0123456789", min_size=12, max_size=18))
    def test_generator_produces_valid(self, body: str) -> None:
        assert is_valid_luhn(_luhn_with_check(body))

    @given(
        body=st.text(alphabet="0123456789", min_size=12, max_size=18),
        position=st.integers(min_value=0, max_value=18),
        delta=st.integers(min_value=1, max_value=9),
    )
    def test_single_digit_mutation_breaks_validity(
        self, body: str, position: int, delta: int
    ) -> None:
        number = _luhn_with_check(body)
        if position >= len(number):
            return
        mutated_digit = (int(number[position]) + delta) % 10
        mutated = number[:position] + str(mutated_digit) + number[position + 1 :]
        assert not is_valid_luhn(mutated)
