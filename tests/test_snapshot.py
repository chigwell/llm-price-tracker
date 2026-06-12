import json
from decimal import Decimal

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.snapshot import load_snapshot, save_snapshot


def test_snapshot_round_trips_decimal_strings(tmp_path) -> None:
    path = tmp_path / "prices.json"
    prices = [
        ModelPrice(
            provider="openai",
            model="gpt-test",
            input_per_1m=Decimal("1.23"),
            source_url="https://example.com/pricing",
            source_type="html",
            fetched_at="2026-06-12T09:00:00Z",
        )
    ]
    save_snapshot(prices, str(path))

    raw = json.loads(path.read_text())
    assert raw[0]["input_per_1m"] == "1.23"
    assert load_snapshot(str(path))[0].input_per_1m == Decimal("1.23")
