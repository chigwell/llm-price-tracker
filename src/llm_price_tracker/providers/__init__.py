"""Provider registry."""

from __future__ import annotations

from collections.abc import Callable

from llm_price_tracker.models import ModelPrice

ProviderFetcher = Callable[[], list[ModelPrice]]

PROVIDERS = ("openai", "anthropic", "google_gemini", "kimi", "minimax", "qwen")


def list_providers() -> list[str]:
    return list(PROVIDERS)


def get_provider_fetcher(provider: str) -> ProviderFetcher:
    normalised = provider.strip().lower().replace("-", "_")
    if normalised == "google":
        normalised = "google_gemini"
    if normalised not in PROVIDERS:
        allowed = ", ".join(PROVIDERS)
        raise ValueError(f"unknown provider {provider!r}; expected one of: {allowed}")

    if normalised == "openai":
        from llm_price_tracker.providers.openai import fetch_prices
    elif normalised == "anthropic":
        from llm_price_tracker.providers.anthropic import fetch_prices
    elif normalised == "google_gemini":
        from llm_price_tracker.providers.google_gemini import fetch_prices
    elif normalised == "kimi":
        from llm_price_tracker.providers.kimi import fetch_prices
    elif normalised == "minimax":
        from llm_price_tracker.providers.minimax import fetch_prices
    else:
        from llm_price_tracker.providers.qwen import fetch_prices

    return fetch_prices
