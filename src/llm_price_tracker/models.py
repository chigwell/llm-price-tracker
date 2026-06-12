"""Typed pricing models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

PRICE_FIELDS = (
    "input_per_1m",
    "output_per_1m",
    "cached_input_per_1m",
    "cache_write_5m_per_1m",
    "cache_write_1h_per_1m",
    "cache_storage_per_1m_hour",
)


class ModelPrice(BaseModel):
    """Normalised price row for one provider model or official price variant."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider: str
    model: str

    input_per_1m: Decimal | None = None
    output_per_1m: Decimal | None = None
    cached_input_per_1m: Decimal | None = None

    cache_write_5m_per_1m: Decimal | None = None
    cache_write_1h_per_1m: Decimal | None = None
    cache_storage_per_1m_hour: Decimal | None = None

    currency: str = "USD"
    unit: str = "1M tokens"

    source_url: HttpUrl
    source_type: str
    fetched_at: str

    modality: str | None = None
    billing_tier: str | None = None
    price_condition: str | None = None
    notes: str | None = None

    @field_validator(*PRICE_FIELDS, mode="before")
    @classmethod
    def coerce_decimal(cls, value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_prices(self) -> ModelPrice:
        if not self.provider:
            raise ValueError("provider is required")
        if not self.model:
            raise ValueError("model is required")
        if not any(getattr(self, field) is not None for field in PRICE_FIELDS):
            raise ValueError("at least one price field is required")
        if not self.currency:
            raise ValueError("currency is required")
        if not self.source_url:
            raise ValueError("source_url is required")
        if not self.fetched_at:
            raise ValueError("fetched_at is required")
        return self


class PriceChange(BaseModel):
    """One changed price field between two snapshots."""

    provider: str
    model: str
    field: str
    old: Decimal | None
    new: Decimal | None
    modality: str | None = None
    billing_tier: str | None = None
    price_condition: str | None = None


class ModelIdentity(BaseModel):
    """Stable identity for a provider model or official price variant."""

    provider: str
    model: str
    modality: str | None = None
    billing_tier: str | None = None
    price_condition: str | None = None


class PriceDiff(BaseModel):
    """Snapshot diff result."""

    new_providers: list[str] = Field(default_factory=list)
    removed_providers: list[str] = Field(default_factory=list)
    new_models: list[ModelIdentity] = Field(default_factory=list)
    removed_models: list[ModelIdentity] = Field(default_factory=list)
    changed_prices: list[PriceChange] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.new_providers
            or self.removed_providers
            or self.new_models
            or self.removed_models
            or self.changed_prices
        )
