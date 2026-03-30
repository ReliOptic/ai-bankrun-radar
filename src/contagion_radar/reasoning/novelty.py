"""Novelty Assessment: compare current state against historical precedents.

If the current crisis pattern is unprecedented (low similarity to known precedents),
the novelty multiplier increases alert severity.
"""

from __future__ import annotations

import numpy as np

from contagion_radar.core.config import NoveltyMultiplierConfig
from contagion_radar.core.types import FeatureVector, NoveltyAssessment


def assess_novelty(
    current: FeatureVector,
    precedents: list[dict[str, float]],
    config: NoveltyMultiplierConfig | None = None,
) -> NoveltyAssessment:
    """Compare current feature vector against known precedent feature vectors.

    Args:
        current: current system state
        precedents: list of {name: str, features: dict[str, float]} precedent records
        config: novelty multiplier configuration

    Returns:
        NoveltyAssessment with multiplier, closest precedent, and similarity.
    """
    if config is None:
        config = NoveltyMultiplierConfig()

    current_vec = _extract_feature_vector(current)

    if not precedents or not current_vec:
        return NoveltyAssessment(
            multiplier=config.novel_multiplier,
            closest_precedent=None,
            similarity=0.0,
            reasoning="No precedents available for comparison",
        )

    best_sim = 0.0
    best_name = None

    for precedent in precedents:
        name = precedent.get("name", "unknown")
        features = precedent.get("features", {})
        if not features:
            continue

        sim = _cosine_similarity(current_vec, features)
        if sim > best_sim:
            best_sim = sim
            best_name = name

    # Map similarity to multiplier
    multiplier = _similarity_to_multiplier(best_sim, config)

    if best_sim > config.routine_max_similarity:
        reasoning = f"Similar to precedent '{best_name}' (sim={best_sim:.2f}), routine"
    elif best_sim > config.novel_max_similarity:
        reasoning = f"Moderate novelty vs '{best_name}' (sim={best_sim:.2f})"
    else:
        reasoning = f"Unprecedented pattern, low similarity to known precedents (sim={best_sim:.2f})"

    return NoveltyAssessment(
        multiplier=multiplier,
        closest_precedent=best_name,
        similarity=best_sim,
        reasoning=reasoning,
    )


def _extract_feature_vector(fv: FeatureVector) -> dict[str, float]:
    """Convert FeatureVector into a flat dict for comparison."""
    result = {"composite": fv.composite}

    for engine_name, risk_score in fv.engines.items():
        result[f"engine_{engine_name}"] = risk_score.value

    if fv.gp_run_probability is not None:
        result["gp_run_prob"] = fv.gp_run_probability
    if fv.dd_f_critical is not None:
        result["dd_f_critical"] = fv.dd_f_critical

    return result


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two feature dicts (shared keys only)."""
    shared = set(a.keys()) & set(b.keys())
    if not shared:
        return 0.0

    va = np.array([a[k] for k in shared])
    vb = np.array([b[k] for k in shared])

    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.clip(np.dot(va, vb) / (norm_a * norm_b), 0.0, 1.0))


def _similarity_to_multiplier(sim: float, config: NoveltyMultiplierConfig) -> float:
    """Map similarity score to novelty multiplier.

    High similarity (routine) → 1.0
    Low similarity (novel) → up to 1.5
    """
    if sim >= config.routine_max_similarity:
        return config.routine_multiplier

    if sim <= config.novel_max_similarity:
        return config.novel_multiplier

    # Linear interpolation between novel and routine
    t = (sim - config.novel_max_similarity) / (config.routine_max_similarity - config.novel_max_similarity)
    return config.novel_multiplier + t * (config.routine_multiplier - config.novel_multiplier)
