"""Money parsing helpers."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from llm_price_tracker.exceptions import PricingParseError

_MONEY_RE = re.compile(r"(?:US)?\$?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]*\.[0-9]+)")


def parse_money(value: str, *, allow_free: bool = False) -> Decimal | None:
    """Parse a USD-like money value into a Decimal."""

    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"n/a", "na", "not available", "-"}:
        return None
    if "free" in cleaned.lower():
        if allow_free:
            return Decimal("0")
        return None
    match = _MONEY_RE.search(cleaned.replace("~~", ""))
    if not match:
        raise PricingParseError(f"could not parse money value: {value!r}")
    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation as exc:
        raise PricingParseError(f"invalid money value: {value!r}") from exc


def decimal_to_string(value: Decimal) -> str:
    """Format Decimal without scientific notation."""

    return format(value, "f")
