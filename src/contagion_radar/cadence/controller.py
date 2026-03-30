"""Cadence Controller: adaptive monitoring interval + AI trigger decisions.

Score → interval mapping via piecewise-linear curve from cadence.yaml.
Hysteresis:
  - Escalation: 3 consecutive rising ticks → immediate interval reduction
  - De-escalation: damping factor + stability window before interval increase
"""

from __future__ import annotations

import time

import numpy as np

from contagion_radar.core.config import CadenceConfig
from contagion_radar.core.types import AITrigger, AITriggerType, CadenceDecision, CadenceState


class CadenceController:
    """Decides monitoring interval and AI trigger events based on score trajectory."""

    def __init__(self, config: CadenceConfig):
        self._config = config
        self._curve = sorted(config.curve, key=lambda p: p[0])
        self._history: list[float] = []
        self._current_interval: float = config.hysteresis.max_interval_seconds
        self._last_state_change: float = time.time()
        self._current_state = CadenceState.NORMAL
        self._peak_score: float = 0.0

    def update(self, score: float) -> CadenceDecision:
        """Process a new composite score. Returns interval + AI triggers."""
        self._history.append(score)
        self._peak_score = max(self._peak_score, score)

        target_interval = self._interpolate_interval(score)
        new_state = self._classify_state(score)

        # Hysteresis logic
        if target_interval < self._current_interval:
            # Escalation: check consecutive rising ticks
            if self._should_escalate():
                self._current_interval = target_interval
                self._last_state_change = time.time()
        elif target_interval > self._current_interval:
            # De-escalation: apply damping + stability window
            if self._should_deescalate():
                damping = self._config.hysteresis.deescalation_damping
                self._current_interval += (target_interval - self._current_interval) * damping
            # Don't actually increase until stable
        # else: same interval, no change

        # Clamp
        hyst = self._config.hysteresis
        self._current_interval = float(np.clip(
            self._current_interval,
            hyst.min_interval_seconds,
            hyst.max_interval_seconds,
        ))

        self._current_state = new_state
        ai_triggers = self._check_ai_triggers(score)

        return CadenceDecision(
            interval_seconds=self._current_interval,
            ai_triggers=ai_triggers,
            state=new_state,
        )

    def _interpolate_interval(self, score: float) -> float:
        """Piecewise linear interpolation on the score→interval curve."""
        if not self._curve:
            return self._config.hysteresis.max_interval_seconds

        if score <= self._curve[0][0]:
            return self._curve[0][1]
        if score >= self._curve[-1][0]:
            return self._curve[-1][1]

        for i in range(len(self._curve) - 1):
            s0, i0 = self._curve[i]
            s1, i1 = self._curve[i + 1]
            if s0 <= score <= s1:
                t = (score - s0) / (s1 - s0) if s1 != s0 else 0
                return i0 + t * (i1 - i0)

        return self._curve[-1][1]

    def _classify_state(self, score: float) -> CadenceState:
        if score >= 0.9:
            return CadenceState.CRISIS
        elif score >= 0.7:
            return CadenceState.CRITICAL
        elif score >= 0.4:
            return CadenceState.ELEVATED
        else:
            return CadenceState.NORMAL

    def _should_escalate(self) -> bool:
        """Check if last N ticks show consecutive score increases."""
        n = self._config.hysteresis.escalation_consecutive_ticks
        if len(self._history) < n:
            return True  # first few ticks: escalate immediately

        recent = self._history[-n:]
        return all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

    def _should_deescalate(self) -> bool:
        """Check if enough time has passed since last state change."""
        elapsed = time.time() - self._last_state_change
        return elapsed >= self._config.hysteresis.stability_window_seconds

    def _check_ai_triggers(self, score: float) -> list[AITrigger]:
        """Determine which AI tasks to trigger based on score."""
        triggers = []
        at = self._config.ai_triggers

        if score >= at.crisis_analysis_threshold:
            triggers.append(AITrigger(
                type=AITriggerType.CRISIS_ANALYSIS,
                reason=f"Score {score:.2f} >= crisis threshold {at.crisis_analysis_threshold}",
            ))

        if score >= at.premortem_generation_threshold:
            triggers.append(AITrigger(
                type=AITriggerType.PREMORTEM_GENERATION,
                reason=f"Score {score:.2f} >= premortem threshold {at.premortem_generation_threshold}",
            ))

        if score >= at.context_interpretation_threshold:
            triggers.append(AITrigger(
                type=AITriggerType.CONTEXT_INTERPRETATION,
                reason=f"Score {score:.2f} >= context threshold {at.context_interpretation_threshold}",
            ))

        # Post-mortem: score dropped below threshold after being above
        if (
            score < at.postmortem_drop_below
            and self._peak_score >= at.postmortem_was_above
        ):
            triggers.append(AITrigger(
                type=AITriggerType.POST_MORTEM,
                reason=f"Score dropped to {score:.2f} from peak {self._peak_score:.2f}",
            ))

        return triggers
