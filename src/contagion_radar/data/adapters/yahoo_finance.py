"""Yahoo Finance adapter for market data.

Uses the public Yahoo Finance v8 API for prices and volumes.
No API key required (rate limited).
"""

from __future__ import annotations

from typing import Any

import httpx

from contagion_radar.core.types import DataStatus

from .base import AdapterError, DataAdapter


class YahooFinanceAdapter(DataAdapter):
    source_name = "yahoo_finance"

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Fetch price/volume data for a ticker symbol.

        Args:
            entity: ticker symbol (e.g., "BTC-USD", "^VIX", "SIVB")
            kwargs:
                range: "1d", "5d", "1mo" (default "1d")
                interval: "1m", "5m", "1h", "1d" (default "5m")
        """
        range_ = kwargs.get("range", "1d")
        interval = kwargs.get("interval", "5m")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/{entity}",
                    params={"range": range_, "interval": interval},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                raw = resp.json()

            result = raw.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            indicators = result.get("indicators", {})
            quotes = indicators.get("quote", [{}])[0]

            closes = quotes.get("close", [])
            volumes = quotes.get("volume", [])

            latest_price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose")

            data = {
                "price": latest_price,
                "previous_close": prev_close,
                "volume": volumes[-1] if volumes else None,
                "currency": meta.get("currency"),
                "exchange": meta.get("exchangeName"),
                "price_series": closes[-60:] if closes else [],
                "volume_series": volumes[-60:] if volumes else [],
            }

            completeness = sum(1 for v in [data["price"], data["volume"]] if v is not None) / 2
            confidence = self._make_confidence(
                status=DataStatus.FRESH,
                completeness=completeness,
            )
            return data, confidence

        except httpx.HTTPStatusError as e:
            raise AdapterError(self.source_name, f"HTTP {e.response.status_code}: {entity}") from e
        except (httpx.RequestError, KeyError, IndexError) as e:
            raise AdapterError(self.source_name, f"Failed for {entity}: {e}") from e
