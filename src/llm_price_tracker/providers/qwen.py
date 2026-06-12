"""Alibaba Cloud Model Studio / Qwen pricing adapter."""

from __future__ import annotations

import re

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.providers.common import slug_model_name
from llm_price_tracker.utils.html import html_table_rows, page_text, require_markers
from llm_price_tracker.utils.http import fetch_html
from llm_price_tracker.utils.money import parse_money
from llm_price_tracker.utils.time import utc_now_iso
from llm_price_tracker.validation import validate_prices

SOURCE_URL = "https://www.alibabacloud.com/help/en/model-studio/models"
PROVIDER = "qwen"
DEFAULT_REQUIRED_MODELS = {"qwen-plus-2025-07-14"}


def fetch_prices(
    html: str | None = None,
    *,
    required_models: set[str] | None = None,
) -> list[ModelPrice]:
    source = html if html is not None else fetch_html(SOURCE_URL, provider=PROVIDER)
    require_markers(page_text(source), ["qwen", "Input cost", "Output cost"], provider=PROVIDER)
    fetched_at = utc_now_iso()
    prices = _parse_tables(source, fetched_at)
    required = (
        DEFAULT_REQUIRED_MODELS
        if required_models is None and html is None
        else required_models or set()
    )
    return validate_prices(prices, provider=PROVIDER, required_models=required)


def _parse_tables(html: str, fetched_at: str) -> list[ModelPrice]:
    rows = html_table_rows(html)
    prices: list[ModelPrice] = []
    for row in rows:
        if len(row) < 3:
            continue
        model_cell = row[0]
        model_match = re.search(r"\b(qwen[a-z0-9_.-]*)\b", model_cell, re.IGNORECASE)
        if not model_match:
            continue
        money_cells = [cell for cell in row if "$" in cell]
        if len(money_cells) < 2:
            continue
        model = slug_model_name(model_match.group(1))
        prices.append(
            ModelPrice(
                provider=PROVIDER,
                model=model,
                input_per_1m=parse_money(money_cells[-2]),
                output_per_1m=parse_money(money_cells[-1]),
                source_url=SOURCE_URL,
                source_type="html",
                fetched_at=fetched_at,
                notes="Parsed from Alibaba Cloud Model Studio model list.",
            )
        )
    deduped: dict[str, ModelPrice] = {}
    for price in prices:
        deduped.setdefault(price.model, price)
    return list(deduped.values())
