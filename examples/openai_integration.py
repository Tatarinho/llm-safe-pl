"""Full anonymize -> OpenAI -> deanonymize round-trip.

Requirements:
    pip install llm-safe-pl openai
    export OPENAI_API_KEY=sk-...

The LLM call is commented out by default so the script runs without hitting
the network. Uncomment the ``response = client.chat.completions.create(...)``
block to exercise the real API.

Run: python examples/openai_integration.py
"""

from llm_safe_pl import Shield

# Uncomment to use the real OpenAI client:
# from openai import OpenAI
#
# client = OpenAI()


def main() -> None:
    shield = Shield()

    document = (
        "Klient Anna Nowak (PESEL 44051401359) zamówiła dostawę. "
        "Kontakt telefoniczny: +48 600 123 456, email anna@example.pl. "
        "Faktura na NIP 526-000-12-46."
    )

    # 1. Anonymize before the LLM sees anything sensitive.
    anonymized = shield.anonymize(document)
    print("Sending to OpenAI:")
    print(anonymized.text)
    print()

    # 2. Call the LLM. Fake response below so the script runs offline —
    #    uncomment the real call to hit the OpenAI API.
    #
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": (
    #                 "You are an assistant that summarises customer orders. "
    #                 "Keep every token of the form [TYPE_NNN] intact — do not "
    #                 "expand, translate, or rephrase them."
    #             ),
    #         },
    #         {"role": "user", "content": anonymized.text},
    #     ],
    # )
    # llm_output = response.choices[0].message.content or ""

    llm_output = (
        "Podsumowanie zamówienia:\n"
        "- Klient identyfikowany przez [PESEL_001].\n"
        "- Kontakt: [PHONE_001] lub [EMAIL_001].\n"
        "- Faktura VAT: [NIP_001]."
    )

    print("LLM response (still anonymized):")
    print(llm_output)
    print()

    # 3. Restore original values using the mapping built during anonymize().
    final = shield.deanonymize(llm_output)
    print("Final, de-anonymized output:")
    print(final)


if __name__ == "__main__":
    main()
