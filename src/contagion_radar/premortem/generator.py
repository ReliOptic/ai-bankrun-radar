"""Pre-mortem Hypothesis Generator.

"If this institution fails tomorrow, why?"
Constructs a prompt from KB context + current FeatureVector,
calls OpenRouter, parses structured hypothesis output.
"""

from __future__ import annotations

import json
from typing import Any

from contagion_radar.core.types import DataSignal, FeatureVector, Hypothesis
from contagion_radar.reasoning.client import AIClient

SYSTEM_PROMPT = """You are a financial crisis analyst performing a pre-mortem analysis.

Given an entity and its current risk state, assume the entity has ALREADY FAILED.
Your job is to reason backward: what plausible chain of events caused the failure?

Generate structured hypotheses with:
1. A specific failure mode (e.g., "de_peg", "liquidity_crisis", "bank_run")
2. A causal chain (sequence of events leading to failure)
3. Estimated probability (0-1)
4. Observable data signals that would confirm the hypothesis is unfolding

You MUST respond with valid JSON matching this structure:
{
  "hypotheses": [
    {
      "failure_mode": "string",
      "cause_chain": ["event1", "event2", "event3"],
      "probability": 0.15,
      "data_signals": [
        {
          "metric": "metric_name",
          "entity": "entity_name",
          "threshold": 0.005,
          "direction": "above",
          "description": "what this signal means"
        }
      ]
    }
  ]
}

Consider: concentration risk, liquidity mismatch, narrative contagion, regulatory action,
counterparty failure, peg instability, smart contract risk, and governance failure.
"""


class PremortemGenerator:
    """Generates pre-mortem hypotheses via AI reasoning."""

    def __init__(self, ai_client: AIClient):
        self._client = ai_client

    async def generate(
        self,
        entity_id: str,
        feature_vector: FeatureVector | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Hypothesis]:
        """Generate hypotheses for an entity.

        Args:
            entity_id: entity to analyze
            feature_vector: current risk state
            context: additional KB context (past hypotheses, anomalies, etc.)
        """
        user_prompt = self._build_prompt(entity_id, feature_vector, context)

        response = await self._client.generate(
            system=SYSTEM_PROMPT,
            user=user_prompt,
        )

        return self._parse_response(entity_id, response)

    def generate_offline(
        self,
        entity_id: str,
        feature_vector: FeatureVector | None = None,
    ) -> list[Hypothesis]:
        """Generate rule-based hypotheses without AI (fallback/budget-exhausted).

        Returns generic hypotheses based on engine scores.
        """
        hypotheses = []

        if feature_vector is None:
            return hypotheses

        for engine_name, risk_score in feature_vector.engines.items():
            if risk_score.value < 0.3:
                continue

            signals = []
            for sig in risk_score.signals:
                signals.append(DataSignal(
                    metric=sig.metric,
                    entity=sig.entity,
                    threshold=sig.threshold,
                    direction="above" if sig.triggered else "below",
                    description=sig.description,
                ))

            failure_mode = {
                "topology": "concentration_failure",
                "narrative": "confidence_collapse",
                "monoculture": "herding_flash_crash",
            }.get(engine_name, "unknown")

            hypotheses.append(Hypothesis(
                entity_id=entity_id,
                failure_mode=failure_mode,
                cause_chain=[f"Elevated {engine_name} risk ({risk_score.value:.2f})"],
                probability=risk_score.value * 0.5,
                data_signals=signals,
                confidence=0.3,
                model_used="rule_based",
            ))

        return hypotheses

    def _build_prompt(
        self,
        entity_id: str,
        fv: FeatureVector | None,
        context: dict[str, Any] | None,
    ) -> str:
        parts = [f"Entity: {entity_id}"]

        if fv is not None:
            parts.append(f"Composite Score: {fv.composite:.3f}")
            for name, rs in fv.engines.items():
                top_signals = ", ".join(s.description for s in rs.signals[:3])
                parts.append(f"  {name}: {rs.value:.3f} [{top_signals}]")

            if fv.gp_run_probability is not None:
                parts.append(f"G&P P(run): {fv.gp_run_probability:.3f}")
            if fv.dd_f_critical is not None:
                parts.append(f"D&D f_critical: {fv.dd_f_critical:.3f}")

        if context:
            if "past_hypotheses" in context:
                parts.append(f"\nPast hypotheses: {json.dumps(context['past_hypotheses'][:5])}")
            if "recent_anomalies" in context:
                parts.append(f"Recent anomalies: {json.dumps(context['recent_anomalies'][:5])}")

        parts.append("\nAssume this entity has failed. Generate 2-3 hypotheses.")
        return "\n".join(parts)

    def _parse_response(
        self, entity_id: str, response: dict[str, Any]
    ) -> list[Hypothesis]:
        hypotheses = []
        raw_hyps = response.get("hypotheses", [])

        for raw in raw_hyps:
            signals = []
            for sig in raw.get("data_signals", []):
                signals.append(DataSignal(
                    metric=sig.get("metric", ""),
                    entity=sig.get("entity", entity_id),
                    threshold=float(sig.get("threshold", 0)),
                    direction=sig.get("direction", "above"),
                    description=sig.get("description", ""),
                ))

            hypotheses.append(Hypothesis(
                entity_id=entity_id,
                failure_mode=raw.get("failure_mode", "unknown"),
                cause_chain=raw.get("cause_chain", []),
                probability=float(raw.get("probability", 0.1)),
                data_signals=signals,
                confidence=0.5,
                model_used=self._client.model,
            ))

        return hypotheses
