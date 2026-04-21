"""Tests for the Deanonymizer."""

from llm_safe_pl.anonymizer import Anonymizer
from llm_safe_pl.deanonymizer import Deanonymizer
from llm_safe_pl.detectors.email import EmailDetector
from llm_safe_pl.detectors.nip import NipDetector
from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.models import Mapping, PIIType


class TestDeanonymizer:
    def test_replaces_known_token(self) -> None:
        mapping = Mapping()
        mapping.token_for("Jan Kowalski", PIIType.PERSON)
        result = Deanonymizer().deanonymize("Osoba: [PERSON_001].", mapping)
        assert result == "Osoba: Jan Kowalski."

    def test_replaces_multiple_tokens(self) -> None:
        mapping = Mapping()
        mapping.token_for("Jan", PIIType.PERSON)
        mapping.token_for("Anna", PIIType.PERSON)
        result = Deanonymizer().deanonymize("Pierwszy: [PERSON_001], drugi: [PERSON_002].", mapping)
        assert result == "Pierwszy: Jan, drugi: Anna."

    def test_unknown_token_left_in_place(self) -> None:
        mapping = Mapping()
        mapping.token_for("Jan", PIIType.PERSON)
        text = "[PERSON_001] i [PERSON_999]"
        result = Deanonymizer().deanonymize(text, mapping)
        assert result == "Jan i [PERSON_999]"

    def test_empty_text(self) -> None:
        assert Deanonymizer().deanonymize("", Mapping()) == ""

    def test_text_with_no_tokens_passes_through(self) -> None:
        result = Deanonymizer().deanonymize("Plain prose, nothing to replace.", Mapping())
        assert result == "Plain prose, nothing to replace."

    def test_preserves_surrounding_text(self) -> None:
        mapping = Mapping()
        mapping.token_for("X", PIIType.PERSON)
        result = Deanonymizer().deanonymize("Przed [PERSON_001] po.", mapping)
        assert result == "Przed X po."

    def test_bracket_like_text_not_in_token_format_ignored(self) -> None:
        mapping = Mapping()
        mapping.token_for("X", PIIType.PERSON)
        # Lowercase type and non-numeric suffix should not be treated as tokens.
        text = "[person_001] [PERSON_ABC] [NOT-A-TOKEN]"
        result = Deanonymizer().deanonymize(text, mapping)
        assert result == text


class TestRoundTrip:
    def test_anonymize_then_deanonymize_restores_original(self) -> None:
        mapping = Mapping()
        anon = Anonymizer(
            detectors=[PeselDetector(), EmailDetector()],
            mapping=mapping,
        )
        original = "PESEL: 44051401359, email: jan@example.pl."
        result = anon.anonymize(original)
        restored = Deanonymizer().deanonymize(result.text, result.mapping)
        assert restored == original

    def test_round_trip_preserves_nip_formatting(self) -> None:
        mapping = Mapping()
        anon = Anonymizer(detectors=[NipDetector()], mapping=mapping)
        original = "NIP 526-000-12-46 oraz 5260001246 drugi raz."
        result = anon.anonymize(original)
        restored = Deanonymizer().deanonymize(result.text, result.mapping)
        assert restored == original

    def test_round_trip_survives_through_llm_like_rewording(self) -> None:
        # Simulate an LLM response that reorders tokens and adds prose around them.
        mapping = Mapping()
        anon = Anonymizer(
            detectors=[PeselDetector(), EmailDetector()],
            mapping=mapping,
        )
        anonymized = anon.anonymize("PESEL 44051401359, email jan@example.pl.")
        # Fake LLM response that reshuffles the tokens in a new sentence.
        llm_output = (
            f"The user can be reached at {'[EMAIL_001]'}. Their identifier is {'[PESEL_001]'}."
        )
        restored = Deanonymizer().deanonymize(llm_output, mapping)
        assert "jan@example.pl" in restored
        assert "44051401359" in restored
        # The mapping is shared, so Anonymizer's result and the LLM output share tokens.
        assert "[PESEL_001]" not in restored
        assert "[EMAIL_001]" not in restored
        assert anonymized.mapping is mapping
