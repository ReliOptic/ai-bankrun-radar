"""Topology Engine: network-based systemic risk assessment.

Builds an exposure graph (nodes=entities, edges=exposure amounts),
computes vulnerability scores per node, and runs Monte Carlo cascade
simulations to estimate systemic loss.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np

from contagion_radar.core.config import TopologyConfig
from contagion_radar.core.types import RiskScore, Signal


@dataclass
class ExposureEdge:
    """A directed exposure between two entities."""
    source: str
    target: str
    amount_usd: float
    exposure_type: str = "general"


class TopologyEngine:
    """Computes network-based systemic risk scores."""

    def __init__(self, config: TopologyConfig):
        self._config = config
        self._graph = nx.DiGraph()

    def build_graph(self, edges: list[ExposureEdge]) -> None:
        """Build the exposure graph from edge data."""
        self._graph.clear()
        min_weight = self._config.graph.min_edge_weight_usd

        for edge in edges:
            if edge.amount_usd >= min_weight:
                self._graph.add_edge(
                    edge.source, edge.target,
                    weight=edge.amount_usd,
                    exposure_type=edge.exposure_type,
                )

    def compute(
        self,
        entity: str,
        metrics: dict[str, float] | None = None,
    ) -> RiskScore:
        """Compute topology risk score for an entity.

        Args:
            entity: entity ID to score
            metrics: optional dict of pre-computed metrics
                     (leverage, maturity_mismatch, concentration ratios)
        """
        signals: list[Signal] = []
        metrics = metrics or {}

        # Node vulnerability score
        vuln = self._vulnerability_score(entity, metrics)
        signals.extend(self._vulnerability_signals(entity, metrics))

        # Graph centrality
        centrality = self._centrality_score(entity)
        if centrality > 0.5:
            signals.append(Signal(
                metric="centrality",
                entity=entity,
                value=centrality,
                threshold=0.5,
                triggered=True,
                description=f"High network centrality: {centrality:.2f}",
            ))

        # Cascade risk (Monte Carlo)
        cascade_loss = self._cascade_simulation(entity)
        if cascade_loss > self._config.cascade.failure_threshold:
            signals.append(Signal(
                metric="cascade_loss",
                entity=entity,
                value=cascade_loss,
                threshold=self._config.cascade.failure_threshold,
                triggered=True,
                description=f"Cascade loss {cascade_loss:.1%} of network",
            ))

        # Combine: weighted sum of vulnerability + centrality + cascade
        score = 0.5 * vuln + 0.2 * centrality + 0.3 * cascade_loss
        score = float(np.clip(score, 0.0, 1.0))

        return RiskScore(engine="topology", value=score, signals=signals)

    def _vulnerability_score(self, entity: str, metrics: dict[str, float]) -> float:
        """Weighted vulnerability index from leverage, maturity mismatch, concentration."""
        vc = self._config.vulnerability
        leverage = metrics.get("leverage", 0.0)
        maturity = metrics.get("maturity_mismatch", 0.0)
        concentration = metrics.get("concentration", 0.0)

        # Centrality from graph
        if entity in self._graph:
            in_deg = self._graph.in_degree(entity, weight="weight")
            out_deg = self._graph.out_degree(entity, weight="weight")
            total_weight = sum(d["weight"] for _, _, d in self._graph.edges(data=True)) or 1
            graph_centrality = (in_deg + out_deg) / (2 * total_weight)
        else:
            graph_centrality = 0.0

        score = (
            vc.leverage_weight * min(leverage, 1.0)
            + vc.maturity_mismatch_weight * min(maturity, 1.0)
            + vc.concentration_weight * min(concentration, 1.0)
            + vc.centrality_weight * min(graph_centrality, 1.0)
        )
        return float(np.clip(score, 0.0, 1.0))

    def _vulnerability_signals(
        self, entity: str, metrics: dict[str, float]
    ) -> list[Signal]:
        signals = []
        for metric_name, threshold in [
            ("leverage", 0.5), ("maturity_mismatch", 0.5), ("concentration", 0.6)
        ]:
            val = metrics.get(metric_name, 0.0)
            if val > threshold:
                signals.append(Signal(
                    metric=metric_name,
                    entity=entity,
                    value=val,
                    threshold=threshold,
                    triggered=True,
                    description=f"{metric_name}: {val:.2f} > {threshold}",
                ))
        return signals

    def _centrality_score(self, entity: str) -> float:
        """Betweenness centrality normalized to [0,1]."""
        if entity not in self._graph or self._graph.number_of_nodes() < 2:
            return 0.0
        bc = nx.betweenness_centrality(self._graph, weight="weight")
        return float(bc.get(entity, 0.0))

    def _cascade_simulation(self, entity: str) -> float:
        """Monte Carlo cascade: shock entity, propagate failures, measure loss."""
        if entity not in self._graph or self._graph.number_of_nodes() < 2:
            return 0.0

        rng = np.random.default_rng(42)
        n_runs = self._config.cascade.simulation_runs
        shock = self._config.cascade.shock_magnitude_pct
        fail_thresh = self._config.cascade.failure_threshold
        total_nodes = self._graph.number_of_nodes()

        total_failed = 0
        for _ in range(n_runs):
            failed = {entity}
            queue = [entity]

            while queue:
                node = queue.pop(0)
                for _, neighbor, data in self._graph.edges(node, data=True):
                    if neighbor in failed:
                        continue
                    exposure = data["weight"]
                    # Probability of cascade depends on exposure + random shock
                    loss = shock * (1 + rng.standard_normal() * 0.2)
                    if loss > fail_thresh * 0.5:
                        failed.add(neighbor)
                        queue.append(neighbor)

            total_failed += len(failed) - 1  # exclude initial entity

        avg_failed = total_failed / n_runs
        return float(np.clip(avg_failed / max(total_nodes - 1, 1), 0.0, 1.0))
