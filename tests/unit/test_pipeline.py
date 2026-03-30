"""Tests for Data Pipeline (storage routing) with mock adapters."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from contagion_radar.core.config import QualityGateConfig, SourceQualityConfig
from contagion_radar.core.types import DataConfidence, DataStatus
from contagion_radar.data.adapters.base import AdapterError, DataAdapter
from contagion_radar.data.pipeline import DataPipeline
from contagion_radar.data.quality_gate import DataQualityGate
from contagion_radar.knowledge.database import init_corpus_db, init_metrics_db


class MockNumericAdapter(DataAdapter):
    source_name = "defillama"

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict, DataConfidence]:
        return {
            "tvl": 5_000_000_000.0,
            "chain": "Ethereum",
            "change_1d": -2.5,
        }, self._make_confidence()


class MockTextAdapter(DataAdapter):
    source_name = "social"

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict, DataConfidence]:
        return {
            "documents": [
                {"text": "USDC is losing its peg!", "source": "reddit"},
                {"text": "Bank run concerns growing", "source": "reddit"},
            ],
            "mention_count": 2,
            "text": "Social mentions for USDC",
        }, self._make_confidence()


class MockFailingAdapter(DataAdapter):
    source_name = "etherscan"

    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict, DataConfidence]:
        raise AdapterError("etherscan", "API key invalid")


@pytest.fixture
def data_dir(tmp_path):
    init_metrics_db(tmp_path)
    init_corpus_db(tmp_path)
    return tmp_path


@pytest.fixture
def gate():
    return DataQualityGate(QualityGateConfig(
        sources={
            "defillama": SourceQualityConfig(
                max_stale_seconds=900,
                circuit_breaker_failures=3,
                completeness_required_fields=["tvl", "chain"],
            ),
            "social": SourceQualityConfig(
                max_stale_seconds=1800,
                circuit_breaker_failures=5,
                completeness_required_fields=["text"],
            ),
            "etherscan": SourceQualityConfig(
                max_stale_seconds=600,
                circuit_breaker_failures=3,
            ),
        },
        score_discounts={"FRESH": 1.0, "STALE": 0.7, "DEGRADED": 0.4, "OFFLINE": 0.0},
    ))


@pytest.fixture
def pipeline(data_dir, gate):
    adapters = {
        "defillama": MockNumericAdapter(),
        "social": MockTextAdapter(),
        "etherscan": MockFailingAdapter(),
    }
    return DataPipeline(adapters=adapters, quality_gate=gate, data_dir=data_dir)


class TestPipeline:
    @pytest.mark.asyncio
    async def test_numeric_stored_in_metrics(self, pipeline, data_dir):
        results = await pipeline.fetch_and_store("USDC", sources=["defillama"])
        assert "defillama" in results
        assert results["defillama"].status == DataStatus.FRESH

        conn = sqlite3.connect(str(data_dir / "metrics.db"))
        rows = conn.execute(
            "SELECT entity, metric, value FROM metrics WHERE source = 'defillama'"
        ).fetchall()
        conn.close()

        metrics = {r[1]: r[2] for r in rows}
        assert metrics["tvl"] == 5_000_000_000.0
        assert metrics["change_1d"] == -2.5

    @pytest.mark.asyncio
    async def test_text_stored_in_corpus(self, pipeline, data_dir):
        results = await pipeline.fetch_and_store("USDC", sources=["social"])
        assert "social" in results

        conn = sqlite3.connect(str(data_dir / "corpus.db"))
        rows = conn.execute("SELECT text FROM documents").fetchall()
        conn.close()

        texts = [r[0] for r in rows]
        assert any("peg" in t for t in texts)
        assert len(texts) == 2

    @pytest.mark.asyncio
    async def test_text_also_stores_metrics(self, pipeline, data_dir):
        await pipeline.fetch_and_store("USDC", sources=["social"])

        conn = sqlite3.connect(str(data_dir / "metrics.db"))
        rows = conn.execute(
            "SELECT metric, value FROM metrics WHERE source = 'social'"
        ).fetchall()
        conn.close()

        metrics = {r[0]: r[1] for r in rows}
        assert metrics["mention_count"] == 2.0

    @pytest.mark.asyncio
    async def test_failing_adapter_returns_degraded(self, pipeline, data_dir):
        results = await pipeline.fetch_and_store("USDC", sources=["etherscan"])
        assert results["etherscan"].status == DataStatus.DEGRADED

        # No data stored in metrics.db for etherscan
        conn = sqlite3.connect(str(data_dir / "metrics.db"))
        rows = conn.execute(
            "SELECT COUNT(*) FROM metrics WHERE source = 'etherscan'"
        ).fetchone()
        conn.close()
        assert rows[0] == 0

    @pytest.mark.asyncio
    async def test_all_sources_together(self, pipeline, data_dir):
        results = await pipeline.fetch_and_store("USDC")
        assert len(results) == 3
        assert results["defillama"].status == DataStatus.FRESH
        assert results["social"].status == DataStatus.FRESH
        assert results["etherscan"].status == DataStatus.DEGRADED
