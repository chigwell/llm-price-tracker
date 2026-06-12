"""Snapshot JSON persistence."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from llm_price_tracker.models import ModelPrice

_SNAPSHOT_ADAPTER = TypeAdapter(list[ModelPrice])


def prices_to_jsonable(prices: list[ModelPrice]) -> list[dict[str, object]]:
    return _SNAPSHOT_ADAPTER.dump_python(prices, mode="json")


def save_snapshot(prices: list[ModelPrice], path: str) -> None:
    """Save prices as JSON, preserving Decimal values as strings."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(prices_to_jsonable(prices), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_snapshot(path: str) -> list[ModelPrice]:
    """Load a JSON snapshot into typed models."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return _SNAPSHOT_ADAPTER.validate_python(data)
