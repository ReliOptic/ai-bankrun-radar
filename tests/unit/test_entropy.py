"""Tests for Shannon Entropy and Monoculture Index."""

import numpy as np
import pytest

from contagion_radar.engines.monoculture.entropy import monoculture_index, shannon_entropy


class TestShannonEntropy:
    def test_uniform_distribution(self):
        """H(uniform_k) = log(k)."""
        k = 5
        dist = [1.0 / k] * k
        assert shannon_entropy(dist) == pytest.approx(np.log(k), abs=1e-10)

    def test_degenerate_distribution(self):
        """Single outcome: H = 0."""
        assert shannon_entropy([1.0]) == 0.0
        assert shannon_entropy([1.0, 0.0, 0.0]) == 0.0

    def test_binary_symmetric(self):
        """H([0.5, 0.5]) = log(2)."""
        assert shannon_entropy([0.5, 0.5]) == pytest.approx(np.log(2))

    def test_non_negative(self):
        """Entropy is always >= 0."""
        rng = np.random.default_rng(42)
        for _ in range(50):
            k = rng.integers(2, 20)
            dist = rng.dirichlet(np.ones(k))
            assert shannon_entropy(dist) >= -1e-10

    def test_empty(self):
        assert shannon_entropy([]) == 0.0

    def test_all_zeros(self):
        assert shannon_entropy([0.0, 0.0, 0.0]) == 0.0

    def test_auto_normalize(self):
        """Non-normalized input is normalized internally."""
        assert shannon_entropy([2, 2, 2]) == pytest.approx(np.log(3), abs=1e-10)


class TestMonocultureIndex:
    def test_uniform_is_zero(self):
        """Perfectly diverse: index = 0."""
        assert monoculture_index([0.25, 0.25, 0.25, 0.25]) == pytest.approx(0.0, abs=1e-10)

    def test_single_strategy_is_one(self):
        """Complete monoculture: index = 1."""
        assert monoculture_index([1.0, 0.0, 0.0]) == pytest.approx(1.0)

    def test_single_element(self):
        """Only one possible strategy: monoculture by definition."""
        assert monoculture_index([1.0]) == 1.0

    def test_range(self):
        """Index always in [0, 1]."""
        rng = np.random.default_rng(42)
        for _ in range(100):
            k = rng.integers(2, 20)
            dist = rng.dirichlet(np.ones(k))
            idx = monoculture_index(dist)
            assert 0.0 <= idx <= 1.0 + 1e-10

    def test_more_concentrated_is_higher(self):
        """More concentrated distribution → higher index."""
        diverse = monoculture_index([0.25, 0.25, 0.25, 0.25])
        moderate = monoculture_index([0.7, 0.1, 0.1, 0.1])
        concentrated = monoculture_index([0.97, 0.01, 0.01, 0.01])
        assert diverse < moderate < concentrated
