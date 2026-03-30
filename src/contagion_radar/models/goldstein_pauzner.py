"""Goldstein-Pauzner (2005) bank run probability model.

Implements the unique equilibrium threshold signal theta*(r1),
withdrawal fraction n(theta, theta*), and utility differential v(theta, n)
from "Demand-Deposit Contracts and the Probability of Bank Runs".

Reference: Journal of Finance, Vol. LX, No. 3, June 2005.

Note: The paper assumes u(0) = 0 and u strictly increasing/concave.
We use CRRA utility u(c) = c^(1-gamma)/(1-gamma).
For gamma < 1, u(0) = 0 (well-behaved).
For gamma >= 1, numerical regularization is applied near singularities.
"""

from __future__ import annotations

import warnings

import numpy as np
from scipy import integrate, optimize


def crra_utility(c: float, gamma: float) -> float:
    """CRRA utility function u(c) = c^(1-gamma) / (1-gamma), gamma != 1."""
    if c <= 0:
        return -1e12 if gamma >= 1 else 0.0
    if abs(gamma - 1.0) < 1e-10:
        return np.log(c)
    return c ** (1 - gamma) / (1 - gamma)


def withdrawal_fraction(
    theta: float,
    theta_star: float,
    lambda_: float,
    epsilon: float,
) -> float:
    """Eq(2) / Corollary 1: proportion of agents demanding early withdrawal.

    n(theta, theta*) is piecewise linear:
      - n = 1                                              if theta <= theta* - epsilon
      - n = lambda + (1-lambda)*(theta*+eps-theta)/(2*eps) if theta*-eps < theta < theta*+eps
      - n = lambda                                         if theta >= theta* + epsilon
    """
    if theta <= theta_star - epsilon:
        return 1.0
    elif theta >= theta_star + epsilon:
        return lambda_
    else:
        return lambda_ + (1 - lambda_) * (theta_star + epsilon - theta) / (2 * epsilon)


def utility_differential(
    theta: float,
    n: float,
    r1: float,
    R: float,
    gamma: float,
    p_func: callable | None = None,
) -> float:
    """Eq(3): patient agent's net incentive to wait vs withdraw.

    v(theta, n) =
      p(theta)*u((1-n*r1)/(1-n) * R) - u(r1)    if lambda <= n <= 1/r1
      -(1/(n*r1)) * u(r1)                         if 1/r1 < n <= 1

    Positive = waiting preferred. Negative = running preferred.
    """
    p_theta = p_func(theta) if p_func is not None else theta

    u_r1 = crra_utility(r1, gamma)

    if n >= 1.0 / r1:
        if n <= 0 or r1 <= 0:
            return -abs(u_r1)
        return -(1.0 / (n * r1)) * u_r1
    else:
        if abs(n - 1.0) < 1e-12:
            return -u_r1
        c2 = (1 - n * r1) / (1 - n) * R
        if c2 <= 0:
            return -abs(u_r1)
        return p_theta * crra_utility(c2, gamma) - u_r1


def theta_star(
    r1: float,
    R: float,
    lambda_: float,
    gamma: float,
    p_func: callable | None = None,
) -> float:
    """Eq(5): compute threshold signal theta* at limit epsilon -> 0.

    The indifference condition at the limit (posterior of n uniform on [lambda,1]):
      integral[lambda to 1] v(theta*, n) dn = 0

    Solving for p(theta*):
      p(theta*) = u(r1)*[1/r1 - lambda + ln(r1)/r1] / integral[lambda to 1/r1] u(c2(n)) dn

    If p_func is None, p(theta) = theta, so theta* = p_inverse(ratio).
    """
    if r1 <= 1.0:
        return 0.0  # no run risk when r1 <= autarkic level

    u_r1 = crra_utility(r1, gamma)
    inv_r1 = 1.0 / r1

    # Numerator: the "cost of running" side
    # = u(r1) * (1/r1 - lambda) + u(r1)/r1 * ln(r1)
    # = u(r1) * (1/r1 - lambda + ln(r1)/r1)
    numerator = u_r1 * (inv_r1 - lambda_ + np.log(r1) / r1)

    # Denominator: integral of u(c2(n)) for n in [lambda, 1/r1]
    # c2(n) = (1 - n*r1)/(1 - n) * R
    # Regularize: integrate up to 1/r1 - small_delta to avoid c2=0 singularity
    upper_limit = inv_r1 - 1e-8

    if upper_limit <= lambda_:
        return 0.0

    def integrand(n: float) -> float:
        c2 = (1 - n * r1) / (1 - n) * R
        if c2 <= 1e-15:
            return 0.0
        return crra_utility(c2, gamma)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        integral_wait, _ = integrate.quad(
            integrand, lambda_, upper_limit,
            limit=100, epsabs=1e-10, epsrel=1e-10,
        )

    if abs(integral_wait) < 1e-15:
        return 0.0

    p_star = numerator / integral_wait
    p_star = float(np.clip(p_star, 0.0, 1.0))

    if p_func is None:
        return p_star
    else:
        def eq(th: float) -> float:
            return p_func(th) - p_star
        try:
            return optimize.brentq(eq, 0.0, 1.0)
        except ValueError:
            return p_star


def run_probability(
    r1: float,
    R: float,
    lambda_: float,
    gamma: float,
    p_func: callable | None = None,
) -> float:
    """Probability of a bank run = theta*(r1) for uniform theta on [0,1].

    Higher theta* means runs occur in a wider range of fundamentals.
    """
    ts = theta_star(r1, R, lambda_, gamma, p_func)
    return float(np.clip(ts, 0.0, 1.0))


def indifference_integral(
    theta_i: float,
    theta_threshold: float,
    r1: float,
    R: float,
    lambda_: float,
    gamma: float,
    epsilon: float,
    p_func: callable | None = None,
) -> float:
    """Eq(4): expected utility differential for agent with signal theta_i.

    Delta(theta_i, theta') = (1/2eps) * integral[theta_i-eps to theta_i+eps]
                              v(theta, n(theta, theta')) d_theta
    """
    def integrand(th: float) -> float:
        n = withdrawal_fraction(th, theta_threshold, lambda_, epsilon)
        return utility_differential(th, n, r1, R, gamma, p_func)

    result, _ = integrate.quad(integrand, theta_i - epsilon, theta_i + epsilon)
    return result / (2 * epsilon)
