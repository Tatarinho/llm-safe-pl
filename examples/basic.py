"""Minimal programmatic usage of llm-safe-pl.

Shows the three-step round-trip: anonymize -> (imaginary LLM call) -> deanonymize.
Uses core install only; no extras needed.

Run: python examples/basic.py
"""

from llm_safe_pl import Shield


def main() -> None:
    shield = Shield()

    document = (
        "Klient: Anna Nowak\n"
        "PESEL: 44051401359\n"
        "NIP: 526-000-12-46\n"
        "Tel: +48 600 123 456\n"
        "Email: anna@example.pl"
    )

    print("Original document:")
    print(document)
    print()

    result = shield.anonymize(document)
    print("Anonymized (safe to send to an LLM):")
    print(result.text)
    print()

    print(f"Detected {len(result.matches)} PII item(s):")
    for match in result.matches:
        print(f"  {match.type.value:15} {match.value!r}")
    print()

    # Pretend the LLM responded by referencing the anonymized tokens.
    llm_response = (
        f"Użytkownik {result.matches[0].value if False else '[PERSON_001]'} "
        f"nie został wykryty bez rozszerzenia [ner]. "
        f"Kontakt telefoniczny: {'[PHONE_001]'}. "
        f"Identyfikator podatkowy: {'[NIP_001]'}."
    )
    print("Fake LLM response (references tokens):")
    print(llm_response)
    print()

    restored = shield.deanonymize(llm_response)
    print("After deanonymize (original values restored):")
    print(restored)


if __name__ == "__main__":
    main()
