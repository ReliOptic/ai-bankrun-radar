"""Composite Scorer: combines engine scores into a FeatureVector.

Applies:
1. YAML-configured weights per engine
2. Data confidence discounts (OFFLINE → 0 contribution)
3. Cross-engine amplification (2+ engines elevated → ×1.5)
4. G&P run probability integration
"""

from __future__ import annotations

import numpy as np

from contagion_radar.core.config import CompositeConfig
from contagion_radar.core.types import DataConfidence, DataStatus, FeatureVector, RiskScore


class CompositeScorer:
    """Produces a FeatureVector from individual engine RiskScores."""

    def __init__(self, config: CompositeConfig):
        self._config = config

    def compute(
        self,
        scores: dict[str, RiskScore],
        confidences: dict[str, DataConfidence],
        gp_run_probability: float | None = None,
        dd_f_critical: float | None = None,
    ) -> FeatureVector:
        """Compute composite score from engine outputs.

        Args:
            scores: engine_name → RiskScore
            confidences: source_name → DataConfidence
            gp_run_probability: Goldstein-Pauzner P(run)
            dd_f_critical: Diamond-Dybvig tipping point
        """
        weights = self._config.weights
        threshold = self._config.cross_engine_threshold
        multiplier = self._config.cross_engine_multiplier

        # Compute discount per engine based on data quality
        discounts = self._compute_discounts(scores, confidences)

        # Weighted sum with data quality discounts
        weighted_sum = 0.0
        total_weight = 0.0
        elevated_count = 0

        for engine_name, risk_score in scores.items():
            w = weights.get(engine_name, 0.0)
            discount = discounts.get(engine_name, 1.0)
            effective_value = risk_score.value * discount
            weighted_sum += w * effective_value
            total_weight += w

            if effective_value > threshold:
                elevated_count += 1

        # Normalize
        if total_weight > 0:
            composite = weighted_sum / total_weight
        else:
            composite = 0.0

        # Cross-engine amplification: 2+ engines above threshold
        if elevated_count >= 2:
            composite *= multiplier

        # Integrate G&P run probability
        if gp_run_probability is not None:
            gp_weight = self._config.gp_run_probability_weight
            composite = (1 - gp_weight) * composite + gp_weight * gp_run_probability

        composite = float(np.clip(composite, 0.0, 1.0))

        data_quality = {}
        for source, conf in confidences.items():
            data_quality[source] = conf.status

        return FeatureVector(
            composite=composite,
            engines=scores,
            data_quality=data_quality,
            gp_run_probability=gp_run_probability,
            dd_f_critical=dd_f_critical,
        )

    def _compute_discounts(
        self,
        scores: dict[str, RiskScore],
        confidences: dict[str, DataConfidence],
    ) -> dict[str, float]:
        """Map engine → discount factor based on data confidence.

        Each engine may depend on multiple data sources. We take the minimum
        discount across its relevant sources.
        """
        # Simple mapping: engine name → sources that feed it
        engine_sources = {
            "topology": ["defillama", "etherscan"],
            "narrative": ["social", "news"],
            "monoculture": ["defillama", "yahoo_finance"],
        }

        _STATUS_DISCOUNTS = {
            DataStatus.FRESH: 1.0,
            DataStatus.STALE: 0.7,
            DataStatus.DEGRADED: 0.4,
            DataStatus.OFFLINE: 0.0,
        }

        discounts = {}
        for engine_name in scores:
            sources = engine_sources.get(engine_name, [])
            if not sources:
                discounts[engine_name] = 1.0
                continue

            relevant = [
                _STATUS_DISCOUNTS.get(confidences[s].status, 1.0)
                for s in sources
                if s in confidences
            ]
            discounts[engine_name] = min(relevant) if relevant else 1.0

        return discounts
