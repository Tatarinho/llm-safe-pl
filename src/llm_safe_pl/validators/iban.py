"""Generic IBAN validator with SWIFT country-length registry and mod-97 check.

The mod-97 algorithm is identical for every country; only the total length
varies. The registry below reflects the published SWIFT IBAN specification
(https://www.swift.com/standards/data-standards/iban). Any country code absent
from the registry is rejected — validate-then-extend beats silently-accept.
"""

from __future__ import annotations

IBAN_LENGTHS: dict[str, int] = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28,
    "BA": 20, "BE": 16, "BG": 22, "BH": 22, "BI": 27,
    "BR": 29, "BY": 28, "CH": 21, "CR": 22, "CY": 28,
    "CZ": 24, "DE": 22, "DJ": 27, "DK": 18, "DO": 28,
    "EE": 20, "EG": 29, "ES": 24, "FI": 18, "FK": 18,
    "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23,
    "GL": 18, "GR": 27, "GT": 28, "HR": 21, "HU": 28,
    "IE": 22, "IL": 23, "IQ": 23, "IS": 26, "IT": 27,
    "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LC": 32,
    "LI": 21, "LT": 20, "LU": 20, "LV": 21, "LY": 25,
    "MC": 27, "MD": 24, "ME": 22, "MK": 19, "MN": 20,
    "MR": 27, "MT": 31, "MU": 30, "NI": 28, "NL": 18,
    "NO": 15, "OM": 23, "PK": 24, "PL": 28, "PS": 29,
    "PT": 25, "QA": 29, "RO": 24, "RS": 22, "RU": 33,
    "SA": 24, "SC": 31, "SD": 18, "SK": 24, "SI": 19,
    "SM": 27, "SO": 23, "ST": 25, "SV": 28, "TL": 23,
    "TN": 24, "TR": 26, "UA": 29, "VA": 22, "VG": 24,
    "XK": 20, "YE": 30,
}  # fmt: skip


def is_valid_iban(s: str) -> bool:
    if not s.isascii() or len(s) < 4:
        return False
    country = s[:2]
    if country not in IBAN_LENGTHS or len(s) != IBAN_LENGTHS[country]:
        return False
    # Check digits: 2 digits. (Country code is implicitly validated as uppercase
    # ASCII letters by the registry lookup — only such keys live in IBAN_LENGTHS.)
    if not s[2:4].isdigit():
        return False
    # BBAN: ASCII digits or uppercase letters.
    if not all(c.isdigit() or "A" <= c <= "Z" for c in s[4:]):
        return False
    # Rearrange (move country+checkdigits to the tail) and convert letters to numbers.
    rearranged = s[4:] + s[:4]
    numeric = "".join(str(ord(c) - ord("A") + 10) if c.isalpha() else c for c in rearranged)
    return int(numeric) % 97 == 1
