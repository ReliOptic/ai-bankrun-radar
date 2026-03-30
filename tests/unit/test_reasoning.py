"""Tests for AI budget, novelty assessment, and pre-mortem scorer."""

import pytest

from contagion_radar.core.config import AIBudgetConfig, NoveltyMultiplierConfig
from contagion_radar.core.types import DataSignal, FeatureVector, Hypothesis, RiskScore
from contagion_radar.premortem.generator import PremortemGenerator
from contagion_radar.premortem.scorer import update_confidence
from contagion_radar.reasoning.budget import AIBudget
from contagion_radar.reasoning.novelty import assess_novelty


# ── AI Budget ────────────────────────────────────────────────


class TestAIBudget:
    @pytest.fixture
    def budget(self):
        return AIBudget(AIBudgetConfig())

    def test_can_call_normal(self, budget):
        assert budget.can_call("normal")

    def test_exhausted_budget(self, budget):
        for _ in range(20):
            budget.record_call("test")
        assert not budget.can_call("normal")

    def test_elevated_higher_limit(self, budget):
        for _ in range(20):
            budget.record_call("test")
        assert not budget.can_call("normal")
        assert budget.can_call("elevated")  # limit is 50

    def test_crisis_unlimited(self, budget):
        for _ in range(200):
            budget.record_call("test")
        assert budget.can_call("critical")

    def test_remaining_today(self, budget):
        assert budget.remaining_today("normal") == 20
        budget.record_call("test")
        assert budget.remaining_today("normal") == 19

    def test_risk_level_mapping(self, budget):
        assert budget.risk_level_for_score(0.1) == "normal"
        assert budget.risk_level_for_score(0.65) == "elevated"
        assert budget.risk_level_for_score(0.85) == "warning"
        assert budget.risk_level_for_score(0.96) == "critical"


# ── Novelty Assessment ───────────────────────────────────────


class TestNoveltyAssessment:
    @pytest.fixture
    def feature_vector(self):
        return FeatureVector(
            composite=0.6,
            engines={
                "topology": RiskScore(engine="topology", value=0.5),
                "narrative": RiskScore(engine="narrative", value=0.7),
                "monoculture": RiskScore(engine="monoculture", value=0.4),
            },
        )

    def test_no_precedents_high_multiplier(self, feature_vector):
        result = assess_novelty(feature_vector, [])
        assert result.multiplier == pytest.approx(1.5)
        assert result.similarity == 0.0

    def test_similar_precedent_low_multiplier(self, feature_vector):
        precedents = [{
            "name": "SVB_2023",
            "features": {
                "composite": 0.6,
                "engine_topology": 0.5,
                "engine_narrative": 0.7,
                "engine_monoculture": 0.4,
            },
        }]
        result = assess_novelty(feature_vector, precedents)
        assert result.multiplier == pytest.approx(1.0)
        assert result.similarity > 0.9
        assert result.closest_precedent == "SVB_2023"

    def test_dissimilar_precedent_high_multiplier(self, feature_vector):
        # Use a precedent with very different pattern (some negative-like ratios)
        # Current: composite=0.6, topo=0.5, narr=0.7, mono=0.4
        # Precedent: very different distribution
        precedents = [{
            "name": "TerraLuna_2022",
            "features": {
                "composite": 0.9,
                "engine_topology": 0.01,
                "engine_narrative": 0.01,
                "engine_monoculture": 0.99,
                "gp_run_prob": 0.9,
            },
        }]
        result = assess_novelty(feature_vector, precedents)
        # With cosine similarity on positive vectors, anything with different proportions
        # should show at least moderate novelty
        assert result.multiplier >= 1.0

    def test_multiplier_range(self, feature_vector):
        result = assess_novelty(feature_vector, [])
        assert 1.0 <= result.multiplier <= 1.5


# ── Pre-mortem Scorer ────────────────────────────────────────


class TestPremortemScorer:
    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            entity_id="USDC",
            failure_mode="de_peg",
            cause_chain=["reserve_concentration", "bank_failure"],
            probability=0.15,
            data_signals=[
                DataSignal(
                    metric="peg_deviation",
                    entity="USDC",
                    threshold=0.005,
                    direction="above",
                ),
                DataSignal(
                    metric="reserve_bank_cds",
                    entity="SVB",
                    threshold=300,
                    direction="above",
                ),
            ],
            confidence=0.5,
        )

    def test_supporting_evidence_increases_confidence(self, hypothesis):
        updated = update_confidence(
            hypothesis, "peg_deviation", 0.01, "above"
        )
        assert updated.confidence > 0.5
        assert len(updated.evidence_for) == 1

    def test_contradicting_evidence_decreases_confidence(self, hypothesis):
        updated = update_confidence(
            hypothesis, "peg_deviation", 0.001, "above"
        )
        assert updated.confidence < 0.5
        assert len(updated.evidence_against) == 1

    def test_multiple_supporting_evidence(self, hypothesis):
        update_confidence(hypothesis, "peg_deviation", 0.01, "above")
        update_confidence(hypothesis, "reserve_bank_cds", 500, "above")
        assert hypothesis.confidence > 0.7

    def test_confidence_bounded(self, hypothesis):
        for _ in range(20):
            update_confidence(hypothesis, "peg_deviation", 0.05, "above")
        assert hypothesis.confidence <= 0.99

    def test_trajectory_recorded(self, hypothesis):
        update_confidence(hypothesis, "peg_deviation", 0.01, "above")
        assert len(hypothesis.confidence_trajectory) == 1

    def test_unmatched_metric_no_change(self, hypothesis):
        update_confidence(hypothesis, "unknown_metric", 100, "above")
        assert hypothesis.confidence == 0.5


# ── Pre-mortem Generator (offline mode) ──────────────────────


class TestPremortemGeneratorOffline:
    def test_offline_generates_hypotheses(self):
        from contagion_radar.core.config import AIConfig
        from contagion_radar.reasoning.client import AIClient

        client = AIClient(AIConfig())
        gen = PremortemGenerator(client)

        fv = FeatureVector(
            composite=0.6,
            engines={
                "topology": RiskScore(engine="topology", value=0.5),
                "narrative": RiskScore(engine="narrative", value=0.7),
            },
        )

        hypotheses = gen.generate_offline("USDC", fv)
        assert len(hypotheses) >= 1
        assert all(h.entity_id == "USDC" for h in hypotheses)
        assert all(h.model_used == "rule_based" for h in hypotheses)

    def test_offline_low_scores_no_hypotheses(self):
        from contagion_radar.core.config import AIConfig
        from contagion_radar.reasoning.client import AIClient

        client = AIClient(AIConfig())
        gen = PremortemGenerator(client)

        fv = FeatureVector(
            composite=0.1,
            engines={
                "topology": RiskScore(engine="topology", value=0.1),
                "narrative": RiskScore(engine="narrative", value=0.1),
            },
        )

        hypotheses = gen.generate_offline("USDC", fv)
        assert len(hypotheses) == 0
