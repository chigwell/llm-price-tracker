"""Public fetching API."""

from __future__ import annotations

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.providers import get_provider_fetcher, list_providers

_LAST_ERRORS: list[str] = []


def fetch_provider_prices(provider: str) -> list[ModelPrice]:
    """Fetch official prices for one provider."""

    return get_provider_fetcher(provider)()


def fetch_all_prices(*, ignore_errors: bool = False) -> list[ModelPrice]:
    """Fetch official prices for all configured providers."""

    global _LAST_ERRORS
    _LAST_ERRORS = []
    prices: list[ModelPrice] = []
    for provider in list_providers():
        try:
            prices.extend(fetch_provider_prices(provider))
        except Exception as exc:
            if not ignore_errors:
                raise
            _LAST_ERRORS.append(f"{provider}: {exc}")
    return prices


def get_last_fetch_errors() -> list[str]:
    """Return provider errors from the last ignore-errors fetch."""

    return list(_LAST_ERRORS)
