"""Etherscan adapter for on-chain data.

Fetches gas prices, token transfers, and contract interactions.
Requires API key (free tier: 5 calls/sec).
"""

from __future__ import annotations

from typing import Any

import httpx

from contagion_radar.core.types import DataStatus

from .base import AdapterError, DataAdapter


class EtherscanAdapter(DataAdapter):
    source_name = "etherscan"

    BASE_URL = "https://api.etherscan.io/api"

    def __init__(self, api_key: str = "", timeout: float = 30.0):
        self._api_key = api_key
        self._timeout = timeout

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Fetch on-chain data for an address or token symbol.

        kwargs:
            metric: "gas" | "balance" | "transfers" (default: "gas")
        """
        metric = kwargs.get("metric", "gas")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                if metric == "gas":
                    return await self._fetch_gas(client)
                elif metric == "balance":
                    return await self._fetch_balance(client, entity)
                elif metric == "transfers":
                    return await self._fetch_transfers(client, entity)
                else:
                    raise AdapterError(self.source_name, f"Unknown metric: {metric}")
        except httpx.RequestError as e:
            raise AdapterError(self.source_name, f"Request failed: {e}") from e

    async def _fetch_gas(self, client: httpx.AsyncClient) -> tuple[dict, Any]:
        resp = await client.get(self.BASE_URL, params={
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": self._api_key,
        })
        resp.raise_for_status()
        raw = resp.json()

        result = raw.get("result", {})
        data = {
            "gas_low": float(result.get("SafeGasPrice", 0)),
            "gas_average": float(result.get("ProposeGasPrice", 0)),
            "gas_high": float(result.get("FastGasPrice", 0)),
            "block_number": int(result.get("LastBlock", 0)),
        }
        completeness = 1.0 if data["block_number"] > 0 else 0.5
        return data, self._make_confidence(status=DataStatus.FRESH, completeness=completeness)

    async def _fetch_balance(self, client: httpx.AsyncClient, address: str) -> tuple[dict, Any]:
        resp = await client.get(self.BASE_URL, params={
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self._api_key,
        })
        resp.raise_for_status()
        raw = resp.json()

        balance_wei = int(raw.get("result", 0))
        data = {
            "balance_wei": balance_wei,
            "balance_eth": balance_wei / 1e18,
            "block_number": 0,
        }
        return data, self._make_confidence(status=DataStatus.FRESH)

    async def _fetch_transfers(self, client: httpx.AsyncClient, address: str) -> tuple[dict, Any]:
        resp = await client.get(self.BASE_URL, params={
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": 50,
            "sort": "desc",
            "apikey": self._api_key,
        })
        resp.raise_for_status()
        raw = resp.json()

        transfers = raw.get("result", [])
        if isinstance(transfers, str):
            transfers = []

        data = {
            "transfer_count": len(transfers),
            "transfers": transfers[:10],
            "block_number": int(transfers[0].get("blockNumber", 0)) if transfers else 0,
        }
        return data, self._make_confidence(status=DataStatus.FRESH)
