from decimal import Decimal

from typer.testing import CliRunner

from llm_price_tracker import cli
from llm_price_tracker.models import ModelPrice


def sample_price(value: str) -> ModelPrice:
    return ModelPrice(
        provider="openai",
        model="gpt-test",
        input_per_1m=Decimal(value),
        source_url="https://example.com/pricing",
        source_type="html",
        fetched_at="2026-06-12T09:00:00Z",
    )


def test_cli_list_providers() -> None:
    result = CliRunner().invoke(cli.app, ["list-providers"])
    assert result.exit_code == 0
    assert "openai" in result.output


def test_cli_fetch_writes_snapshot(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "fetch_provider_prices", lambda provider: [sample_price("1.00")])
    output = tmp_path / "prices.json"

    result = CliRunner().invoke(
        cli.app,
        ["fetch", "--provider", "openai", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert '"input_per_1m": "1.00"' in output.read_text()


def test_cli_diff_fail_on_change(tmp_path) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    cli.save_snapshot([sample_price("1.00")], str(old))
    cli.save_snapshot([sample_price("2.00")], str(new))

    result = CliRunner().invoke(
        cli.app,
        ["diff", "--old", str(old), "--new", str(new), "--fail-on-change"],
    )

    assert result.exit_code == 2
    assert "input_per_1m" in result.output
