"""Monoculture Engine: strategy concentration risk assessment.

Combines entropy-based monoculture index with signal correlation
analysis to detect herding behavior (flash run precursor).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from contagion_radar.core.config import MonocultureConfig
from contagion_radar.core.types import RiskScore, Signal
from contagion_radar.engines.monoculture.entropy import monoculture_index


class MonocultureEngine:
    """Detects strategy concentration and herding behavior."""

    def __init__(self, config: MonocultureConfig):
        self._config = config

    def compute(
        self,
        entity: str,
        strategy_distribution: list[float] | np.ndarray | None = None,
        price_series: dict[str, list[float]] | None = None,
    ) -> RiskScore:
        """Compute monoculture risk score.

        Args:
            entity: entity to score
            strategy_distribution: weights across strategy clusters
            price_series: dict of asset_name → price time series for correlation
        """
        signals: list[Signal] = []

        # Monoculture index from strategy distribution
        mono_score = 0.0
        if strategy_distribution is not None:
            dist = np.asarray(strategy_distribution, dtype=np.float64)
            if dist.sum() > 0:
                mono_score = monoculture_index(dist)
                if mono_score > self._config.entropy.index_alert_threshold:
                    signals.append(Signal(
                        metric="monoculture_index",
                        entity=entity,
                        value=mono_score,
                        threshold=self._config.entropy.index_alert_threshold,
                        triggered=True,
                        description=f"Monoculture index {mono_score:.2f} (high concentration)",
                    ))

        # Cross-asset correlation
        corr_score = 0.0
        if price_series and len(price_series) >= 2:
            corr_score = self._correlation_score(price_series)
            if corr_score > self._config.correlation.high_correlation_threshold:
                signals.append(Signal(
                    metric="cross_correlation",
                    entity=entity,
                    value=corr_score,
                    threshold=self._config.correlation.high_correlation_threshold,
                    triggered=True,
                    description=f"High cross-asset correlation: {corr_score:.2f}",
                ))

        # Combined score: 60% monoculture index + 40% correlation
        score = 0.6 * mono_score + 0.4 * corr_score
        score = float(np.clip(score, 0.0, 1.0))

        return RiskScore(engine="monoculture", value=score, signals=signals)

    def _correlation_score(self, price_series: dict[str, list[float]]) -> float:
        """Compute average pairwise correlation across price series."""
        names = list(price_series.keys())
        if len(names) < 2:
            return 0.0

        # Align to shortest series
        min_len = min(len(price_series[n]) for n in names)
        if min_len < 10:
            return 0.0

        # Build matrix of returns
        returns = []
        for name in names:
            prices = np.array(price_series[name][-min_len:], dtype=np.float64)
            # Log returns
            valid = prices[:-1] > 0
            if not valid.all():
                continue
            ret = np.diff(np.log(prices))
            returns.append(ret)

        if len(returns) < 2:
            return 0.0

        # Correlation matrix
        corr_matrix = np.corrcoef(returns)
        n = len(returns)

        # Average off-diagonal correlation
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                if not np.isnan(corr_matrix[i, j]):
                    total += abs(corr_matrix[i, j])
                    count += 1

        return total / count if count > 0 else 0.0
