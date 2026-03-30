"""Diamond-Dybvig (1983) liquidity model.

Implements the tipping point formula, residual payment calculation,
and multiple equilibria analysis from "Bank Runs, Deposit Insurance,
and Liquidity".

Reference: Journal of Political Economy, Vol. 91, No. 3, June 1983.
"""

from __future__ import annotations

from dataclasses import dataclass


def f_critical(r1: float, R: float) -> float:
    """Tipping point: fraction of withdrawals that triggers a bank run.

    f_critical = (R - r1) / (r1 * (R - 1))

    When expected withdrawal fraction exceeds f_critical, the remaining
    payment r2 drops below r1, making it rational for all agents to run.

    Args:
        r1: short-term payment offered by the bank (r1 > 1)
        R:  long-term return on investment (R > 1)

    Returns:
        Critical withdrawal fraction in (0, 1).

    Example:
        >>> f_critical(1.28, 2.0)
        0.5625
    """
    if R <= 1.0:
        raise ValueError(f"R must be > 1, got {R}")
    if r1 <= 0.0:
        raise ValueError(f"r1 must be > 0, got {r1}")
    return (R - r1) / (r1 * (R - 1))


def r2_given_f(f: float, r1: float, R: float) -> float:
    """Residual payment to patient agents given withdrawal fraction f.

    r2(f) = (1 - f * r1) * R / (1 - f)

    When f < f_critical: r2 > r1 (patient agents prefer to wait)
    When f > f_critical: r2 < r1 (patient agents prefer to run)
    When f = 1: bank is bankrupt (r2 undefined)

    Args:
        f:  fraction of agents withdrawing in period 1
        r1: short-term payment
        R:  long-term return

    Returns:
        Payment to remaining agents in period 2.
    """
    if abs(f - 1.0) < 1e-12:
        return 0.0
    numerator = (1 - f * r1) * R
    denominator = 1 - f
    if numerator < 0:
        return 0.0
    return numerator / denominator


@dataclass
class EquilibriaResult:
    """Analysis of multiple equilibria in the D&D model."""
    good_equilibrium_f: float
    good_equilibrium_r2: float
    bad_equilibrium_f: float
    bad_equilibrium_r2: float
    tipping_point_f: float
    is_viable: bool
    description: str


def equilibria(r1: float, R: float, lambda_: float) -> EquilibriaResult:
    """Analyze good/bad equilibria and the tipping point.

    Good equilibrium: only impatient agents withdraw (f = lambda)
    Bad equilibrium:  everyone withdraws (f = 1, bank fails)
    Tipping point:    f_critical where r2 = r1

    Args:
        r1:      short-term payment (r1 > 1)
        R:       long-term return (R > 1)
        lambda_: fraction of impatient agents (0 < lambda < 1)
    """
    fc = f_critical(r1, R)
    good_r2 = r2_given_f(lambda_, r1, R)
    bad_r2 = r2_given_f(1.0, r1, R)

    is_viable = good_r2 > r1 and lambda_ < fc

    desc_parts = []
    if is_viable:
        desc_parts.append(
            f"Good equilibrium: f={lambda_:.2f}, r2={good_r2:.3f} > r1={r1:.2f} (stable)"
        )
        desc_parts.append(
            f"Tipping point: f_critical={fc:.4f}"
        )
        desc_parts.append(
            f"Bad equilibrium: f=1.0, r2={bad_r2:.3f} (bank failure)"
        )
    else:
        desc_parts.append(
            f"Bank not viable: good_r2={good_r2:.3f} <= r1={r1:.2f} "
            f"or lambda={lambda_:.2f} >= f_critical={fc:.4f}"
        )

    return EquilibriaResult(
        good_equilibrium_f=lambda_,
        good_equilibrium_r2=good_r2,
        bad_equilibrium_f=1.0,
        bad_equilibrium_r2=bad_r2,
        tipping_point_f=fc,
        is_viable=is_viable,
        description="\n".join(desc_parts),
    )


def optimal_r1(R: float, lambda_: float, gamma: float = 2.0) -> float:
    """First-best r1 from equating marginal utilities.

    Under CRRA utility u(c) = c^(1-gamma)/(1-gamma):
    u'(r1) = R * u'(r2) where r2 = (1-lambda*r1)/(1-lambda) * R

    This gives the risk-sharing optimum ignoring run risk.
    """
    from scipy.optimize import brentq

    def foc(r1_val: float) -> float:
        if r1_val <= 0 or r1_val >= 1.0 / lambda_:
            return float("inf")
        r2 = (1 - lambda_ * r1_val) / (1 - lambda_) * R
        if r2 <= 0:
            return float("inf")
        return r1_val ** (-gamma) - R * r2 ** (-gamma)

    try:
        return brentq(foc, 1.0 + 1e-6, min(1.0 / lambda_ - 1e-6, R - 1e-6))
    except ValueError:
        return 1.0
