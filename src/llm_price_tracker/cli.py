"""Command line interface."""

from __future__ import annotations

from decimal import Decimal

import typer
from rich.console import Console

from llm_price_tracker.diff import diff_snapshots
from llm_price_tracker.exceptions import PricingError
from llm_price_tracker.fetch import fetch_all_prices, fetch_provider_prices, get_last_fetch_errors
from llm_price_tracker.models import ModelIdentity, PriceChange, PriceDiff
from llm_price_tracker.providers import list_providers as provider_names
from llm_price_tracker.snapshot import load_snapshot, save_snapshot

app = typer.Typer(help="Fetch and diff official LLM API token pricing.")
console = Console()
err_console = Console(stderr=True)


@app.command("list-providers")
def list_providers() -> None:
    """Print supported provider names."""

    for provider in provider_names():
        console.print(provider)


@app.command()
def fetch(
    provider: str = typer.Option("all", "--provider", help="Provider name or 'all'."),
    output: str = typer.Option(..., "--output", "-o", help="Output JSON snapshot path."),
    ignore_errors: bool = typer.Option(
        False,
        "--ignore-errors",
        help="Continue when fetching all providers and one provider fails.",
    ),
) -> None:
    """Fetch pricing and write a JSON snapshot."""

    try:
        if provider.strip().lower() == "all":
            prices = fetch_all_prices(ignore_errors=ignore_errors)
            errors = get_last_fetch_errors()
        else:
            prices = fetch_provider_prices(provider)
            errors = []
        save_snapshot(prices, output)
    except (PricingError, ValueError) as exc:
        err_console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"Wrote {len(prices)} price rows to {output}")
    for error in errors:
        err_console.print(f"[yellow]warning:[/yellow] {error}")


@app.command()
def diff(
    old: str = typer.Option(..., "--old", help="Old JSON snapshot path."),
    new: str = typer.Option(..., "--new", help="New JSON snapshot path."),
    fail_on_change: bool = typer.Option(
        False,
        "--fail-on-change",
        help="Exit non-zero if any provider, model, or price changed.",
    ),
) -> None:
    """Diff two JSON snapshots."""

    try:
        result = diff_snapshots(load_snapshot(old), load_snapshot(new))
    except Exception as exc:
        err_console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(1) from exc

    _print_diff(result)
    if fail_on_change and result.has_changes:
        raise typer.Exit(2)


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "null"
    return format(value, "f")


def _format_identity(identity: ModelIdentity) -> str:
    parts = [identity.provider, identity.model]
    if identity.modality:
        parts.append(f"modality={identity.modality}")
    if identity.billing_tier:
        parts.append(f"tier={identity.billing_tier}")
    if identity.price_condition:
        parts.append(identity.price_condition)
    return " / ".join(parts)


def _format_change(change: PriceChange) -> str:
    identity = _format_identity(
        ModelIdentity(
            provider=change.provider,
            model=change.model,
            modality=change.modality,
            billing_tier=change.billing_tier,
            price_condition=change.price_condition,
        )
    )
    return (
        f"- {identity}: {change.field}: "
        f"{_format_decimal(change.old)} -> {_format_decimal(change.new)}"
    )


def _print_diff(result: PriceDiff) -> None:
    if not result.has_changes:
        console.print("No pricing changes.")
        return
    if result.changed_prices:
        console.print("Changed prices:")
        for change in result.changed_prices:
            console.print(_format_change(change))
    if result.new_providers:
        console.print("New providers:")
        for provider in result.new_providers:
            console.print(f"- {provider}")
    if result.removed_providers:
        console.print("Removed providers:")
        for provider in result.removed_providers:
            console.print(f"- {provider}")
    if result.new_models:
        console.print("New models:")
        for model in result.new_models:
            console.print(f"- {_format_identity(model)}")
    if result.removed_models:
        console.print("Removed models:")
        for model in result.removed_models:
            console.print(f"- {_format_identity(model)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
