"""Weighted-sum checksum validators for Polish government identifiers.

Algorithms are per the official GUS and Ministerstwo Finansów specifications:

- PESEL: 11 digits, weights (1, 3, 7, 9, 1, 3, 7, 9, 1, 3), check = (10 - sum%10) % 10.
- NIP: 10 digits, weights (6, 5, 7, 2, 3, 4, 5, 6, 7), check = sum % 11, rejected if check == 10.
- REGON-9: 9 digits, weights (8, 9, 2, 3, 4, 5, 6, 7), check = sum % 11, 10 collapses to 0.
- REGON-14: 14 digits, weights (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8),
  check = sum % 11, 10 collapses to 0. The first 9 digits must themselves
  form a valid 9-digit REGON.

Inputs are required to be pure ASCII digits; fullwidth Unicode digits and any
other non-ASCII characters are rejected so the validators mirror what a
digit-only regex detector in Phase 3 would have matched.
"""

from __future__ import annotations

_PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
_NIP_WEIGHTS = (6, 5, 7, 2, 3, 4, 5, 6, 7)
_REGON_9_WEIGHTS = (8, 9, 2, 3, 4, 5, 6, 7)
_REGON_14_WEIGHTS = (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)


def _is_ascii_digits(s: str) -> bool:
    return s.isascii() and s.isdigit()


def is_valid_pesel(s: str) -> bool:
    if len(s) != 11 or not _is_ascii_digits(s):
        return False
    body, check_digit = s[:10], s[10]
    digits = [int(c) for c in body]
    total = sum(d * w for d, w in zip(digits, _PESEL_WEIGHTS, strict=True))
    expected = (10 - total % 10) % 10
    return expected == int(check_digit)


def is_valid_nip(s: str) -> bool:
    if len(s) != 10 or not _is_ascii_digits(s):
        return False
    body, check_digit = s[:9], s[9]
    digits = [int(c) for c in body]
    check = sum(d * w for d, w in zip(digits, _NIP_WEIGHTS, strict=True)) % 11
    if check == 10:
        return False
    return check == int(check_digit)


def is_valid_regon(s: str) -> bool:
    if not _is_ascii_digits(s):
        return False
    if len(s) == 9:
        return _check_regon_9(s)
    if len(s) == 14:
        return _check_regon_9(s[:9]) and _check_regon_14(s)
    return False


def _check_regon_9(s: str) -> bool:
    body, check_digit = s[:8], s[8]
    digits = [int(c) for c in body]
    check = sum(d * w for d, w in zip(digits, _REGON_9_WEIGHTS, strict=True)) % 11
    if check == 10:
        check = 0
    return check == int(check_digit)


def _check_regon_14(s: str) -> bool:
    body, check_digit = s[:13], s[13]
    digits = [int(c) for c in body]
    check = sum(d * w for d, w in zip(digits, _REGON_14_WEIGHTS, strict=True)) % 11
    if check == 10:
        check = 0
    return check == int(check_digit)
