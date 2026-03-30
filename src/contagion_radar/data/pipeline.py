"""Data pipeline: fetch → quality gate → route to appropriate DB.

Routing rules:
- Numeric adapters (DeFiLlama, Etherscan, Yahoo) → metrics.db
- Text adapters (Social, News) → corpus.db (raw text) + metrics.db (aggregated counts)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from contagion_radar.core.config import QualityGateConfig
from contagion_radar.core.types import DataConfidence, DataStatus
from contagion_radar.data.adapters.base import AdapterError, DataAdapter
from contagion_radar.data.quality_gate import DataQualityGate


# Sources that produce text documents for corpus.db
_TEXT_SOURCES = {"social", "news"}

# Sources that produce numeric metrics for metrics.db
_NUMERIC_SOURCES = {"defillama", "etherscan", "yahoo_finance"}


class DataPipeline:
    """Orchestrates data fetching, quality assessment, and storage routing."""

    def __init__(
        self,
        adapters: dict[str, DataAdapter],
        quality_gate: DataQualityGate,
        data_dir: Path,
    ):
        self._adapters = adapters
        self._gate = quality_gate
        self._data_dir = data_dir

    async def fetch_and_store(
        self,
        entity: str,
        sources: list[str] | None = None,
    ) -> dict[str, DataConfidence]:
        """Fetch from all (or specified) sources and route data to DBs.

        Returns a dict of source → DataConfidence for each source attempted.
        """
        if sources is None:
            sources = list(self._adapters.keys())

        results: dict[str, DataConfidence] = {}
        now = datetime.utcnow()

        for source_name in sources:
            adapter = self._adapters.get(source_name)
            if adapter is None:
                continue

            try:
                data, adapter_confidence = await adapter.fetch(entity)
                confidence = self._gate.assess(source_name, data, now, error=False)
            except AdapterError:
                data = {}
                confidence = self._gate.assess(source_name, data, now, error=True)
                results[source_name] = confidence
                continue

            results[source_name] = confidence

            if confidence.status == DataStatus.OFFLINE:
                continue

            # Route to appropriate DB(s)
            if source_name in _TEXT_SOURCES:
                self._store_documents(source_name, entity, data, now)
                self._store_text_metrics(source_name, entity, data, now)
            else:
                self._store_metrics(source_name, entity, data, now)

        return results

    def _store_metrics(
        self, source: str, entity: str, data: dict[str, Any], ts: datetime
    ) -> None:
        """Insert numeric metrics into metrics.db."""
        db_path = self._data_dir / "metrics.db"
        if not db_path.exists():
            return

        ts_str = ts.isoformat()
        rows = []
        for key, value in data.items():
            if isinstance(value, (int, float)) and value is not None:
                rows.append((ts_str, source, entity, key, float(value)))

        if not rows:
            return

        conn = sqlite3.connect(str(db_path))
        try:
            conn.executemany(
                "INSERT INTO metrics (timestamp, source, entity, metric, value) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        finally:
            conn.close()

    def _store_documents(
        self, source: str, entity: str, data: dict[str, Any], ts: datetime
    ) -> None:
        """Insert text documents into corpus.db."""
        db_path = self._data_dir / "corpus.db"
        if not db_path.exists():
            return

        documents = data.get("documents", [])
        if not documents:
            return

        ts_str = ts.isoformat()
        rows = []
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
            doc_source = doc.get("source", source)
            rows.append((
                doc.get("timestamp", ts_str) if isinstance(doc.get("timestamp"), str) else ts_str,
                doc_source,
                json.dumps([entity]),
                text,
                None,  # category (filled by narrative engine later)
                None,  # sentiment_score
            ))

        if not rows:
            return

        conn = sqlite3.connect(str(db_path))
        try:
            conn.executemany(
                "INSERT INTO documents (timestamp, source, entity_mentions, text, category, sentiment_score) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        finally:
            conn.close()

    def _store_text_metrics(
        self, source: str, entity: str, data: dict[str, Any], ts: datetime
    ) -> None:
        """Extract aggregated counts from text data and store in metrics.db."""
        db_path = self._data_dir / "metrics.db"
        if not db_path.exists():
            return

        ts_str = ts.isoformat()
        rows = []

        if "mention_count" in data:
            rows.append((ts_str, source, entity, "mention_count", float(data["mention_count"])))
        if "article_count" in data:
            rows.append((ts_str, source, entity, "article_count", float(data["article_count"])))
        if "total_results" in data:
            rows.append((ts_str, source, entity, "total_results", float(data["total_results"])))

        if not rows:
            return

        conn = sqlite3.connect(str(db_path))
        try:
            conn.executemany(
                "INSERT INTO metrics (timestamp, source, entity, metric, value) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        finally:
            conn.close()


def build_pipeline(
    config: "RadarConfig",  # noqa: F821 - avoid circular import
    data_dir: Path | None = None,
) -> DataPipeline:
    """Factory: build a DataPipeline from RadarConfig."""
    from contagion_radar.data.adapters import (
        DeFiLlamaAdapter,
        EtherscanAdapter,
        NewsAdapter,
        SocialAdapter,
        YahooFinanceAdapter,
    )

    adapters: dict[str, DataAdapter] = {
        "defillama": DeFiLlamaAdapter(),
        "etherscan": EtherscanAdapter(api_key=config.api_keys.etherscan),
        "yahoo_finance": YahooFinanceAdapter(),
        "social": SocialAdapter(
            twitter_bearer=config.api_keys.twitter_bearer,
            reddit_client_id=config.api_keys.reddit_client_id,
            reddit_client_secret=config.api_keys.reddit_client_secret,
        ),
        "news": NewsAdapter(api_key=config.api_keys.news_api),
    }

    gate = DataQualityGate(config.quality_gate)
    d = data_dir or Path(config.system.data_dir)

    return DataPipeline(adapters=adapters, quality_gate=gate, data_dir=d)
