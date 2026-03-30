"""Tests for Cadence Controller."""

import pytest

from contagion_radar.cadence.controller import CadenceController
from contagion_radar.core.config import CadenceConfig
from contagion_radar.core.types import AITriggerType, CadenceState


@pytest.fixture
def config():
    return CadenceConfig(
        curve=[
            [0.0, 3600], [0.2, 3600], [0.3, 1800], [0.4, 1200],
            [0.5, 600], [0.6, 300], [0.7, 180], [0.8, 120],
            [0.9, 60], [0.95, 30], [1.0, 10],
        ],
    )


@pytest.fixture
def controller(config):
    return CadenceController(config)


class TestInterpolation:
    def test_low_score_long_interval(self, controller):
        decision = controller.update(0.1)
        assert decision.interval_seconds == pytest.approx(3600)

    def test_mid_score_mid_interval(self, controller):
        decision = controller.update(0.5)
        assert decision.interval_seconds == pytest.approx(600)

    def test_high_score_short_interval(self, controller):
        # Feed 3 rising ticks to trigger escalation
        controller.update(0.7)
        controller.update(0.8)
        decision = controller.update(0.9)
        assert decision.interval_seconds <= 60

    def test_max_score(self, controller):
        for _ in range(3):
            controller.update(1.0)
        decision = controller.update(1.0)
        assert decision.interval_seconds == pytest.approx(10)


class TestHysteresis:
    def test_escalation_after_consecutive_rises(self, controller):
        """3 consecutive rises → immediate interval reduction."""
        controller.update(0.3)
        controller.update(0.5)
        decision = controller.update(0.7)
        # Should have escalated after 3 consecutive rises
        assert decision.interval_seconds <= 600

    def test_deescalation_is_gradual(self, controller):
        """Score drop: interval increases gradually, not instantly."""
        # Rise to crisis
        for _ in range(3):
            controller.update(0.9)

        crisis_interval = controller.update(0.9).interval_seconds

        # Drop to normal — but too soon (stability window not met)
        decision = controller.update(0.1)
        # Should NOT instantly jump to 3600 (damped)
        assert decision.interval_seconds < 3600


class TestStateClassification:
    def test_states(self, controller):
        assert controller.update(0.1).state == CadenceState.NORMAL
        assert controller.update(0.5).state == CadenceState.ELEVATED
        assert controller.update(0.75).state == CadenceState.CRITICAL
        assert controller.update(0.95).state == CadenceState.CRISIS


class TestAITriggers:
    def test_crisis_triggers_analysis(self, controller):
        decision = controller.update(0.95)
        trigger_types = [t.type for t in decision.ai_triggers]
        assert AITriggerType.CRISIS_ANALYSIS in trigger_types

    def test_elevated_triggers_context(self, controller):
        decision = controller.update(0.55)
        trigger_types = [t.type for t in decision.ai_triggers]
        assert AITriggerType.CONTEXT_INTERPRETATION in trigger_types

    def test_postmortem_on_score_drop(self, controller):
        """Score drops from above 0.7 to below 0.5 → postmortem trigger."""
        controller.update(0.8)
        controller.update(0.8)
        decision = controller.update(0.3)
        trigger_types = [t.type for t in decision.ai_triggers]
        assert AITriggerType.POST_MORTEM in trigger_types

    def test_low_score_no_triggers(self, controller):
        decision = controller.update(0.1)
        assert len(decision.ai_triggers) == 0
