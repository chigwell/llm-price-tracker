from decimal import Decimal
from pathlib import Path

from llm_price_tracker.providers import anthropic, google_gemini, kimi, minimax, openai, qwen

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_openai_fixture() -> None:
    prices = openai.fetch_prices(fixture("openai_pricing.html"))
    by_identity = {(price.model, price.modality, price.price_condition): price for price in prices}
    assert by_identity[("gpt-5.3-codex", None, None)].input_per_1m == Decimal("1.75")
    assert by_identity[("gpt-5.4", None, "<272K context length")].output_per_1m == Decimal("15")
    assert by_identity[("gpt-5.4-mini", None, None)].cached_input_per_1m == Decimal("0.075")
    assert by_identity[("gpt-5.5", None, "<272K context length")].input_per_1m == Decimal("5")
    assert by_identity[("gpt-image-2", "image", None)].output_per_1m == Decimal("30")
    assert by_identity[("gpt-image-2", "text", None)].output_per_1m is None


def test_anthropic_fixture() -> None:
    prices = anthropic.fetch_prices(fixture("anthropic_pricing.html"))
    assert prices[0].model == "claude-sonnet-4.5"
    assert prices[0].cache_write_5m_per_1m == Decimal("3.75")


def test_google_gemini_fixture_tiered_prices() -> None:
    prices = google_gemini.fetch_prices(fixture("google_gemini_pricing.html"))
    assert len(prices) == 2
    assert prices[0].price_condition == "prompts <= 200k tokens"
    assert prices[1].input_per_1m == Decimal("2.50")


def test_kimi_fixture() -> None:
    prices = kimi.fetch_prices(fixture("kimi_pricing.html"))
    assert prices[0].model == "kimi-k2.6"
    assert prices[0].cached_input_per_1m == Decimal("0.16")


def test_minimax_fixture() -> None:
    prices = minimax.fetch_prices(fixture("minimax_pricing.html"))
    by_model = {price.model: price for price in prices}
    assert by_model["minimax-m3"].cached_input_per_1m == Decimal("0.06")
    assert by_model["minimax-m2.7"].cache_write_5m_per_1m == Decimal("0.375")


def test_qwen_fixture() -> None:
    prices = qwen.fetch_prices(fixture("qwen_pricing.html"))
    assert prices[0].model == "qwen-plus"
    assert prices[0].input_per_1m == Decimal("0.115")
