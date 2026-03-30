"""Tests for the three risk engines and composite scorer."""

import numpy as np
import pytest

from contagion_radar.core.config import (
    CompositeConfig,
    MonocultureConfig,
    NarrativeConfig,
    TopologyConfig,
)
from contagion_radar.core.types import DataConfidence, DataStatus, RiskScore
from contagion_radar.engines.monoculture.engine import MonocultureEngine
from contagion_radar.engines.narrative.engine import NarrativeEngine
from contagion_radar.engines.topology.engine import ExposureEdge, TopologyEngine
from contagion_radar.rule_engine.composite import CompositeScorer


# ── Topology Engine ──────────────────────────────────────────


class TestTopologyEngine:
    @pytest.fixture
    def engine(self):
        return TopologyEngine(TopologyConfig())

    def test_no_graph_returns_low_score(self, engine):
        score = engine.compute("USDC")
        assert score.engine == "topology"
        assert score.value == 0.0

    def test_high_leverage_triggers_signal(self, engine):
        score = engine.compute("USDC", metrics={"leverage": 0.8})
        assert score.value > 0
        assert any(s.metric == "leverage" for s in score.signals)

    def test_graph_with_edges(self, engine):
        edges = [
            ExposureEdge("SVB", "USDC", 3_300_000_000),
            ExposureEdge("USDC", "Aave", 1_000_000_000),
            ExposureEdge("Aave", "DAI", 500_000_000),
            ExposureEdge("SVB", "Aave", 800_000_000),
        ]
        engine.build_graph(edges)
        score = engine.compute("SVB", metrics={"leverage": 0.7, "concentration": 0.8})
        assert score.value > 0.2
        assert len(score.signals) >= 1

    def test_score_in_range(self, engine):
        score = engine.compute("X", metrics={"leverage": 0.9, "maturity_mismatch": 0.8, "concentration": 0.9})
        assert 0.0 <= score.value <= 1.0


# ── Narrative Engine ─────────────────────────────────────────


class TestNarrativeEngine:
    @pytest.fixture
    def engine(self):
        return NarrativeEngine(NarrativeConfig())

    def test_no_documents_zero_score(self, engine):
        score = engine.compute("USDC", [])
        assert score.value == 0.0

    def test_crisis_keywords_detected(self, engine):
        docs = [
            {"text": "USDC is experiencing a de-peg event, price below $0.95"},
            {"text": "USDC bank run fears intensify as withdrawals surge"},
            {"text": "USDC liquidity crisis deepens, redemptions halted"},
        ] * 5  # repeat for volume
        score = engine.compute("USDC", docs)
        assert score.value > 0.0
        assert len(score.signals) >= 1

    def test_classify_text(self, engine):
        categories = engine.classify_text("Major bank run at Silicon Valley Bank")
        assert "bank_run" in categories

    def test_depeg_detection(self, engine):
        categories = engine.classify_text("USDC lost its peg, trading at 0.93")
        assert "de_peg" in categories

    def test_benign_text_no_categories(self, engine):
        categories = engine.classify_text("The weather is nice today")
        assert len(categories) == 0

    def test_momentum_scaling(self, engine):
        """More mentions relative to baseline → higher score."""
        few_docs = [{"text": "USDC de-peg concerns"}] * 2
        many_docs = [{"text": "USDC de-peg concerns"}] * 20
        score_few = engine.compute("USDC", few_docs)
        score_many = engine.compute("USDC", many_docs)
        assert score_many.value >= score_few.value


# ── Monoculture Engine ───────────────────────────────────────


class TestMonocultureEngine:
    @pytest.fixture
    def engine(self):
        return MonocultureEngine(MonocultureConfig())

    def test_diverse_distribution_low_score(self, engine):
        dist = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        score = engine.compute("market", strategy_distribution=dist)
        assert score.value < 0.3

    def test_concentrated_distribution_high_score(self, engine):
        dist = [0.95, 0.01, 0.01, 0.01, 0.01, 0.01]
        score = engine.compute("market", strategy_distribution=dist)
        assert score.value > 0.5
        assert any(s.metric == "monoculture_index" for s in score.signals)

    def test_high_correlation_detected(self, engine):
        rng = np.random.default_rng(42)
        base = np.cumsum(rng.standard_normal(100)) + 100
        price_series = {
            "A": list(base + rng.standard_normal(100) * 0.1),
            "B": list(base + rng.standard_normal(100) * 0.1),
            "C": list(base + rng.standard_normal(100) * 0.1),
        }
        score = engine.compute("market", price_series=price_series)
        assert score.value > 0
        assert any(s.metric == "cross_correlation" for s in score.signals)

    def test_no_data_zero_score(self, engine):
        score = engine.compute("market")
        assert score.value == 0.0


