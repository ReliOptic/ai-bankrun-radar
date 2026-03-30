"""Rule Engine main loop.

Orchestrates: data fetch → quality check → 3 engines → composite scorer → FeatureVector.
One tick() call = one complete cycle. No AI calls — pure rule-based, deterministic, cost 0.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from contagion_radar.core.config import RadarConfig
from contagion_radar.core.types import DataConfidence, DataStatus, FeatureVector, RiskScore
from contagion_radar.data.adapters.base import AdapterError, DataAdapter
from contagion_radar.data.quality_gate import DataQualityGate
from contagion_radar.engines.monoculture.engine import MonocultureEngine
from contagion_radar.engines.narrative.engine import NarrativeEngine
from contagion_radar.engines.topology.engine import TopologyEngine
from contagion_radar.models.diamond_dybvig import f_critical
from contagion_radar.models.goldstein_pauzner import run_probability
from contagion_radar.rule_engine.composite import CompositeScorer


class RuleEngine:
    """Deterministic rule engine. One tick() = one full scan cycle."""

    def __init__(
        self,
        config: RadarConfig,
        adapters: dict[str, DataAdapter] | None = None,
        quality_gate: DataQualityGate | None = None,
    ):
        self._config = config
        self._adapters = adapters or {}
        self._gate = quality_gate or DataQualityGate(config.quality_gate)

        self._topology = TopologyEngine(config.engines.topology)
        self._narrative = NarrativeEngine(config.engines.narrative)
        self._monoculture = MonocultureEngine(config.engines.monoculture)
        self._composite = CompositeScorer(config.engines.composite)

        self._last_feature_vector: FeatureVector | None = None

    @property
    def last_feature_vector(self) -> FeatureVector | None:
        return self._last_feature_vector

    async def tick(
        self,
        entity: str,
        data: dict[str, Any] | None = None,
    ) -> FeatureVector:
        """Execute one scan cycle.

        Args:
            entity: entity to scan
            data: optional pre-fetched data dict (for testing/backtest).
                  If None, fetches from adapters.
        """
        if data is None:
            data, confidences = await self._fetch_all(entity)
        else:
            confidences = {
                source: DataConfidence(source=source, status=DataStatus.FRESH)
                for source in ["defillama", "etherscan", "yahoo_finance", "social", "news"]
            }

        # Run engines
        topology_score = self._run_topology(entity, data)
        narrative_score = self._run_narrative(entity, data)
        monoculture_score = self._run_monoculture(entity, data)

        scores = {
            "topology": topology_score,
            "narrative": narrative_score,
            "monoculture": monoculture_score,
        }

        # Math model outputs
        gp_prob = self._compute_gp_probability(data)
        dd_fc = self._compute_dd_fcritical(data)

        # Composite
        fv = self._composite.compute(
            scores=scores,
            confidences=confidences,
            gp_run_probability=gp_prob,
            dd_f_critical=dd_fc,
        )

        self._last_feature_vector = fv
        return fv

    async def _fetch_all(
        self, entity: str
    ) -> tuple[dict[str, Any], dict[str, DataConfidence]]:
        """Fetch from all adapters and assess quality."""
        all_data: dict[str, Any] = {}
        confidences: dict[str, DataConfidence] = {}
        now = datetime.utcnow()

        for source_name, adapter in self._adapters.items():
            try:
                fetched, _ = await adapter.fetch(entity)
                confidence = self._gate.assess(source_name, fetched, now)
                all_data[source_name] = fetched
            except AdapterError:
                confidence = self._gate.assess(source_name, {}, now, error=True)
                all_data[source_name] = {}

            confidences[source_name] = confidence

        return all_data, confidences

    def _run_topology(self, entity: str, data: dict[str, Any]) -> RiskScore:
        metrics = data.get("topology_metrics", {})
        edges = data.get("exposure_edges", [])

        if edges:
            from contagion_radar.engines.topology.engine import ExposureEdge
            edge_objs = [ExposureEdge(**e) if isinstance(e, dict) else e for e in edges]
            self._topology.build_graph(edge_objs)

        return self._topology.compute(entity, metrics=metrics)

    def _run_narrative(self, entity: str, data: dict[str, Any]) -> RiskScore:
        documents = data.get("documents", [])
        historical = data.get("historical_narrative_counts")
        return self._narrative.compute(entity, documents, historical)

    def _run_monoculture(self, entity: str, data: dict[str, Any]) -> RiskScore:
        strategy_dist = data.get("strategy_distribution")
        price_series = data.get("price_series")
        return self._monoculture.compute(entity, strategy_dist, price_series)

    def _compute_gp_probability(self, data: dict[str, Any]) -> float | None:
        r1 = data.get("r1")
        if r1 is None:
            gp = self._config.engines.models.goldstein_pauzner
            r1 = 1.0 + data.get("deposit_rate", 0.05)

        gp_config = self._config.engines.models.goldstein_pauzner
        try:
            return run_probability(
                r1=r1,
                R=gp_config.R,
                lambda_=gp_config.lambda_,
                gamma=gp_config.risk_aversion,
            )
        except Exception:
            return None

    def _compute_dd_fcritical(self, data: dict[str, Any]) -> float | None:
        r1 = data.get("r1")
        if r1 is None:
            r1 = 1.0 + data.get("deposit_rate", 0.05)

        dd_config = self._config.engines.models.diamond_dybvig
        try:
            return f_critical(r1=r1, R=dd_config.R)
        except (ValueError, ZeroDivisionError):
            return None
