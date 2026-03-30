"""Calibrator: KB feedback loop to rule engine weights.

Reviews past 90 days of hypotheses and anomalies, computes per-engine
precision, and adjusts composite weights. Changes are bounded (max +-20%/round)
and logged to calibrations table.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml


@dataclass
class CalibrationResult:
    """Result of a calibration run."""
    old_weights: dict[str, float]
    new_weights: dict[str, float]
    engine_precision: dict[str, float]
    changes: list[str] = field(default_factory=list)
    applied: bool = False


class Calibrator:
    """Adjusts engine weights based on historical accuracy."""

    MAX_CHANGE_RATIO = 0.20  # max +-20% per round

    def __init__(self, data_dir: Path, config_dir: Path):
        self._data_dir = data_dir
        self._config_dir = config_dir

    def recalibrate(self, dry_run: bool = False) -> CalibrationResult:
        """Analyze historical accuracy and adjust weights.

        Args:
            dry_run: if True, compute suggestions without applying them
        """
        old_weights = self._load_current_weights()
        precision = self._compute_engine_precision()

        new_weights = self._adjust_weights(old_weights, precision)
        changes = []

        for engine in old_weights:
            old_w = old_weights[engine]
            new_w = new_weights.get(engine, old_w)
            if abs(new_w - old_w) > 0.001:
                changes.append(
                    f"{engine}: {old_w:.3f} -> {new_w:.3f} "
                    f"(precision={precision.get(engine, 0):.2f})"
                )

        result = CalibrationResult(
            old_weights=old_weights,
            new_weights=new_weights,
            engine_precision=precision,
            changes=changes,
            applied=False,
        )

        if not dry_run and changes:
            self._apply_weights(new_weights)
            self._log_calibration(result)
            result.applied = True

        return result

    def _load_current_weights(self) -> dict[str, float]:
        engines_path = self._config_dir / "engines.yaml"
        if not engines_path.exists():
            return {"topology": 0.35, "narrative": 0.30, "monoculture": 0.35}

        with open(engines_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return data.get("composite", {}).get("weights", {
            "topology": 0.35, "narrative": 0.30, "monoculture": 0.35,
        })

    def _compute_engine_precision(self) -> dict[str, float]:
        """Compute precision per engine from anomalies table (last 90 days).

        Precision = resolved anomalies / total anomalies per engine.
        """
        db_path = self._data_dir / "knowledge.db"
        if not db_path.exists():
            return {}

        conn = sqlite3.connect(str(db_path))
        try:
            rows = conn.execute(
                """SELECT engine,
                          COUNT(*) as total,
                          SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved
                   FROM anomalies
                   WHERE detected_at >= datetime('now', '-90 days')
                   GROUP BY engine"""
            ).fetchall()
        finally:
            conn.close()

        precision = {}
        for engine, total, resolved in rows:
            precision[engine] = resolved / total if total > 0 else 0.5

        # Default precision for engines with no data
        for engine in ["topology", "narrative", "monoculture"]:
            if engine not in precision:
                precision[engine] = 0.5

        return precision

    def _adjust_weights(
        self,
        old_weights: dict[str, float],
        precision: dict[str, float],
    ) -> dict[str, float]:
        """Adjust weights proportional to precision, bounded by MAX_CHANGE_RATIO."""
        if not precision:
            return dict(old_weights)

        total_precision = sum(precision.get(e, 0.5) for e in old_weights)
        if total_precision <= 0:
            return dict(old_weights)

        new_weights = {}
        for engine, old_w in old_weights.items():
            target_w = precision.get(engine, 0.5) / total_precision

            # Bound the change
            max_delta = old_w * self.MAX_CHANGE_RATIO
            delta = target_w - old_w
            delta = max(-max_delta, min(max_delta, delta))

            new_weights[engine] = max(0.05, old_w + delta)

        # Re-normalize to sum to 1
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: v / total for k, v in new_weights.items()}

        return new_weights

    def _apply_weights(self, new_weights: dict[str, float]) -> None:
        """Write new weights to engines.yaml."""
        engines_path = self._config_dir / "engines.yaml"
        if not engines_path.exists():
            return

        with open(engines_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if "composite" not in data:
            data["composite"] = {}
        data["composite"]["weights"] = {k: round(v, 4) for k, v in new_weights.items()}

        with open(engines_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _log_calibration(self, result: CalibrationResult) -> None:
        """Log the calibration to knowledge.db."""
        db_path = self._data_dir / "knowledge.db"
        if not db_path.exists():
            return

        conn = sqlite3.connect(str(db_path))
        try:
            for engine, new_w in result.new_weights.items():
                old_w = result.old_weights.get(engine, 0)
                conn.execute(
                    """INSERT INTO calibrations
                       (timestamp, engine, metric, old_value, new_value, reason, triggered_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now(timezone.utc).isoformat(),
                        engine,
                        "composite_weight",
                        old_w,
                        new_w,
                        f"Precision-based recalibration (precision={result.engine_precision.get(engine, 0):.2f})",
                        "calibrator",
                    ),
                )
            conn.commit()
        finally:
            conn.close()
