# llm-price-tracker

[![PyPI version](https://badge.fury.io/py/llm-price-tracker.svg)](https://badge.fury.io/py/llm-price-tracker)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/llm-price-tracker)](https://pepy.tech/project/llm-price-tracker)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

`llm-price-tracker` fetches official published API token prices for major LLM
providers, normalises them into one schema, and supports JSON snapshots and
snapshot diffs.

Prices are collected from official provider pages only. Provider page structures
can change without notice, so review fetched prices before using them for
production billing or customer-facing estimates.

## Supported providers

- OpenAI GPT API models: <https://developers.openai.com/api/docs/pricing>
- Anthropic Claude models: <https://docs.anthropic.com/en/docs/about-claude/pricing>
- Google Gemini models: <https://ai.google.dev/gemini-api/docs/pricing>
- Kimi / Moonshot AI models: <https://platform.kimi.ai/docs/pricing/chat>
- MiniMax models: <https://platform.minimax.io/docs/guides/pricing-paygo>
- Qwen / DashScope models: <https://www.alibabacloud.com/help/en/model-studio/models>

## Installation

```sh
pip install llm-price-tracker
```

For local development:

```sh
python3 -m pip install -e ".[dev]"
```

Python 3.10 or newer is required.

## Python usage

```python
from llm_price_tracker import (
    diff_snapshots,
    fetch_all_prices,
    fetch_provider_prices,
    load_snapshot,
    save_snapshot,
)

prices = fetch_all_prices()
openai_prices = fetch_provider_prices("openai")
save_snapshot(prices, "prices.json")

old = load_snapshot("prices-old.json")
new = load_snapshot("prices.json")
diff = diff_snapshots(old, new)
```

## CLI usage

```sh
llm-price-tracker list-providers
llm-price-tracker fetch --provider openai --output openai-prices.json
llm-price-tracker fetch --provider all --output prices.json
llm-price-tracker diff --old prices-old.json --new prices.json
llm-price-tracker diff --old prices-old.json --new prices.json --fail-on-change
```

The CLI exits non-zero when fetching, parsing, validation, or diff
`--fail-on-change` checks fail. Use `--ignore-errors` with `fetch --provider all`
to write successful providers while reporting skipped provider errors.

## Output schema

Snapshots are JSON arrays of `ModelPrice` objects. Decimal prices are serialized
as strings to avoid floating-point precision loss.

```json
[
  {
    "provider": "openai",
    "model": "gpt-4.1",
    "input_per_1m": "2.00",
    "output_per_1m": "8.00",
    "cached_input_per_1m": "0.50",
    "cache_write_5m_per_1m": null,
    "cache_write_1h_per_1m": null,
    "cache_storage_per_1m_hour": null,
    "currency": "USD",
    "unit": "1M tokens",
    "source_url": "https://developers.openai.com/api/docs/pricing",
    "source_type": "html",
    "fetched_at": "2026-06-12T09:00:00Z",
    "modality": null,
    "billing_tier": null,
    "price_condition": null,
    "notes": null
  }
]
```

Some providers publish tiered or modality-specific prices. Those variants use
optional `modality`, `billing_tier`, and `price_condition` fields instead of
inventing new model names.

Provider adapters include lightweight required-model sanity checks for current
official pages. Those checks are adapter arguments so downstream users can
override them when providers rename, add, or deprecate models.

## Development

```sh
python3 -m pip install -e ".[dev]"
pytest
ruff check .
black --check .
```

Normal tests use saved fixtures and do not call live provider pages. Live tests,
when added, should be opt-in:

```sh
LLM_PRICE_TRACKER_LIVE_TESTS=1 pytest tests/live
```

## Author

Eugene Evstafev <hi@eugene.plus>
