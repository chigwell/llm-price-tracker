"""OpenAI pricing adapter."""

from __future__ import annotations

import html as html_lib
import re
from decimal import Decimal

from llm_price_tracker.exceptions import PricingParseError
from llm_price_tracker.models import ModelPrice
from llm_price_tracker.providers.common import slug_model_name
from llm_price_tracker.utils.html import html_table_rows, page_text, require_markers
from llm_price_tracker.utils.http import fetch_html
from llm_price_tracker.utils.money import parse_money
from llm_price_tracker.utils.time import utc_now_iso
from llm_price_tracker.validation import validate_prices

SOURCE_URL = "https://developers.openai.com/api/docs/pricing"
PROVIDER = "openai"
DEFAULT_REQUIRED_MODELS = {
    "gpt-5.3-codex",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gpt-image-2",
}


def fetch_prices(
    html: str | None = None,
    *,
    required_models: set[str] | None = None,
) -> list[ModelPrice]:
    source = html if html is not None else fetch_html(SOURCE_URL, provider=PROVIDER)
    require_markers(page_text(source), ["OpenAI", "Price", "Input", "Output"], provider=PROVIDER)
    fetched_at = utc_now_iso()
    prices = (
        _parse_embedded_pricing(source, fetched_at)
        or _parse_tables(source, fetched_at)
        or _parse_cards(source, fetched_at)
    )
    required = (
        DEFAULT_REQUIRED_MODELS
        if required_models is None and html is None
        else required_models or set()
    )
    return validate_prices(prices, provider=PROVIDER, required_models=required)


def _parse_embedded_pricing(html: str, fetched_at: str) -> list[ModelPrice]:
    text = html_lib.unescape(html)
    group_re = re.compile(r'"model":\[0,"(?P<group>[^"]+)"\],"rows":\[1,\[')
    row_re = re.compile(
        r'\[\[0,"(?P<name>[^"]+)"\],'
        r"\[0,(?P<input>null|-?[0-9]+(?:\.[0-9]+)?|\"[^\"]*\")\],"
        r"\[0,(?P<cached>null|-?[0-9]+(?:\.[0-9]+)?|\"[^\"]*\")\],"
        r"\[0,(?P<output>null|-?[0-9]+(?:\.[0-9]+)?|\"[^\"]*\")\]\]"
    )
    groups = list(group_re.finditer(text))
    parsed: list[ModelPrice] = []
    for row_match in row_re.finditer(text):
        row_name = row_match.group("name")
        model, modality, condition = _row_identity("", row_name)
        if not _looks_like_openai_model(model):
            continue
        price = _price_from_row_match(row_match, model, modality, condition, fetched_at)
        if price is not None:
            parsed.append(price)

    for index, group_match in enumerate(groups):
        group = group_match.group("group")
        start = group_match.end()
        end = groups[index + 1].start() if index + 1 < len(groups) else len(text)
        segment = text[start:end]
        for row_match in row_re.finditer(segment):
            row_name = row_match.group("name")
            model, modality, condition = _row_identity(group, row_name)
            if not _looks_like_openai_model(model):
                continue
            price = _price_from_row_match(row_match, model, modality, condition, fetched_at)
            if price is not None:
                parsed.append(price)
    return _dedupe_prices(parsed)


def _price_from_row_match(
    row_match: re.Match[str],
    model: str,
    modality: str | None,
    condition: str | None,
    fetched_at: str,
) -> ModelPrice | None:
    input_price = _embedded_value(row_match.group("input"))
    cached_price = _embedded_value(row_match.group("cached"))
    output_price = _embedded_value(row_match.group("output"))
    if input_price is None and cached_price is None and output_price is None:
        return None
    return ModelPrice(
        provider=PROVIDER,
        model=model,
        input_per_1m=input_price,
        cached_input_per_1m=cached_price,
        output_per_1m=output_price,
        source_url=SOURCE_URL,
        source_type="html",
        fetched_at=fetched_at,
        modality=modality,
        price_condition=condition,
    )


def _row_identity(group: str, row_name: str) -> tuple[str, str | None, str | None]:
    if _looks_like_openai_model(group) and row_name.lower() in {"image", "text", "audio"}:
        return group, row_name.lower(), None
    condition_match = re.search(r"\((?P<condition>[^)]+)\)", row_name)
    condition = condition_match.group("condition") if condition_match else None
    model_name = re.sub(r"\s*\([^)]*\)", "", row_name).strip()
    return slug_model_name(model_name), None, condition


def _embedded_value(value: str) -> Decimal | None:
    if value in {"null", '""', '"-"'}:
        return None
    if value == '"Free"':
        return Decimal("0")
    if value.startswith('"') and value.endswith('"'):
        return parse_money(value.strip('"'))
    return Decimal(value)


def _looks_like_openai_model(model: str) -> bool:
    return model.startswith(
        (
            "gpt-",
            "o1",
            "o3",
            "o4",
            "codex-",
            "chatgpt-",
            "computer-use",
            "text-embedding",
            "omni-moderation",
        )
    )


def _dedupe_prices(prices: list[ModelPrice]) -> list[ModelPrice]:
    deduped: dict[tuple[str, str | None, str | None], ModelPrice] = {}
    for price in prices:
        deduped.setdefault((price.model, price.modality, price.price_condition), price)
    return list(deduped.values())


def _parse_tables(html: str, fetched_at: str) -> list[ModelPrice]:
    rows = html_table_rows(html)
    parsed: list[ModelPrice] = []
    for row in rows:
        if len(row) < 4 or row[0].lower() in {"model", "models"}:
            continue
        headerish = " ".join(row).lower()
        if "$" not in headerish:
            continue
        try:
            parsed.append(
                ModelPrice(
                    provider=PROVIDER,
                    model=slug_model_name(row[0]),
                    input_per_1m=parse_money(row[1]),
                    cached_input_per_1m=parse_money(row[2]),
                    output_per_1m=parse_money(row[3]),
                    source_url=SOURCE_URL,
                    source_type="html",
                    fetched_at=fetched_at,
                )
            )
        except Exception:
            continue
    return parsed


def _parse_cards(html: str, fetched_at: str) -> list[ModelPrice]:
    parsed: list[ModelPrice] = []
    card_re = re.compile(
        r"<h2[^>]*>(?P<model>[^<]+)</h2>(?P<body>.*?)(?=<h2[^>]*>|</section>|</main>)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in card_re.finditer(html):
        model = slug_model_name(match.group("model"))
        body = match.group("body")
        input_price = _price_after("Input", body)
        output_price = _price_after("Output", body)
        cached_price = _price_after("Cached input", body)
        if input_price is None and output_price is None and cached_price is None:
            continue
        if not model.startswith(("gpt-", "o", "codex-", "computer-use")):
            continue
        parsed.append(
            ModelPrice(
                provider=PROVIDER,
                model=model,
                input_per_1m=input_price,
                cached_input_per_1m=cached_price,
                output_per_1m=output_price,
                source_url=SOURCE_URL,
                source_type="html",
                fetched_at=fetched_at,
            )
        )
    if not parsed:
        raise PricingParseError("openai: no model pricing cards found")
    return parsed


def _price_after(label: str, body: str):
    money = r"(\$[0-9][0-9,]*(?:\.[0-9]+)?)"
    pattern = rf"{re.escape(label)}:\s*(?:<br\s*/?>|\s|&nbsp;)*\s*{money}\s*/\s*1M tokens"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    return parse_money(match.group(1))
