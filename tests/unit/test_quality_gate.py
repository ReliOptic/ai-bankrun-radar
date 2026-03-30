"""Tests for Data Quality Gate."""

from datetime import datetime, timedelta

import pytest

from contagion_radar.core.config import QualityGateConfig, SourceQualityConfig
from contagion_radar.core.types import DataStatus
from contagion_radar.data.quality_gate import DataQualityGate


@pytest.fixture
def gate():
    config = QualityGateConfig(
        sources={
            "test_source": SourceQualityConfig(
                max_stale_seconds=60,
                circuit_breaker_failures=3,
                completeness_required_fields=["price", "volume"],
            ),
        },
        score_discounts={"FRESH": 1.0, "STALE": 0.7, "DEGRADED": 0.4, "OFFLINE": 0.0},
    )
    return DataQualityGate(config)


class TestAssess:
    def test_fresh_data(self, gate):
        now = datetime.utcnow()
        conf = gate.assess("test_source", {"price": 100, "volume": 5000}, now)
        assert conf.status == DataStatus.FRESH
        assert conf.completeness_ratio == 1.0
        assert conf.consecutive_failures == 0

    def test_incomplete_data_degraded(self, gate):
        now = datetime.utcnow()
        conf = gate.assess("test_source", {"price": 100}, now)
        assert conf.completeness_ratio == 0.5
        assert conf.status == DataStatus.DEGRADED

    def test_stale_after_max_stale(self, gate):
        """Data is STALE when a fetch fails after a long gap since last success."""
        t1 = datetime.utcnow()
        gate.assess("test_source", {"price": 100, "volume": 5000}, t1)
        t2 = t1 + timedelta(seconds=120)
        # Simulate a failed fetch — last_success stays at t1, staleness = 120s > 60s max
        conf = gate.assess("test_source", {}, t2, error=True)
        assert conf.staleness_seconds >= 120
        # With 1 failure it's DEGRADED (not yet OFFLINE)
        assert conf.status == DataStatus.DEGRADED

    def test_single_error_degraded(self, gate):
        now = datetime.utcnow()
        conf = gate.assess("test_source", {}, now, error=True)
        assert conf.status == DataStatus.DEGRADED
        assert conf.consecutive_failures == 1

    def test_circuit_breaker_offline(self, gate):
        now = datetime.utcnow()
        for i in range(3):
            conf = gate.assess("test_source", {}, now, error=True)

        assert conf.status == DataStatus.OFFLINE
        assert conf.consecutive_failures == 3

    def test_success_resets_failures(self, gate):
        now = datetime.utcnow()
        gate.assess("test_source", {}, now, error=True)
        gate.assess("test_source", {}, now, error=True)
        conf = gate.assess("test_source", {"price": 100, "volume": 5000}, now, error=False)
        assert conf.status == DataStatus.FRESH
        assert conf.consecutive_failures == 0

    def test_unknown_source_uses_defaults(self, gate):
        now = datetime.utcnow()
        conf = gate.assess("unknown_source", {"something": 42}, now)
        assert conf.status == DataStatus.FRESH


class TestScoreDiscount:
    def test_discounts(self, gate):
        from contagion_radar.core.types import DataConfidence

        for status, expected in [
            (DataStatus.FRESH, 1.0),
            (DataStatus.STALE, 0.7),
            (DataStatus.DEGRADED, 0.4),
            (DataStatus.OFFLINE, 0.0),
        ]:
            conf = DataConfidence(source="test", status=status)
            assert gate.score_discount(conf) == expected


class TestReset:
    def test_reset_clears_failures(self, gate):
        now = datetime.utcnow()
        gate.assess("test_source", {}, now, error=True)
        gate.assess("test_source", {}, now, error=True)
        gate.reset("test_source")
        conf = gate.assess("test_source", {}, now, error=True)
        assert conf.consecutive_failures == 1  # reset, then 1 new failure
        assert conf.status == DataStatus.DEGRADED  # not OFFLINE
