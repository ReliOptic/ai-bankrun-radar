"""AI Budget Manager.

Tracks daily AI call limits per risk level.
Crisis mode: unlimited calls. Normal: 20/day. Elevated: 50. Warning: 200.
"""

from __future__ import annotations

from datetime import datetime, timezone

from contagion_radar.core.config import AIBudgetConfig


class AIBudget:
    """Manages daily AI call quotas based on risk level."""

    def __init__(self, config: AIBudgetConfig):
        self._config = config
        self._daily_calls: int = 0
        self._daily_tokens: int = 0
        self._daily_cost: float = 0.0
        self._current_date: str = ""

    def can_call(self, risk_level: str = "normal") -> bool:
        """Check if an AI call is allowed under current budget."""
        self._maybe_reset_day()

        limit = self._config.daily_limits.get(risk_level, 20)
        if limit == -1:  # unlimited (crisis mode)
            return True

        return self._daily_calls < limit

    def record_call(
        self,
        call_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Record an AI call for budget tracking."""
        self._maybe_reset_day()
        self._daily_calls += 1
        self._daily_tokens += input_tokens + output_tokens
        self._daily_cost += cost_usd

    def remaining_today(self, risk_level: str = "normal") -> int:
        """How many calls remain today for the given risk level."""
        self._maybe_reset_day()
        limit = self._config.daily_limits.get(risk_level, 20)
        if limit == -1:
            return 999999
        return max(0, limit - self._daily_calls)

    @property
    def daily_calls(self) -> int:
        self._maybe_reset_day()
        return self._daily_calls

    @property
    def daily_cost(self) -> float:
        self._maybe_reset_day()
        return self._daily_cost

    def _maybe_reset_day(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            self._current_date = today
            self._daily_calls = 0
            self._daily_tokens = 0
            self._daily_cost = 0.0

    def risk_level_for_score(self, score: float) -> str:
        """Map composite score to risk level string."""
        thresholds = self._config.risk_level_thresholds
        if score >= thresholds.get("warning", 0.8):
            return "warning" if score < 0.95 else "critical"
        elif score >= thresholds.get("elevated", 0.6):
            return "elevated"
        elif score >= thresholds.get("normal", 0.3):
            return "normal"
        else:
            return "normal"
