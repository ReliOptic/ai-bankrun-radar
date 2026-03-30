"""Narrative Engine: text-based crisis signal detection.

Classifies text into crisis categories, computes narrative momentum
(spread velocity x algo sensitivity x 1/liquidity), and measures
the lag between narrative emergence and market reaction.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import numpy as np

from contagion_radar.core.config import NarrativeConfig
from contagion_radar.core.types import RiskScore, Signal

# Crisis keyword patterns (compiled regexes)
_CATEGORY_PATTERNS: dict[str, list[re.Pattern]] = {
    "bank_run": [
        re.compile(r"\bbank\s*run\b", re.I),
        re.compile(r"\brunning\s+on\s+the\s+bank\b", re.I),
        re.compile(r"\bwithdraw(?:al|ing)?\s+(?:all|everything|funds)\b", re.I),
        re.compile(r"\bqueue(?:ing|s)?\s+(?:at|outside)\b", re.I),
    ],
    "de_peg": [
        re.compile(r"\bde[- ]?peg\b", re.I),
        re.compile(r"\blost?\s+(?:its?\s+)?peg\b", re.I),
        re.compile(r"\bpeg\s+(?:break|broken|lost|slip)\b", re.I),
        re.compile(r"\bbelow\s+\$?0\.9[0-9]\b", re.I),
    ],
    "liquidity_crisis": [
        re.compile(r"\bliquidity\s+crisis\b", re.I),
        re.compile(r"\bliquidity\s+(?:crunch|squeeze|dry|dried)\b", re.I),
        re.compile(r"\bno\s+liquidity\b", re.I),
        re.compile(r"\bredemption\s+(?:halt|freeze|suspend)\b", re.I),
    ],
    "contagion": [
        re.compile(r"\bcontagion\b", re.I),
        re.compile(r"\bspill\s*over\b", re.I),
        re.compile(r"\bdomino\s+effect\b", re.I),
        re.compile(r"\bsystemic\s+risk\b", re.I),
    ],
    "confidence_loss": [
        re.compile(r"\bloss\s+of\s+confidence\b", re.I),
        re.compile(r"\btrust\s+(?:lost|broken|eroded)\b", re.I),
        re.compile(r"\bpanic\s+sell\b", re.I),
        re.compile(r"\bcapitulat\w+\b", re.I),
    ],
    "regulatory_action": [
        re.compile(r"\b(?:SEC|CFTC|DOJ|FBI)\s+(?:sue|charge|investigat)\b", re.I),
        re.compile(r"\bregulatory\s+(?:action|crackdown|enforcement)\b", re.I),
        re.compile(r"\bfraud\s+(?:charge|allegation)\b", re.I),
        re.compile(r"\bseiz(?:e|ed|ure)\b", re.I),
    ],
}


class NarrativeEngine:
    """Detects and quantifies crisis narratives from text data."""

    def __init__(self, config: NarrativeConfig):
        self._config = config

    def compute(
        self,
        entity: str,
        documents: list[dict[str, Any]],
        historical_counts: dict[str, list[float]] | None = None,
    ) -> RiskScore:
        """Compute narrative risk score for an entity.

        Args:
            entity: entity to score
            documents: list of dicts with "text", "timestamp", optional "score"
            historical_counts: per-category historical mention counts for baseline
        """
        signals: list[Signal] = []

        # Classify documents
        category_counts = self._classify_documents(documents, entity)
        total_mentions = sum(category_counts.values())

        # Narrative momentum per category
        momentum_scores = {}
        for category, count in category_counts.items():
            if count == 0:
                continue

            baseline = 1.0
            if historical_counts and category in historical_counts:
                hist = historical_counts[category]
                baseline = max(np.mean(hist) if hist else 1.0, 1.0)

            velocity = count / baseline
            momentum_scores[category] = min(velocity / self._config.momentum.alert_threshold, 1.0)

            if velocity >= self._config.momentum.alert_threshold:
                signals.append(Signal(
                    metric=f"narrative_{category}",
                    entity=entity,
                    value=velocity,
                    threshold=self._config.momentum.alert_threshold,
                    triggered=True,
                    description=f'"{category}" mentions {velocity:.1f}x baseline',
                ))

        # Overall narrative risk
        if momentum_scores:
            score = float(np.clip(max(momentum_scores.values()), 0.0, 1.0))
        elif total_mentions > 0:
            score = min(total_mentions / 50.0, 0.3)
        else:
            score = 0.0

        # Volume signal
        if total_mentions > 20:
            signals.append(Signal(
                metric="mention_volume",
                entity=entity,
                value=float(total_mentions),
                threshold=20.0,
                triggered=True,
                description=f"{total_mentions} crisis-related mentions",
            ))

        return RiskScore(engine="narrative", value=score, signals=signals)

    def _classify_documents(
        self, documents: list[dict[str, Any]], entity: str
    ) -> dict[str, int]:
        """Count documents matching each crisis category."""
        counts = {cat: 0 for cat in _CATEGORY_PATTERNS}

        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue

            # Only count if entity is mentioned (or entity filter not needed)
            entity_lower = entity.lower()
            if entity_lower not in text.lower() and len(documents) > 10:
                continue

            for category, patterns in _CATEGORY_PATTERNS.items():
                if any(p.search(text) for p in patterns):
                    counts[category] += 1

        return counts

    def classify_text(self, text: str) -> list[str]:
        """Classify a single text into crisis categories. Returns matched categories."""
        matched = []
        for category, patterns in _CATEGORY_PATTERNS.items():
            if any(p.search(text) for p in patterns):
                matched.append(category)
        return matched
