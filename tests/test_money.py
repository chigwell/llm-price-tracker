from decimal import Decimal

import pytest

from llm_price_tracker.exceptions import PricingParseError
from llm_price_tracker.utils.money import parse_money


def test_parse_money_usd_values() -> None:
    assert parse_money("$1.25 / 1M tokens") == Decimal("1.25")
    assert parse_money("US$0.115") == Decimal("0.115")
    assert parse_money("0.95") == Decimal("0.95")


def test_parse_money_optional_free() -> None:
    assert parse_money("Free of charge") is None
    assert parse_money("Free of charge", allow_free=True) == Decimal("0")


def test_parse_money_invalid() -> None:
    with pytest.raises(PricingParseError):
        parse_money("price pending")
