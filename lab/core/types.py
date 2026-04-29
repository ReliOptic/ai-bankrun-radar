"""Shared types for the lab framework."""
from __future__ import annotations
from dataclasses import dataclass

__all__ = ["BankParameters", "RunOutcome", "CalibrationCell"]


@dataclass(frozen=True, slots=True)
class BankParameters:
    """Diamond-Dybvig (1983) two-period contract parameters."""

    R: float   # long-asset gross return, R > 1
    r1: float  # short-period payout to early-withdrawing depositors
    L: float   # liquidation cost when long asset is sold prematurely

    def __post_init__(self) -> None:
        # Import here to avoid circular import (errors imports nothing from core)
        from core.errors import BankParameterError

        if self.R <= 1.0:
            raise BankParameterError(f"R must be > 1 (got {self.R})")
        if self.r1 <= 0.0:
            raise BankParameterError(f"r1 must be > 0 (got {self.r1})")
        if not 0.0 <= self.L < 1.0:
            raise BankParameterError(f"L must be in [0, 1) (got {self.L})")


@dataclass(frozen=True, slots=True)
class RunOutcome:
    """Result of a single simulated trial."""

    withdrawal_rate: float
    collapsed: bool
    f_critical: float


@dataclass(frozen=True, slots=True)
class CalibrationCell:
    """One (R, r1) cell in the E01 calibration sweep."""

    R: float
    r1: float
    f_critical: float
