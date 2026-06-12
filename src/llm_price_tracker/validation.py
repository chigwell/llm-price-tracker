"""Validation helpers shared by providers."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import ValidationError

from llm_price_tracker.exceptions import PricingValidationError
from llm_price_tracker.models import ModelPrice


def validate_prices(
    prices: list[ModelPrice],
    *,
    provider: str,
    required_models: Iterable[str] = (),
) -> list[ModelPrice]:
    if not prices:
        raise PricingValidationError(f"{provider}: no prices parsed")
    for price in prices:
        try:
            ModelPrice.model_validate(price)
        except ValidationError as exc:
            raise PricingValidationError(
                f"{provider}: invalid price row for {price.model}"
            ) from exc
        if price.provider != provider:
            raise PricingValidationError(f"{provider}: parsed row has provider {price.provider!r}")

    present_models = {price.model for price in prices}
    missing = sorted(set(required_models) - present_models)
    if missing:
        joined = ", ".join(missing)
        raise PricingValidationError(f"{provider}: required model(s) missing: {joined}")
    return prices
