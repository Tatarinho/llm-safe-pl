"""Tests for the Strategy enum."""

from llm_safe_pl.strategies import Strategy


class TestStrategy:
    def test_only_member_in_v0_1_is_token(self) -> None:
        assert {m.name for m in Strategy} == {"TOKEN"}

    def test_token_value_is_lowercase_string(self) -> None:
        assert Strategy.TOKEN.value == "token"

    def test_strategy_is_str_subclass(self) -> None:
        assert isinstance(Strategy.TOKEN, str)
        assert Strategy.TOKEN == "token"
