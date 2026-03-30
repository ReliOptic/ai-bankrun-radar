"""Social media adapter for narrative signals.

Fetches from Reddit (public JSON) and Twitter (bearer token).
Returns text documents for corpus.db + aggregated metrics for metrics.db.
"""

from __future__ import annotations

from typing import Any

import httpx

from contagion_radar.core.types import DataStatus

from .base import AdapterError, DataAdapter


class SocialAdapter(DataAdapter):
    source_name = "social"

    def __init__(
        self,
        twitter_bearer: str = "",
        reddit_client_id: str = "",
        reddit_client_secret: str = "",
        timeout: float = 30.0,
    ):
        self._twitter_bearer = twitter_bearer
        self._reddit_client_id = reddit_client_id
        self._reddit_client_secret = reddit_client_secret
        self._timeout = timeout

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Fetch social mentions for an entity.

        Returns both documents (for corpus.db) and aggregated counts (for metrics.db).
        """
        documents: list[dict] = []
        mention_count = 0

        # Reddit (public JSON, no auth needed for read)
        try:
            reddit_docs = await self._fetch_reddit(entity)
            documents.extend(reddit_docs)
            mention_count += len(reddit_docs)
        except AdapterError:
            pass

        data = {
            "documents": documents,
            "mention_count": mention_count,
            "text": f"Social mentions for {entity}",
        }

        status = DataStatus.FRESH if mention_count > 0 else DataStatus.DEGRADED
        confidence = self._make_confidence(
            status=status,
            completeness=1.0 if mention_count > 0 else 0.5,
        )
        return data, confidence

    async def _fetch_reddit(self, entity: str) -> list[dict]:
        """Search Reddit for mentions of an entity."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"https://www.reddit.com/search.json",
                    params={
                        "q": entity,
                        "sort": "new",
                        "limit": 25,
                        "t": "day",
                    },
                    headers={"User-Agent": "ContagionRadar/0.1"},
                )
                resp.raise_for_status()
                raw = resp.json()

            documents = []
            for child in raw.get("data", {}).get("children", []):
                post = child.get("data", {})
                documents.append({
                    "text": f"{post.get('title', '')} {post.get('selftext', '')}".strip(),
                    "source": "reddit",
                    "timestamp": post.get("created_utc"),
                    "subreddit": post.get("subreddit"),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                })
            return documents

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise AdapterError(self.source_name, f"Reddit fetch failed: {e}") from e
