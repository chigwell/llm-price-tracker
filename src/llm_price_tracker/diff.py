"""Snapshot diffing."""

from __future__ import annotations

from llm_price_tracker.models import PRICE_FIELDS, ModelIdentity, ModelPrice, PriceChange, PriceDiff


def _identity(price: ModelPrice) -> tuple[str, str, str | None, str | None, str | None]:
    return (
        price.provider,
        price.model,
        price.modality,
        price.billing_tier,
        price.price_condition,
    )


def _identity_model(key: tuple[str, str, str | None, str | None, str | None]) -> ModelIdentity:
    provider, model, modality, billing_tier, price_condition = key
    return ModelIdentity(
        provider=provider,
        model=model,
        modality=modality,
        billing_tier=billing_tier,
        price_condition=price_condition,
    )


def diff_snapshots(old: list[ModelPrice], new: list[ModelPrice]) -> PriceDiff:
    """Detect provider, model, and price changes between two snapshots."""

    old_by_key = {_identity(price): price for price in old}
    new_by_key = {_identity(price): price for price in new}

    old_providers = {price.provider for price in old}
    new_providers = {price.provider for price in new}

    removed_keys = sorted(set(old_by_key) - set(new_by_key))
    new_keys = sorted(set(new_by_key) - set(old_by_key))

    changed: list[PriceChange] = []
    for key in sorted(set(old_by_key) & set(new_by_key)):
        old_price = old_by_key[key]
        new_price = new_by_key[key]
        for field in PRICE_FIELDS:
            old_value = getattr(old_price, field)
            new_value = getattr(new_price, field)
            if old_value != new_value:
                provider, model, modality, billing_tier, price_condition = key
                changed.append(
                    PriceChange(
                        provider=provider,
                        model=model,
                        modality=modality,
                        billing_tier=billing_tier,
                        price_condition=price_condition,
                        field=field,
                        old=old_value,
                        new=new_value,
                    )
                )

    return PriceDiff(
        new_providers=sorted(new_providers - old_providers),
        removed_providers=sorted(old_providers - new_providers),
        new_models=[_identity_model(key) for key in new_keys],
        removed_models=[_identity_model(key) for key in removed_keys],
        changed_prices=changed,
    )
