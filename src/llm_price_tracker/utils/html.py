"""HTML extraction helpers."""

from __future__ import annotations

import html as html_lib
import re
from collections.abc import Iterable

from bs4 import BeautifulSoup

from llm_price_tracker.exceptions import PricingParseError


def normalise_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def page_text(html: str) -> str:
    """Return visible and embedded text from modern docs/pricing pages."""

    soup = BeautifulSoup(html, "lxml")
    visible = soup.get_text("\n")
    embedded_parts = [script.get_text("\n") for script in soup.find_all("script")]
    embedded = "\n".join(embedded_parts)
    combined = "\n".join([visible, embedded, html])
    combined = html_lib.unescape(combined)
    combined = combined.replace("\\n", "\n").replace('\\"', '"').replace("\\u0026", "&")
    combined = re.sub(r"\r\n?", "\n", combined)
    return combined


def text_lines(html: str) -> list[str]:
    """Extract non-empty normalised text lines."""

    text = page_text(html)
    return [normalise_space(line) for line in text.split("\n") if normalise_space(line)]


def require_markers(text: str, markers: Iterable[str], *, provider: str) -> None:
    missing = [marker for marker in markers if marker.lower() not in text.lower()]
    if missing:
        joined = ", ".join(missing)
        raise PricingParseError(f"{provider}: pricing page is missing expected marker(s): {joined}")


def html_table_rows(html: str) -> list[list[str]]:
    """Extract rows from literal HTML tables."""

    soup = BeautifulSoup(html, "lxml")
    rows: list[list[str]] = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue
        rows.append([normalise_space(cell.get_text(" ")) for cell in cells])
    return rows
