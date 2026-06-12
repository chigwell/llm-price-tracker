"""Shared provider parsing helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.utils.money import parse_money


def slug_model_name(value: str) -> str:
    name = re.sub(r"\([^)]*\)", "", value)
    name = re.sub(r"\s+", "-", name.strip().lower())
    return name.strip("-")


def markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [clean_markdown_cell(cell) for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def clean_markdown_cell(value: str) -> str:
    cleaned = value.strip()
    cleaned = cleaned.replace("<br />", " ").replace("<br/>", " ").replace("<br>", " ")
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.replace("**", "").replace("\\$", "$")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def last_money(value: str) -> Decimal | None:
    matches = re.findall(
        r"(?:US)?\$\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|(?:US)?\$\s*[0-9]*\.[0-9]+",
        value.replace("\\$", "$"),
    )
    if not matches:
        return parse_money(value)
    return parse_money(matches[-1])


def require_any_model(prices: Iterable[ModelPrice], provider: str) -> list[ModelPrice]:
    rows = list(prices)
    if not rows:
        from llm_price_tracker.exceptions import PricingParseError

        raise PricingParseError(f"{provider}: no pricing rows parsed")
    return rows
