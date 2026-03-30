"""Shannon Entropy and Monoculture Index.

Monoculture Index measures how concentrated market strategies are.
When all participants use the same strategy, the index approaches 1
(flash run precursor). When strategies are diverse, it approaches 0.
"""

from __future__ import annotations

import numpy as np


def shannon_entropy(distribution: list[float] | np.ndarray) -> float:
    """Compute Shannon entropy H(X) = -sum(p_i * log(p_i)).

    Args:
        distribution: probability distribution (must sum to ~1, non-negative).

    Returns:
        Shannon entropy in nats (natural log). Returns 0 for degenerate distributions.
    """
    dist = np.asarray(distribution, dtype=np.float64)

    if dist.size == 0:
        return 0.0

    # Normalize if not already
    total = dist.sum()
    if total <= 0:
        return 0.0
    dist = dist / total

    # Filter out zero entries to avoid log(0)
    nonzero = dist[dist > 0]
    return float(-np.sum(nonzero * np.log(nonzero)))


def monoculture_index(distribution: list[float] | np.ndarray) -> float:
    """Compute Monoculture Index = 1 - H(distribution) / H_max.

    H_max = log(k) where k is the number of strategy clusters.

    Index interpretation:
      0.0 = perfectly diverse (uniform distribution)
      1.0 = complete monoculture (single strategy dominates)

    Args:
        distribution: strategy weights across clusters.

    Returns:
        Monoculture index in [0, 1].
    """
    dist = np.asarray(distribution, dtype=np.float64)

    if dist.size <= 1:
        return 1.0

    k = dist.size
    h_max = np.log(k)

    if h_max == 0:
        return 1.0

    h = shannon_entropy(dist)
    index = 1.0 - h / h_max

    return float(np.clip(index, 0.0, 1.0))
