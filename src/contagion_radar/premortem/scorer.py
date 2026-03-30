"""Hypothesis confidence scorer with Bayesian updating.

Updates hypothesis confidence as new evidence arrives.
"""

from __future__ import annotations

from datetime import datetime

from contagion_radar.core.types import Evidence, Hypothesis


def update_confidence(
    hypothesis: Hypothesis,
    metric: str,
    observed_value: float,
    expected_direction: str,
    likelihood_ratio: float = 2.0,
) -> Hypothesis:
    """Bayesian update of hypothesis confidence given new evidence.

    Args:
        hypothesis: the hypothesis to update
        metric: which metric was observed
        observed_value: the observed value
        expected_direction: "above" or "below" threshold
        likelihood_ratio: how much more likely this evidence is if hypothesis is true
                         vs false (default 2.0)

    Returns:
        Updated hypothesis (mutated in-place and returned).
    """
    # Find matching data signal
    matching_signal = None
    for sig in hypothesis.data_signals:
        if sig.metric == metric:
            matching_signal = sig
            break

    if matching_signal is None:
        return hypothesis

    # Check if evidence supports hypothesis
    if expected_direction == "above":
        actual_direction = "above" if observed_value > matching_signal.threshold else "below"
    else:
        actual_direction = "below" if observed_value < matching_signal.threshold else "above"

    supports = (actual_direction == expected_direction)

    evidence = Evidence(
        timestamp=datetime.utcnow(),
        metric=metric,
        observed_value=observed_value,
        expected_direction=expected_direction,
        actual_direction=actual_direction,
        supports=supports,
    )

    if supports:
        hypothesis.evidence_for.append(evidence)
    else:
        hypothesis.evidence_against.append(evidence)

    # Bayesian update: P(H|E) = P(E|H)*P(H) / [P(E|H)*P(H) + P(E|~H)*P(~H)]
    prior = hypothesis.confidence
    if supports:
        posterior = (likelihood_ratio * prior) / (likelihood_ratio * prior + (1 - prior))
    else:
        inv_lr = 1.0 / likelihood_ratio
        posterior = (inv_lr * prior) / (inv_lr * prior + (1 - prior))

    posterior = max(0.01, min(0.99, posterior))
    hypothesis.confidence = posterior

    ts_str = datetime.utcnow().isoformat()
    hypothesis.confidence_trajectory.append((ts_str, posterior))

    return hypothesis
