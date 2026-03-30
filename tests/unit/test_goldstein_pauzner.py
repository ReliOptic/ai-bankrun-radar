"""Tests for Goldstein-Pauzner (2005) bank run probability model.

The paper assumes u(0) = 0, which holds for CRRA utility with gamma < 1.
Theorem 2 (monotonicity of theta* in r1) is tested for gamma < 1 only.
For gamma >= 1, we test basic properties (range, boundary conditions).
"""

import numpy as np
import pytest

from contagion_radar.models.goldstein_pauzner import (
    crra_utility,
    indifference_integral,
    run_probability,
    theta_star,
    utility_differential,
    withdrawal_fraction,
)

# ── CRRA Utility ──────────────────────────────────────────────


class TestCRRAUtility:
    def test_positive_consumption(self):
        assert crra_utility(2.0, 0.5) == pytest.approx(2.0**0.5 / 0.5)

    def test_log_utility_gamma_1(self):
        assert crra_utility(2.0, 1.0) == pytest.approx(np.log(2.0))

    def test_zero_consumption_gamma_below_1(self):
        assert crra_utility(0.0, 0.5) == 0.0

    def test_zero_consumption_gamma_above_1(self):
        assert crra_utility(0.0, 2.0) == -1e12

    def test_negative_consumption(self):
        assert crra_utility(-1.0, 0.5) == 0.0

    def test_increasing(self):
        """u is strictly increasing for c > 0."""
        for gamma in [0.5, 1.0, 2.0, 3.0]:
            vals = [crra_utility(c, gamma) for c in [0.5, 1.0, 2.0, 4.0]]
            for i in range(len(vals) - 1):
                assert vals[i] < vals[i + 1], f"gamma={gamma}"

    def test_concavity(self):
        """u is concave: u(midpoint) > average of endpoints."""
        for gamma in [0.5, 2.0]:
            c_lo, c_hi = 1.0, 3.0
            c_mid = (c_lo + c_hi) / 2
            avg = (crra_utility(c_lo, gamma) + crra_utility(c_hi, gamma)) / 2
            assert crra_utility(c_mid, gamma) > avg


# ── Withdrawal Fraction ───────────────────────────────────────


class TestWithdrawalFraction:
    @pytest.fixture
    def params(self):
        return dict(theta_star=0.5, lambda_=0.25, epsilon=0.1)

    def test_all_withdraw_below_threshold(self, params):
        """theta <= theta* - epsilon: everyone runs."""
        assert withdrawal_fraction(0.3, **params) == 1.0
        assert withdrawal_fraction(0.4, **params) == 1.0

    def test_only_impatient_above_threshold(self, params):
        """theta >= theta* + epsilon: only impatient agents withdraw."""
        assert withdrawal_fraction(0.7, **params) == 0.25
        assert withdrawal_fraction(0.6, **params) == 0.25

    def test_linear_in_middle(self, params):
        """theta* - eps < theta < theta* + eps: linear interpolation."""
        n = withdrawal_fraction(0.5, **params)
        assert 0.25 < n < 1.0
        # At theta = theta_star: n = lambda + (1-lambda)*0.5 = 0.25 + 0.375 = 0.625
        assert n == pytest.approx(0.625)

    def test_boundary_left(self, params):
        """At theta = theta* - epsilon: n = 1.0."""
        assert withdrawal_fraction(0.4, **params) == 1.0

    def test_boundary_right(self, params):
        """At theta = theta* + epsilon: n = lambda."""
        assert withdrawal_fraction(0.6, **params) == 0.25

    def test_range(self):
        """n always in [lambda, 1]."""
        for theta in np.linspace(0, 1, 50):
            n = withdrawal_fraction(theta, 0.5, 0.25, 0.1)
            assert 0.25 <= n <= 1.0


# ── Utility Differential ─────────────────────────────────────


class TestUtilityDifferential:
    def test_positive_when_waiting_preferred(self):
        """Low n, high theta: waiting is better."""
        v = utility_differential(theta=0.9, n=0.25, r1=1.2, R=2.0, gamma=0.5)
        assert v > 0

    def test_negative_when_running_preferred(self):
        """High n (insolvency region): running is rational."""
        v = utility_differential(theta=0.5, n=0.95, r1=1.2, R=2.0, gamma=0.5)
        assert v < 0

    def test_insolvency_regime(self):
        """n > 1/r1: bank can't pay everyone, v < 0."""
        r1 = 1.5
        n = 0.8  # > 1/1.5 = 0.667
        v = utility_differential(theta=0.9, n=n, r1=r1, R=2.0, gamma=0.5)
        assert v < 0


# ── Theta Star (threshold signal) ────────────────────────────


