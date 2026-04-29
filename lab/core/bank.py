"""Diamond-Dybvig (1983) two-period bank contract.

Implements the canonical f_critical formula and run-condition check.
Pure analytical — no stochasticity, no LLM. Used by E01 and as the
substrate for E02–E08 LLM-agent experiments.
"""
from __future__ import annotations

import structlog

from core.errors import BankParameterError
from core.types import BankParameters, RunOutcome

__all__ = ["DiamondDybvigContract", "f_critical"]

_log = structlog.get_logger(__name__)


def f_critical(params: BankParameters) -> float:
    """Return the run-equilibrium critical fraction f* = (R − r1) / (r1 · (R − 1)).

    When the fraction of depositors withdrawing in period 1 exceeds f*,
    the bank cannot honor remaining period-2 claims and collapses.

    Reference: Diamond and Dybvig (1983), Eq. (10) reformulation.
    """
    numerator = params.R - params.r1
    denominator = params.r1 * (params.R - 1.0)
    if denominator <= 0.0:
        raise BankParameterError(
            "f_critical denominator non-positive — check r1 > 0 and R > 1"
        )
    return numerator / denominator


class DiamondDybvigContract:
    """Encapsulates a D-D contract instance and its run-condition logic."""

    __slots__ = ("_params", "_f_crit")

    def __init__(self, params: BankParameters) -> None:
        self._params = params
        self._f_crit = f_critical(params)
        _log.info(
            "bank.contract_initialized",
            R=params.R,
            r1=params.r1,
            L=params.L,
            f_critical=self._f_crit,
        )

    @property
    def params(self) -> BankParameters:
        """Return the contract parameters."""
        return self._params

    @property
    def f_critical(self) -> float:
        """Return the precomputed critical withdrawal fraction."""
        return self._f_crit

    def is_collapse(self, withdrawal_rate: float) -> bool:
        """Return True iff f > f_critical, indicating bank collapse."""
        if not 0.0 <= withdrawal_rate <= 1.0:
            raise BankParameterError(
                f"withdrawal_rate must be in [0, 1] (got {withdrawal_rate})"
            )
        return withdrawal_rate > self._f_crit

    def evaluate(self, withdrawal_rate: float) -> RunOutcome:
        """Return RunOutcome for a given withdrawal fraction."""
        return RunOutcome(
            withdrawal_rate=withdrawal_rate,
            collapsed=self.is_collapse(withdrawal_rate),
            f_critical=self._f_crit,
        )
