"""MiniMax pricing adapter."""

from __future__ import annotations

import re

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.providers.common import clean_markdown_cell, last_money, markdown_table_rows
from llm_price_tracker.utils.http import fetch_html
from llm_price_tracker.utils.time import utc_now_iso
from llm_price_tracker.validation import validate_prices

SOURCE_URL = "https://platform.minimax.io/docs/guides/pricing-paygo.md"
PROVIDER = "minimax"
DEFAULT_REQUIRED_MODELS = {"minimax-m3", "minimax-m2.7"}


def fetch_prices(
    html: str | None = None,
    *,
    required_models: set[str] | None = None,
) -> list[ModelPrice]:
    text = html if html is not None else fetch_html(SOURCE_URL, provider=PROVIDER)
    fetched_at = utc_now_iso()
    prices = _parse_markdown(text, fetched_at)
    required = (
        DEFAULT_REQUIRED_MODELS
        if required_models is None and html is None
        else required_models or set()
    )
    return validate_prices(prices, provider=PROVIDER, required_models=required)


def _parse_markdown(text: str, fetched_at: str) -> list[ModelPrice]:
    prices: list[ModelPrice] = []
    current_tier = "standard"
    for line in text.splitlines():
        if '<Tab title="Standard">' in line:
            current_tier = "standard"
        elif '<Tab title="Priority' in line:
            current_tier = "priority"
        if not line.strip().startswith("|") or "**MiniMax-" not in line:
            continue
        cells = [clean_markdown_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        model_match = re.search(r"(MiniMax-[A-Za-z0-9.-]+)", cells[0])
        if not model_match:
            continue
        condition = cells[0].replace(model_match.group(1), "").strip() or None
        cache_write = last_money(cells[4]) if len(cells) > 4 else None
        prices.append(
            ModelPrice(
                provider=PROVIDER,
                model=model_match.group(1).lower(),
                input_per_1m=last_money(cells[1]),
                output_per_1m=last_money(cells[2]),
                cached_input_per_1m=last_money(cells[3]),
                cache_write_5m_per_1m=cache_write,
                source_url=SOURCE_URL,
                source_type="markdown",
                fetched_at=fetched_at,
                billing_tier=current_tier if "m3" in model_match.group(1).lower() else "standard",
                price_condition=condition,
            )
        )
    if not prices:
        for row in markdown_table_rows(text):
            if row and row[0].lower().startswith("minimax"):
                pass
    return prices
