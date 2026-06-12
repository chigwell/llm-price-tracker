from decimal import Decimal

from llm_price_tracker.diff import diff_snapshots
from llm_price_tracker.models import ModelPrice


def price(provider: str, model: str, input_price: str) -> ModelPrice:
    return ModelPrice(
        provider=provider,
        model=model,
        input_per_1m=Decimal(input_price),
        source_url="https://example.com/pricing",
        source_type="html",
        fetched_at="2026-06-12T09:00:00Z",
    )


def test_diff_detects_changed_and_new_models() -> None:
    result = diff_snapshots(
        [price("openai", "gpt-a", "1.00")],
        [price("openai", "gpt-a", "2.00"), price("google_gemini", "gemini-a", "0.50")],
    )

    assert result.new_providers == ["google_gemini"]
    assert result.new_models[0].model == "gemini-a"
    assert result.changed_prices[0].field == "input_per_1m"
    assert result.changed_prices[0].old == Decimal("1.00")
    assert result.changed_prices[0].new == Decimal("2.00")
