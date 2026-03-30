"""DeFiLlama adapter for TVL and protocol data.

Public API, no key required.
Docs: https://defillama.com/docs/api
"""

from __future__ import annotations

from typing import Any

import httpx

from contagion_radar.core.types import DataStatus

from .base import AdapterError, DataAdapter


class DeFiLlamaAdapter(DataAdapter):
    source_name = "defillama"

    BASE_URL = "https://api.llama.fi"

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Fetch TVL and protocol info for a protocol slug (e.g., 'aave')."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self.BASE_URL}/protocol/{entity}")
                resp.raise_for_status()
                raw = resp.json()

            data = {
                "tvl": raw.get("tvl"),
                "chain": raw.get("chain"),
                "chains": raw.get("chains", []),
                "name": raw.get("name"),
                "symbol": raw.get("symbol"),
                "category": raw.get("category"),
                "change_1h": raw.get("change_1h"),
                "change_1d": raw.get("change_1d"),
                "change_7d": raw.get("change_7d"),
                "mcap": raw.get("mcap"),
            }

            completeness = sum(1 for v in [data["tvl"], data["chain"]] if v is not None) / 2
            confidence = self._make_confidence(
                status=DataStatus.FRESH,
                completeness=completeness,
            )
            return data, confidence

        except httpx.HTTPStatusError as e:
            raise AdapterError(self.source_name, f"HTTP {e.response.status_code}: {entity}") from e
        except httpx.RequestError as e:
            raise AdapterError(self.source_name, f"Request failed: {e}") from e

    async def fetch_stablecoins(self) -> tuple[list[dict], Any]:
        """Fetch all stablecoin data (peg deviations, mcap)."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"https://stablecoins.llama.fi/stablecoins?includePrices=true")
                resp.raise_for_status()
                raw = resp.json()

            coins = []
            for item in raw.get("peggedAssets", []):
                coins.append({
                    "name": item.get("name"),
                    "symbol": item.get("symbol"),
                    "peg_type": item.get("pegType"),
                    "price": item.get("price"),
                    "circulating": item.get("circulating", {}).get("peggedUSD"),
                })
            confidence = self._make_confidence(status=DataStatus.FRESH)
            return coins, confidence

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise AdapterError(self.source_name, f"Stablecoins fetch failed: {e}") from e
