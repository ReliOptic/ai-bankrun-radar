"""Tests for Rule Engine main loop."""

import pytest

from contagion_radar.core.config import RadarConfig
from contagion_radar.rule_engine.engine import RuleEngine


@pytest.fixture
def config():
    return RadarConfig()


@pytest.fixture
def engine(config):
    return RuleEngine(config=config)


class TestRuleEngine:
    @pytest.mark.asyncio
    async def test_tick_with_synthetic_data(self, engine):
        """tick() with pre-supplied data returns a valid FeatureVector."""
        data = {
            "topology_metrics": {"leverage": 0.5, "concentration": 0.6},
            "documents": [
                {"text": "USDC de-peg fears are growing rapidly"},
                {"text": "USDC bank run imminent, withdraw now"},
            ] * 5,
            "strategy_distribution": [0.7, 0.1, 0.1, 0.05, 0.05],
            "deposit_rate": 0.10,
        }
        fv = engine.tick.__wrapped__(engine, "USDC", data=data) if hasattr(engine.tick, '__wrapped__') else await engine.tick("USDC", data=data)

        assert 0.0 <= fv.composite <= 1.0
        assert "topology" in fv.engines
        assert "narrative" in fv.engines
        assert "monoculture" in fv.engines
        assert fv.gp_run_probability is not None
        assert fv.dd_f_critical is not None

    @pytest.mark.asyncio
    async def test_tick_no_data(self, engine):
        """tick() with empty data returns low scores."""
        fv = await engine.tick("USDC", data={})
        assert 0.0 <= fv.composite <= 1.0

    @pytest.mark.asyncio
    async def test_crisis_data_produces_elevated_score(self, engine):
        """Extreme synthetic data should produce an elevated composite."""
        crisis_data = {
            "topology_metrics": {
                "leverage": 0.9,
                "maturity_mismatch": 0.8,
                "concentration": 0.9,
            },
            "documents": [
                {"text": "USDC bank run in progress, massive withdrawals"},
                {"text": "USDC de-peg confirmed, trading at $0.90"},
                {"text": "Systemic contagion spreading from SVB to USDC"},
                {"text": "Liquidity crisis: all USDC redemptions frozen"},
            ] * 10,
            "strategy_distribution": [0.95, 0.02, 0.01, 0.01, 0.01],
            "deposit_rate": 0.28,
        }
        fv = await engine.tick("USDC", data=crisis_data)
        assert fv.composite > 0.3

    @pytest.mark.asyncio
    async def test_last_feature_vector_updated(self, engine):
        assert engine.last_feature_vector is None
        await engine.tick("USDC", data={})
        assert engine.last_feature_vector is not None
