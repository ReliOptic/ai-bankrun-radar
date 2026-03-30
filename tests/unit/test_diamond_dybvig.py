"""Tests for Diamond-Dybvig (1983) liquidity model."""

import pytest

from contagion_radar.models.diamond_dybvig import (
    EquilibriaResult,
    equilibria,
    f_critical,
    optimal_r1,
    r2_given_f,
)


class TestFCritical:
    def test_paper_value(self):
        """f_critical(1.28, 2.0) = 0.5625 — matches paper example."""
        assert f_critical(1.28, 2.0) == pytest.approx(0.5625)

    def test_range(self):
        """f_critical in (0, 1) for valid parameters."""
        for r1 in [1.05, 1.2, 1.5, 1.8]:
            for R in [1.5, 2.0, 3.0]:
                if r1 < R:
                    fc = f_critical(r1, R)
                    assert 0.0 < fc < 1.0, f"r1={r1}, R={R}: fc={fc}"

    def test_decreasing_in_r1(self):
        """Higher r1 → lower tipping point (more fragile)."""
        fc_low = f_critical(1.1, 2.0)
        fc_high = f_critical(1.5, 2.0)
        assert fc_low > fc_high

    def test_r_must_exceed_1(self):
        with pytest.raises(ValueError, match="R must be > 1"):
            f_critical(1.2, 1.0)

    def test_r1_must_be_positive(self):
        with pytest.raises(ValueError, match="r1 must be > 0"):
            f_critical(0.0, 2.0)


class TestR2GivenF:
    def test_no_withdrawals(self):
        """f=0: patient agents get full R."""
        assert r2_given_f(0.0, 1.2, 2.0) == pytest.approx(2.0)

    def test_at_tipping_point(self):
        """At f=f_critical, r2 = r1."""
        r1, R = 1.28, 2.0
        fc = f_critical(r1, R)
        assert r2_given_f(fc, r1, R) == pytest.approx(r1, abs=1e-6)

    def test_all_withdraw(self):
        """f=1: bank is bankrupt, r2 = 0."""
        assert r2_given_f(1.0, 1.2, 2.0) == 0.0

    def test_above_tipping(self):
        """f > f_critical: r2 < r1."""
        r1, R = 1.28, 2.0
        fc = f_critical(r1, R)
        r2 = r2_given_f(fc + 0.1, r1, R)
        assert r2 < r1

    def test_below_tipping(self):
        """f < f_critical: r2 > r1."""
        r1, R = 1.28, 2.0
        fc = f_critical(r1, R)
        r2 = r2_given_f(fc - 0.1, r1, R)
        assert r2 > r1


class TestEquilibria:
    def test_viable_bank(self):
        result = equilibria(1.28, 2.0, 0.25)
        assert result.is_viable
        assert result.good_equilibrium_f == 0.25
        assert result.good_equilibrium_r2 > 1.28
        assert result.bad_equilibrium_f == 1.0
        assert result.bad_equilibrium_r2 == 0.0
        assert 0 < result.tipping_point_f < 1

    def test_non_viable_bank(self):
        """r1 too high relative to R: bank can't sustain even good equilibrium."""
        result = equilibria(1.9, 2.0, 0.5)
        assert not result.is_viable

    def test_result_type(self):
        result = equilibria(1.28, 2.0, 0.25)
        assert isinstance(result, EquilibriaResult)
        assert isinstance(result.description, str)
        assert len(result.description) > 0


class TestOptimalR1:
    def test_exceeds_1(self):
        """Optimal r1 > 1 (insurance value)."""
        r1 = optimal_r1(2.0, 0.25, gamma=2.0)
        assert r1 > 1.0

    def test_below_R(self):
        """Optimal r1 < R (can't promise more than long-term return)."""
        r1 = optimal_r1(2.0, 0.25, gamma=2.0)
        assert r1 < 2.0

    def test_higher_risk_aversion(self):
        """Higher gamma → higher r1 (more insurance desired)."""
        r1_low = optimal_r1(2.0, 0.25, gamma=1.5)
        r1_high = optimal_r1(2.0, 0.25, gamma=3.0)
        assert r1_high > r1_low
