"""Moonshot AI / Kimi pricing adapter."""

from __future__ import annotations

import re

from llm_price_tracker.models import ModelPrice
from llm_price_tracker.utils.http import fetch_html
from llm_price_tracker.utils.money import parse_money
from llm_price_tracker.utils.time import utc_now_iso
from llm_price_tracker.validation import validate_prices

PROVIDER = "kimi"
INDEX_URL = "https://platform.kimi.ai/docs/pricing/chat.md"
MODEL_URLS = (
    "https://platform.kimi.ai/docs/pricing/chat-k27-code.md",
    "https://platform.kimi.ai/docs/pricing/chat-k26.md",
    "https://platform.kimi.ai/docs/pricing/chat-k25.md",
    "https://platform.kimi.ai/docs/pricing/chat-v1.md",
)
DEFAULT_REQUIRED_MODELS = {"kimi-k2.6"}


def fetch_prices(
    html: str | None = None,
    *,
    required_models: set[str] | None = None,
) -> list[ModelPrice]:
    fetched_at = utc_now_iso()
    documents: list[tuple[str, str]]
    if html is not None:
        documents = [(INDEX_URL, html)]
    else:
        documents = [(url, fetch_html(url, provider=PROVIDER)) for url in MODEL_URLS]
    prices: list[ModelPrice] = []
    for source_url, text in documents:
        prices.extend(_parse_doc(text, source_url, fetched_at))
    required = (
        DEFAULT_REQUIRED_MODELS
        if required_models is None and html is None
        else required_models or set()
    )
    return validate_prices(prices, provider=PROVIDER, required_models=required)


def _parse_doc(text: str, source_url: str, fetched_at: str) -> list[ModelPrice]:
    prices: list[ModelPrice] = []
    row_re = re.compile(
        r'\["(?P<model>[^"]+)",\s*"1M tokens",\s*<>\{"\$"}(?P<cached>[0-9.]+)</>,\s*'
        r'<>\{"\$"}(?P<input>[0-9.]+)</>,\s*<>\{"\$"}(?P<output>[0-9.]+)</>',
        re.DOTALL,
    )
    for match in row_re.finditer(text):
        prices.append(
            ModelPrice(
                provider=PROVIDER,
                model=match.group("model"),
                input_per_1m=parse_money(match.group("input")),
                cached_input_per_1m=parse_money(match.group("cached")),
                output_per_1m=parse_money(match.group("output")),
                source_url=source_url,
                source_type="markdown",
                fetched_at=fetched_at,
                modality="text/image/video" if "k2" in match.group("model") else "text",
            )
        )
    return prices