# ── Composite Scorer ─────────────────────────────────────────


class TestCompositeScorer:
    @pytest.fixture
    def scorer(self):
        return CompositeScorer(CompositeConfig())

    @pytest.fixture
    def fresh_confidences(self):
        return {
            "defillama": DataConfidence(source="defillama", status=DataStatus.FRESH),
            "etherscan": DataConfidence(source="etherscan", status=DataStatus.FRESH),
            "yahoo_finance": DataConfidence(source="yahoo_finance", status=DataStatus.FRESH),
            "social": DataConfidence(source="social", status=DataStatus.FRESH),
            "news": DataConfidence(source="news", status=DataStatus.FRESH),
        }

    def test_basic_composite(self, scorer, fresh_confidences):
        scores = {
            "topology": RiskScore(engine="topology", value=0.3),
            "narrative": RiskScore(engine="narrative", value=0.2),
            "monoculture": RiskScore(engine="monoculture", value=0.1),
        }
        fv = scorer.compute(scores, fresh_confidences)
        assert 0.0 <= fv.composite <= 1.0
        assert fv.engines == scores

    def test_cross_engine_amplification(self, scorer, fresh_confidences):
        """When 2+ engines above threshold, composite is amplified."""
        scores_elevated = {
            "topology": RiskScore(engine="topology", value=0.6),
            "narrative": RiskScore(engine="narrative", value=0.6),
            "monoculture": RiskScore(engine="monoculture", value=0.6),
        }
        scores_low = {
            "topology": RiskScore(engine="topology", value=0.6),
            "narrative": RiskScore(engine="narrative", value=0.1),
            "monoculture": RiskScore(engine="monoculture", value=0.1),
        }
        fv_high = scorer.compute(scores_elevated, fresh_confidences)
        fv_low = scorer.compute(scores_low, fresh_confidences)
        # Amplified score should be significantly higher
        assert fv_high.composite > fv_low.composite

    def test_offline_source_discounts(self, scorer):
        """OFFLINE data source → engine contribution = 0."""
        confidences = {
            "defillama": DataConfidence(source="defillama", status=DataStatus.OFFLINE),
            "etherscan": DataConfidence(source="etherscan", status=DataStatus.OFFLINE),
            "social": DataConfidence(source="social", status=DataStatus.FRESH),
            "news": DataConfidence(source="news", status=DataStatus.FRESH),
            "yahoo_finance": DataConfidence(source="yahoo_finance", status=DataStatus.FRESH),
        }
        scores = {
            "topology": RiskScore(engine="topology", value=0.9),
            "narrative": RiskScore(engine="narrative", value=0.1),
            "monoculture": RiskScore(engine="monoculture", value=0.1),
        }
        fv = scorer.compute(scores, confidences)
        # Topology is 0.9 but its sources are OFFLINE → discounted to 0
        assert fv.composite < 0.5

    def test_gp_integration(self, scorer, fresh_confidences):
        """G&P run probability is blended into composite."""
        scores = {
            "topology": RiskScore(engine="topology", value=0.3),
            "narrative": RiskScore(engine="narrative", value=0.3),
            "monoculture": RiskScore(engine="monoculture", value=0.3),
        }
        fv_no_gp = scorer.compute(scores, fresh_confidences)
        fv_with_gp = scorer.compute(scores, fresh_confidences, gp_run_probability=0.8)
        assert fv_with_gp.composite > fv_no_gp.composite
        assert fv_with_gp.gp_run_probability == 0.8

    def test_composite_capped_at_1(self, scorer, fresh_confidences):
        """Even with amplification, composite <= 1.0."""
        scores = {
            "topology": RiskScore(engine="topology", value=1.0),
            "narrative": RiskScore(engine="narrative", value=1.0),
            "monoculture": RiskScore(engine="monoculture", value=1.0),
        }
        fv = scorer.compute(scores, fresh_confidences, gp_run_probability=1.0)
        assert fv.composite <= 1.0

    def test_weights_sum_to_1(self):
        config = CompositeConfig()
        assert sum(config.weights.values()) == pytest.approx(1.0)
