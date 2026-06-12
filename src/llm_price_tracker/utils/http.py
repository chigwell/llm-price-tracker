"""HTTP client helpers."""

from __future__ import annotations

import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import httpx

from llm_price_tracker.exceptions import PricingFetchError

USER_AGENT = "llm-price-tracker/0.1 (+https://github.com/chigwell/llm-price-tracker)"


def fetch_html(url: str, *, provider: str, timeout: float = 20.0, retries: int = 2) -> str:
    """Fetch a provider pricing page with bounded retries."""

    headers = {"User-Agent": USER_AGENT}
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                max_redirects=5,
            ) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.text
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.25 * (attempt + 1))
    try:
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", "ignore")
    except (HTTPError, URLError, TimeoutError) as exc:
        last_error = exc
    raise PricingFetchError(f"{provider}: failed to fetch {url}: {last_error}") from last_error
