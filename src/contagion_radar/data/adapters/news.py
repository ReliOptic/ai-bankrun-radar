"""News adapter for narrative signals.

Uses NewsAPI.org for headline and article searches.
Returns text documents for corpus.db + aggregated metrics for metrics.db.
"""

from __future__ import annotations

from typing import Any

import httpx

from contagion_radar.core.types import DataStatus

from .base import AdapterError, DataAdapter


class NewsAdapter(DataAdapter):
    source_name = "news"

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str = "", timeout: float = 30.0):
        self._api_key = api_key
        self._timeout = timeout

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Fetch news articles mentioning an entity.

        Returns documents (for corpus.db) and article counts (for metrics.db).
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/everything",
                    params={
                        "q": entity,
                        "sortBy": "publishedAt",
                        "pageSize": 25,
                        "language": "en",
                    },
                    headers={"X-Api-Key": self._api_key},
                )
                resp.raise_for_status()
                raw = resp.json()

            articles = raw.get("articles", [])
            documents = []
            for article in articles:
                title = article.get("title", "")
                desc = article.get("description", "")
                documents.append({
                    "text": f"{title}. {desc}".strip(),
                    "title": title,
                    "source": f"news:{article.get('source', {}).get('name', 'unknown')}",
                    "timestamp": article.get("publishedAt"),
                    "url": article.get("url"),
                })

            data = {
                "documents": documents,
                "article_count": len(documents),
                "total_results": raw.get("totalResults", 0),
                "title": documents[0]["title"] if documents else "",
            }

            status = DataStatus.FRESH if documents else DataStatus.DEGRADED
            confidence = self._make_confidence(
                status=status,
                completeness=1.0 if documents else 0.5,
            )
            return data, confidence

        except httpx.HTTPStatusError as e:
            raise AdapterError(self.source_name, f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise AdapterError(self.source_name, f"Request failed: {e}") from e
