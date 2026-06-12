"""Google Gemini pricing adapter."""

from __future__ import annotations

import re
from decimal import Decimal

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.utils.html import page_text, require_markers, text_lines
from llm_price_tracker.utils.http import fetch_html
from llm_price_tracker.utils.money import parse_money
from llm_price_tracker.utils.time import utc_now_iso
from llm_price_tracker.validation import validate_prices

SOURCE_URL = "https://ai.google.dev/gemini-api/docs/pricing"
PROVIDER = "google_gemini"
DEFAULT_REQUIRED_MODELS = {"gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"}


def fetch_prices(
    html: str | None = None,
    *,
    required_models: set[str] | None = None,
) -> list[ModelPrice]:
    source = html if html is not None else fetch_html(SOURCE_URL, provider=PROVIDER)
    require_markers(page_text(source), ["Gemini", "Input price", "Output price"], provider=PROVIDER)
    fetched_at = utc_now_iso()
    prices = _parse_model_blocks(source, fetched_at)
    required = (
        DEFAULT_REQUIRED_MODELS
        if required_models is None and html is None
        else required_models or set()
    )
    return validate_prices(prices, provider=PROVIDER, required_models=required)


def _parse_model_blocks(html: str, fetched_at: str) -> list[ModelPrice]:
    lines = text_lines(html)
    prices: list[ModelPrice] = []
    for index, line in enumerate(lines):
        if not re.fullmatch(r"gemini-[a-z0-9_.-]+", line):
            continue
        model = line
        block = lines[index + 1 : index + 45]
        input_values = _values_between(block, "Input price", "Output price")
        output_values = _values_between(block, "Output price", "Context caching price")
        cached_values = _values_between(block, "Context caching price", "Grounding")
        storage = _storage_price(block)
        count = max(len(input_values), len(output_values), len(cached_values), 1)
        for variant_index in range(count):
            input_price, input_condition = _pick_value(input_values, variant_index)
            output_price, output_condition = _pick_value(output_values, variant_index)
            cached_price, cached_condition = _pick_value(cached_values, variant_index)
            if (
                input_price is None
                and output_price is None
                and cached_price is None
                and storage is None
            ):
                continue
            condition = input_condition or output_condition or cached_condition
            prices.append(
                ModelPrice(
                    provider=PROVIDER,
                    model=model,
                    input_per_1m=input_price,
                    output_per_1m=output_price,
                    cached_input_per_1m=cached_price,
                    cache_storage_per_1m_hour=storage,
                    source_url=SOURCE_URL,
                    source_type="html",
                    fetched_at=fetched_at,
                    modality=_modality_from_condition(condition),
                    billing_tier="paid",
                    price_condition=condition,
                )
            )
    return prices


def _values_between(block: list[str], start: str, stop: str) -> list[tuple[Decimal, str | None]]:
    try:
        start_index = next(i for i, line in enumerate(block) if start.lower() in line.lower())
    except StopIteration:
        return []
    stop_index = len(block)
    for i in range(start_index + 1, len(block)):
        if stop.lower() in block[i].lower():
            stop_index = i
            break
    values: list[tuple[Decimal, str | None]] = []
    for line in block[start_index + 1 : stop_index]:
        if "$" not in line:
            continue
        if "tokens per hour" in line.lower() or "storage price" in line.lower():
            continue
        try:
            price = parse_money(line)
        except Exception:
            continue
        condition = _condition(line)
        if price is not None:
            values.append((price, condition))
    return values


def _storage_price(block: list[str]) -> Decimal | None:
    for line in block:
        if "$" in line and "tokens per hour" in line.lower():
            return parse_money(line)
    return None


def _pick_value(
    values: list[tuple[Decimal, str | None]], index: int
) -> tuple[Decimal | None, str | None]:
    if not values:
        return None, None
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return None, None


def _condition(line: str) -> str | None:
    cleaned = re.sub(r"^\$[0-9][0-9,]*(?:\.[0-9]+)?\s*,?\s*", "", line).strip()
    return cleaned or None


def _modality_from_condition(condition: str | None) -> str | None:
    if not condition:
        return "text"
    lower = condition.lower()
    if "audio" in lower and "text" not in lower:
        return "audio"
    if "image" in lower or "video" in lower or "text" in lower:
        return "text/image/video"
    return "text"
