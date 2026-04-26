"""Hardening features added in v0.2.0: Shield.reset() and max_input_bytes.

Two short demos, each independent of the other.

Run: python examples/hardening.py
"""

from llm_safe_pl import Shield


def demo_reset() -> None:
    """Reset the accumulated mapping between unrelated documents."""
    print("--- Demo 1: Shield.reset() ---")
    shield = Shield()

    # Document A — sensitive, internal.
    doc_a = "Klient: PESEL 44051401359."
    result_a = shield.anonymize(doc_a)
    print(f"After document A: mapping has {len(shield.mapping)} entry/entries.")
    print(f"  text: {result_a.text}")

    # Without reset(), document A's tokens persist into the next call.
    # If document B happens to contain a literal '[PESEL_001]' (e.g. an LLM
    # response that the caller forgot to validate), `deanonymize` would
    # substitute it with A's PESEL.
    shield.reset()
    print(f"After reset(): mapping has {len(shield.mapping)} entry/entries.")

    # Document B — different user, different request.
    doc_b = "Inny klient: PESEL 92010100003."
    result_b = shield.anonymize(doc_b)
    print(f"After document B: mapping has {len(shield.mapping)} entry/entries.")
    print(f"  text: {result_b.text}")
    print()


def demo_max_input_bytes() -> None:
    """Refuse oversized input at the boundary."""
    print("--- Demo 2: max_input_bytes ---")
    # Cap at 100 bytes for demonstration; realistic values are MiB-scale.
    shield = Shield(max_input_bytes=100)

    small = "PESEL 44051401359 — fits."
    print(f"Small input ({len(small.encode('utf-8'))} bytes): accepted.")
    shield.anonymize(small)

    big = "x" * 200
    print(f"Big input ({len(big.encode('utf-8'))} bytes): rejected.")
    try:
        shield.anonymize(big)
    except ValueError as exc:
        print(f"  ValueError: {exc}")


if __name__ == "__main__":
    demo_reset()
    demo_max_input_bytes()
