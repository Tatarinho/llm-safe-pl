"""Luhn checksum validator (credit card numbers, ISO/IEC 7812).

The Luhn algorithm sums the digits of the number, doubling every second digit
from the right (subtracting 9 when the doubled value is >= 10). A number is
valid when the total is divisible by 10.
"""

from __future__ import annotations

_MIN_CARD_LENGTH = 13
_MAX_CARD_LENGTH = 19


def is_valid_luhn(s: str) -> bool:
    if not (_MIN_CARD_LENGTH <= len(s) <= _MAX_CARD_LENGTH):
        return False
    if not (s.isascii() and s.isdigit()):
        return False
    total = 0
    for position, ch in enumerate(reversed(s)):
        digit = int(ch)
        if position % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