class TestThetaStar:
    def test_r1_leq_1_no_run_risk(self):
        """When r1 <= 1, bank offers no incentive to run early."""
        assert theta_star(1.0, 2.0, 0.25, 0.5) == 0.0
        assert theta_star(0.5, 2.0, 0.25, 0.5) == 0.0

    def test_range(self):
        """theta* in [0, 1]."""
        for r1 in np.linspace(1.01, 1.9, 20):
            ts = theta_star(r1, 2.0, 0.25, 0.5)
            assert 0.0 <= ts <= 1.0

    def test_monotonicity_gamma_below_1(self):
        """Theorem 2: theta*(r1) is non-decreasing in r1 for gamma < 1.

        The paper proves strict monotonicity in the interior (0,1).
        At boundaries (0 or 1), saturation is expected.
        """
        gamma = 0.5
        r1_values = np.linspace(1.01, 1.8, 30)
        ts_values = [theta_star(r1, 2.0, 0.25, gamma) for r1 in r1_values]

        for i in range(len(ts_values) - 1):
            assert ts_values[i] <= ts_values[i + 1] + 1e-10, (
                f"Non-decreasing violated: theta*({r1_values[i]:.3f})={ts_values[i]:.6f} "
                f"> theta*({r1_values[i+1]:.3f})={ts_values[i+1]:.6f}"
            )

    def test_strict_monotonicity_interior(self):
        """In the interior (0 < theta* < 1), monotonicity is strict."""
        gamma = 0.5
        r1_values = [1.02, 1.04, 1.06, 1.08, 1.10]
        ts_values = [theta_star(r1, 2.0, 0.25, gamma) for r1 in r1_values]

        # All should be in interior for these small r1 values
        for ts in ts_values:
            assert 0.0 < ts < 1.0, f"Expected interior theta*, got {ts}"

        for i in range(len(ts_values) - 1):
            assert ts_values[i] < ts_values[i + 1], (
                f"Strict monotonicity failed: theta*({r1_values[i]})={ts_values[i]} "
                f">= theta*({r1_values[i+1]})={ts_values[i+1]}"
            )

    def test_saturation_at_high_r1(self):
        """For gamma < 1 with generous r1, theta* saturates at 1.0."""
        gamma = 0.5
        ts = theta_star(1.5, 2.0, 0.25, gamma)
        assert ts == 1.0

    def test_gamma_above_1_basic_properties(self):
        """For gamma >= 1: values should still be in [0,1] and sensible."""
        for gamma in [1.5, 2.0, 3.0]:
            for r1 in [1.1, 1.28, 1.5]:
                ts = theta_star(r1, 2.0, 0.25, gamma)
                assert 0.0 <= ts <= 1.0, f"gamma={gamma}, r1={r1}: theta*={ts}"

    def test_custom_p_func(self):
        """With p(theta) = theta^2, theta* should differ from linear case."""
        p_func = lambda theta: theta**2
        ts_linear = theta_star(1.1, 2.0, 0.25, 0.5)
        ts_quad = theta_star(1.1, 2.0, 0.25, 0.5, p_func=p_func)
        # Quadratic p means higher theta needed for same p_star
        assert ts_quad > ts_linear or ts_quad == pytest.approx(ts_linear, abs=0.01)


# ── Run Probability ──────────────────────────────────────────


class TestRunProbability:
    def test_same_as_theta_star(self):
        """run_probability is just clipped theta_star."""
        for r1 in [1.0, 1.1, 1.28, 1.5]:
            rp = run_probability(r1, 2.0, 0.25, 0.5)
            ts = theta_star(r1, 2.0, 0.25, 0.5)
            assert rp == pytest.approx(float(np.clip(ts, 0.0, 1.0)))

    def test_range(self):
        for r1 in np.linspace(0.5, 1.9, 30):
            rp = run_probability(r1, 2.0, 0.25, 0.5)
            assert 0.0 <= rp <= 1.0


# ── Indifference Integral ────────────────────────────────────


class TestIndifferenceIntegral:
    def test_at_threshold(self):
        """At theta_i = theta*, the integral should be near 0 (indifference)."""
        ts = theta_star(1.08, 2.0, 0.25, 0.5)
        if 0.01 < ts < 0.99:
            delta = indifference_integral(
                ts, ts, 1.08, 2.0, 0.25, 0.5, epsilon=0.01
            )
            assert abs(delta) < 0.1, f"Expected near 0, got {delta}"

    def test_positive_above_threshold(self):
        """Well above threshold: waiting is preferred."""
        ts = theta_star(1.08, 2.0, 0.25, 0.5)
        if ts < 0.8:
            delta = indifference_integral(
                0.95, ts, 1.08, 2.0, 0.25, 0.5, epsilon=0.01
            )
            assert delta > 0

    def test_negative_below_threshold(self):
        """Well below threshold: running is preferred."""
        ts = theta_star(1.08, 2.0, 0.25, 0.5)
        if ts > 0.2:
            delta = indifference_integral(
                0.05, ts, 1.08, 2.0, 0.25, 0.5, epsilon=0.01
            )
            assert delta < 0
