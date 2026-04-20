"""Tests for PESEL, NIP, and REGON checksum validators."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from llm_safe_pl.validators.checksum import (
    _NIP_WEIGHTS,
    _PESEL_WEIGHTS,
    _REGON_9_WEIGHTS,
    _REGON_14_WEIGHTS,
    is_valid_nip,
    is_valid_pesel,
    is_valid_regon,
)


def _pesel_with_check(body10: str) -> str:
    digits = [int(c) for c in body10]
    total = sum(d * w for d, w in zip(digits, _PESEL_WEIGHTS, strict=True))
    return body10 + str((10 - total % 10) % 10)


def _nip_with_check(body9: str) -> str | None:
    digits = [int(c) for c in body9]
    check = sum(d * w for d, w in zip(digits, _NIP_WEIGHTS, strict=True)) % 11
    if check == 10:
        return None
    return body9 + str(check)


def _regon9_with_check(body8: str) -> str:
    digits = [int(c) for c in body8]
    check = sum(d * w for d, w in zip(digits, _REGON_9_WEIGHTS, strict=True)) % 11
    if check == 10:
        check = 0
    return body8 + str(check)


def _regon14_with_check(body13: str) -> str:
    digits = [int(c) for c in body13]
    check = sum(d * w for d, w in zip(digits, _REGON_14_WEIGHTS, strict=True)) % 11
    if check == 10:
        check = 0
    return body13 + str(check)


class TestPesel:
    @pytest.mark.parametrize(
        "pesel",
        [
            "44051401359",
            "92010100003",
            "02070803628",
            "90010112349",
        ],
    )
    def test_known_valid(self, pesel: str) -> None:
        assert is_valid_pesel(pesel)

    @pytest.mark.parametrize(
        "pesel",
        [
            "44051401358",
            "44051401350",
            "00000000001",
            "99999999999",
        ],
    )
    def test_known_invalid(self, pesel: str) -> None:
        assert not is_valid_pesel(pesel)

    def test_all_zeros_is_valid_by_checksum(self) -> None:
        assert is_valid_pesel("00000000000")

    @pytest.mark.parametrize("bad", ["", "1234567890", "123456789012", "4405140135a"])
    def test_wrong_shape(self, bad: str) -> None:
        assert not is_valid_pesel(bad)

    def test_whitespace_rejected(self) -> None:
        assert not is_valid_pesel(" 4405140135")
        assert not is_valid_pesel("44051401359 ")

    def test_unicode_digits_rejected(self) -> None:
        assert not is_valid_pesel("４４０５１４０１３５９")  # noqa: RUF001

    @given(body=st.text(alphabet="0123456789", min_size=10, max_size=10))
    def test_generator_produces_valid(self, body: str) -> None:
        assert is_valid_pesel(_pesel_with_check(body))

    @given(
        body=st.text(alphabet="0123456789", min_size=10, max_size=10),
        position=st.integers(min_value=0, max_value=10),
        delta=st.integers(min_value=1, max_value=9),
    )
    def test_single_digit_mutation_breaks_validity(
        self, body: str, position: int, delta: int
    ) -> None:
        valid = _pesel_with_check(body)
        mutated_digit = (int(valid[position]) + delta) % 10
        mutated = valid[:position] + str(mutated_digit) + valid[position + 1 :]
        assert not is_valid_pesel(mutated)


class TestNip:
    @pytest.mark.parametrize(
        "nip",
        [
            "5260001246",
            "1070001927",
            "7272445205",
        ],
    )
    def test_known_valid(self, nip: str) -> None:
        assert is_valid_nip(nip)

    @pytest.mark.parametrize(
        "nip",
        [
            "5260001245",
            "1070001921",
            "5260001240",
        ],
    )
    def test_known_invalid(self, nip: str) -> None:
        assert not is_valid_nip(nip)

    @pytest.mark.parametrize("bad", ["", "123456789", "12345678901", "526000124a"])
    def test_wrong_shape(self, bad: str) -> None:
        assert not is_valid_nip(bad)

    def test_body_with_check_of_10_is_always_invalid(self) -> None:
        # Body "000000003" produces weighted sum 3*7 = 21, and 21 % 11 == 10.
        # A NIP with this body is invalid regardless of its trailing digit.
        body = "000000003"
        for last in "0123456789":
            assert not is_valid_nip(body + last)

    @given(body=st.text(alphabet="0123456789", min_size=9, max_size=9))
    def test_generator_produces_valid(self, body: str) -> None:
        nip = _nip_with_check(body)
        if nip is None:
            return
        assert is_valid_nip(nip)

    @given(
        body=st.text(alphabet="0123456789", min_size=9, max_size=9),
        position=st.integers(min_value=0, max_value=9),
        delta=st.integers(min_value=1, max_value=9),
    )
    def test_single_digit_mutation_breaks_validity(
        self, body: str, position: int, delta: int
    ) -> None:
        nip = _nip_with_check(body)
        if nip is None:
            return
        mutated_digit = (int(nip[position]) + delta) % 10
        mutated = nip[:position] + str(mutated_digit) + nip[position + 1 :]
        assert not is_valid_nip(mutated)


class TestRegon:
    @pytest.mark.parametrize(
        "regon",
        [
            "123456785",
            "012345675",
            "987654326",
        ],
    )
    def test_known_valid_9_digit(self, regon: str) -> None:
        assert is_valid_regon(regon)

    @pytest.mark.parametrize("regon", ["123456784", "999999999"])
    def test_known_invalid_9_digit(self, regon: str) -> None:
        assert not is_valid_regon(regon)

    def test_generated_9_digit_valid(self) -> None:
        assert is_valid_regon(_regon9_with_check("12345678"))

    def test_generated_14_digit_valid(self) -> None:
        body9 = _regon9_with_check("12345678")
        # _regon14_with_check expects 13 body chars; add 4 to reach 13.
        full = _regon14_with_check(body9 + "0000")
        assert is_valid_regon(full)

    def test_14_digit_with_bad_inner_rejected(self) -> None:
        body9 = "123456784"  # inner 9-digit check deliberately wrong
        assert not is_valid_regon(body9)
        full = _regon14_with_check(body9 + "0000")
        assert not is_valid_regon(full)

    @pytest.mark.parametrize("length", [0, 1, 5, 8, 10, 13, 15, 20])
    def test_wrong_length(self, length: int) -> None:
        assert not is_valid_regon("1" * length)

    def test_non_digit_rejected(self) -> None:
        assert not is_valid_regon("12345678a")
        assert not is_valid_regon("1234567890abcd")

    def test_unicode_digits_rejected(self) -> None:
        assert not is_valid_regon("１２３４５６７８５")  # noqa: RUF001

    @given(body=st.text(alphabet="0123456789", min_size=8, max_size=8))
    def test_generator_9_digit_valid(self, body: str) -> None:
        assert is_valid_regon(_regon9_with_check(body))

    @given(body=st.text(alphabet="0123456789", min_size=13, max_size=13))
    def test_generator_14_digit_valid_when_inner_valid(self, body: str) -> None:
        # Generator constraint: the first 9 chars must themselves be a valid 9-digit REGON.
        inner_body, tail = body[:8], body[9:]
        inner = _regon9_with_check(inner_body)
        full = _regon14_with_check(inner + tail)
        assert is_valid_regon(full)

    # Note: no single-digit-mutation property test for REGON.
    # REGON collapses check=10 to check=0, so mutations that take the weighted
    # sum from ≡0 to ≡10 mod 11 (or vice versa) preserve validity — the property
    # is mathematically false, not a bug.
