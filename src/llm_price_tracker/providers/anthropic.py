"""Anthropic Claude pricing adapter."""

from __future__ import annotations

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.providers.common import slug_model_name
from llm_price_tracker.utils.html import html_table_rows, page_text, require_markers
from llm_price_tracker.utils.http import fetch_html
from llm_price_tracker.utils.money import parse_money
from llm_price_tracker.utils.time import utc_now_iso
from llm_price_tracker.validation import validate_prices

SOURCE_URL = "https://docs.anthropic.com/en/docs/about-claude/pricing"
PROVIDER = "anthropic"
DEFAULT_REQUIRED_MODELS = {"claude-sonnet-4.5", "claude-haiku-4.5"}


def fetch_prices(
    html: str | None = None,
    *,
    required_models: set[str] | None = None,
) -> list[ModelPrice]:
    source = html if html is not None else fetch_html(SOURCE_URL, provider=PROVIDER)
    require_markers(
        page_text(source),
        ["Model pricing", "Base Input Tokens", "Output Tokens"],
        provider=PROVIDER,
    )
    fetched_at = utc_now_iso()
    prices: list[ModelPrice] = []
    for row in html_table_rows(source):
        if len(row) < 6 or row[0].lower() == "model":
            continue
        if not row[0].lower().startswith("claude"):
            continue
        prices.append(
            ModelPrice(
                provider=PROVIDER,
                model=slug_model_name(row[0]),
                input_per_1m=parse_money(row[1]),
                cache_write_5m_per_1m=parse_money(row[2]),
                cache_write_1h_per_1m=parse_money(row[3]),
                cached_input_per_1m=parse_money(row[4]),
                output_per_1m=parse_money(row[5]),
                source_url=SOURCE_URL,
                source_type="html",
                fetched_at=fetched_at,
            )
        )
    required = (
        DEFAULT_REQUIRED_MODELS
        if required_models is None and html is None
        else required_models or set()
    )
    return validate_prices(prices, provider=PROVIDER, required_models=required)
