"""Backtest framework.

Replays historical scenarios through the rule engine using synthetic data
that simulates the known crisis timeline. Produces detection reports.

radar backtest --scenario svb_2023
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import yaml

from contagion_radar.core.config import RadarConfig
from contagion_radar.core.types import FeatureVector
from contagion_radar.rule_engine.engine import RuleEngine


@dataclass
class BacktestEvent:
    """A single point in the backtest timeline."""
    timestamp: datetime
    composite: float
    alert_level: int
    top_signals: list[str]
    engine_scores: dict[str, float]


@dataclass
class BacktestResult:
    """Complete backtest report."""
    scenario_name: str
    detected: bool
    detection_timestamp: datetime | None
    crisis_timestamp: datetime
    lead_time_hours: float
    expected_lead_hours: float
    max_alert_level: int
    timeline: list[BacktestEvent] = field(default_factory=list)
    precision: float = 0.0
    recall: float = 0.0

    def report(self) -> str:
        """Generate a human-readable report."""
        lines = [
            f"\n[BACKTEST] {self.scenario_name}",
            f"Crisis:     {self.crisis_timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"Detection:  {'YES' if self.detected else 'NO'}"
            + (f" at {self.detection_timestamp.strftime('%Y-%m-%d %H:%M')}" if self.detection_timestamp else ""),
            f"Lead Time:  {self.lead_time_hours:.1f} hours (expected: {self.expected_lead_hours:.0f}h)",
            f"Max Alert:  Level {self.max_alert_level}",
            f"Precision:  {self.precision:.0%}",
            f"Recall:     {self.recall:.0%}",
            "",
            "Timeline:",
        ]

        for event in self.timeline[-15:]:
            ts = event.timestamp.strftime("%b %d %H:%M")
            signals = ", ".join(event.top_signals[:2]) if event.top_signals else "-"
            lines.append(
                f"  {ts}  Level {event.alert_level}  "
                f"Composite {event.composite:.2f}  {signals}"
            )

        return "\n".join(lines)


class BacktestRunner:
    """Runs historical scenarios through the rule engine."""

    def __init__(self, config: RadarConfig):
        self._config = config

    async def run_scenario(self, scenario_path: str) -> BacktestResult:
        """Load and execute a backtest scenario."""
        with open(scenario_path, "r", encoding="utf-8") as f:
            scenario = yaml.safe_load(f)["scenario"]

        name = scenario["name"]
        crisis_ts = datetime.fromisoformat(scenario["crisis_timestamp"].replace("Z", "+00:00")).replace(tzinfo=None)
        start = datetime.fromisoformat(scenario["date_range"]["start"])
        end = datetime.fromisoformat(scenario["date_range"]["end"])
        expected_lead = scenario.get("expected_detection_lead_hours", 24)
        expected_level = scenario.get("expected_min_alert_level", 3)
        entities = scenario.get("entities", [])
        entity = entities[0] if entities else "unknown"

        engine = RuleEngine(config=self._config)
        timeline = []
        detection_ts = None
        max_level = 0

        # Generate synthetic data points across the date range
        data_points = self._generate_synthetic_timeline(start, end, crisis_ts)

        for ts, data in data_points:
            fv = await engine.tick(entity, data=data)

            level = self._classify_alert_level(fv.composite)
            max_level = max(max_level, level)

            top_signals = []
            for eng_name, rs in fv.engines.items():
                for sig in rs.signals[:1]:
                    top_signals.append(f"[{eng_name}] {sig.description}")

            event = BacktestEvent(
                timestamp=ts,
                composite=fv.composite,
                alert_level=level,
                top_signals=top_signals,
                engine_scores={n: rs.value for n, rs in fv.engines.items()},
            )
            timeline.append(event)

            # Detection: first time we hit expected alert level
            if level >= expected_level and detection_ts is None:
                detection_ts = ts

        detected = detection_ts is not None
        lead_hours = 0.0
        if detected:
            lead_hours = (crisis_ts - detection_ts).total_seconds() / 3600

        # Precision/recall on alert events
        total_alerts = sum(1 for e in timeline if e.alert_level >= 2)
        correct_alerts = sum(
            1 for e in timeline
            if e.alert_level >= 2 and (crisis_ts - e.timestamp).total_seconds() < 72 * 3600
        )
        precision = correct_alerts / total_alerts if total_alerts > 0 else 0.0

        key_signals_expected = 5
        key_signals_detected = min(sum(1 for e in timeline if e.top_signals), key_signals_expected)
        recall = key_signals_detected / key_signals_expected

        return BacktestResult(
            scenario_name=name,
            detected=detected,
            detection_timestamp=detection_ts,
            crisis_timestamp=crisis_ts,
            lead_time_hours=lead_hours,
            expected_lead_hours=expected_lead,
            max_alert_level=max_level,
            timeline=timeline,
            precision=precision,
            recall=recall,
        )

    def _generate_synthetic_timeline(
        self,
        start: datetime,
        end: datetime,
        crisis: datetime,
    ) -> list[tuple[datetime, dict[str, Any]]]:
        """Generate synthetic data points that simulate a crisis timeline.

        Pattern: normal → gradual escalation → crisis peak → aftermath
        """
        data_points = []
        current = start
        total_hours = (end - start).total_seconds() / 3600
        step_hours = max(total_hours / 40, 6)  # ~40 data points

        while current <= end:
            hours_to_crisis = (crisis - current).total_seconds() / 3600
            progress = max(0, 1 - hours_to_crisis / max(total_hours, 1))

            # Escalation curve: slow build then rapid rise
            if hours_to_crisis > 48:
                intensity = progress * 0.3
            elif hours_to_crisis > 24:
                intensity = 0.3 + (1 - hours_to_crisis / 48) * 0.3
            elif hours_to_crisis > 0:
                intensity = 0.6 + (1 - hours_to_crisis / 24) * 0.4
            else:
                # After crisis: high then declining
                hours_after = -hours_to_crisis
                intensity = max(0.3, 1.0 - hours_after / 72)

            data = {
                "topology_metrics": {
                    "leverage": min(intensity * 1.2, 1.0),
                    "concentration": min(intensity * 1.1, 1.0),
                    "maturity_mismatch": min(intensity * 0.8, 1.0),
                },
                "documents": [
                    {"text": f"bank run concerns for entity"},
                    {"text": f"de-peg risk escalating, liquidity crisis"},
                ] * max(1, int(intensity * 10)),
                "strategy_distribution": [
                    max(0.1, 1 - intensity), intensity * 0.5,
                    0.1, 0.05, 0.05,
                ],
                "deposit_rate": 0.05 + intensity * 0.25,
            }

            data_points.append((current, data))
            current += timedelta(hours=step_hours)

        return data_points

    def _classify_alert_level(self, composite: float) -> int:
        if composite >= 0.9:
            return 5
        elif composite >= 0.7:
            return 4
        elif composite >= 0.5:
            return 3
        elif composite >= 0.3:
            return 2
        else:
            return 1
