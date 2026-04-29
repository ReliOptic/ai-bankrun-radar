"""Tests for core.bank.DiamondDybvigContract."""
import pytest

from core.bank import DiamondDybvigContract, f_critical
from core.errors import BankParameterError
from core.types import BankParameters, RunOutcome


def test_f_critical_known_values() -> None:
    """f_critical for (R=1.5, r1=1.2): (1.5-1.2)/(1.2*(1.5-1)) = 0.3/0.6 = 0.5"""
    params = BankParameters(R=1.5, r1=1.2, L=0.0)
    assert f_critical(params) == pytest.approx(0.5)


def test_f_critical_high_return() -> None:
    """f_critical for (R=2.0, r1=1.5): (2.0-1.5)/(1.5*(2.0-1.0)) = 0.5/1.5 = 1/3"""
    params = BankParameters(R=2.0, r1=1.5, L=0.0)
    assert f_critical(params) == pytest.approx(1.0 / 3.0)


def test_f_critical_low_return() -> None:
    """f_critical for (R=1.2, r1=1.05): (1.2-1.05)/(1.05*(1.2-1.0)) = 0.15/0.21 ≈ 0.7143"""
    params = BankParameters(R=1.2, r1=1.05, L=0.0)
    assert f_critical(params) == pytest.approx(0.15 / 0.21)


def test_invalid_R_raises() -> None:
    with pytest.raises(BankParameterError, match="R must be > 1"):
        BankParameters(R=1.0, r1=0.5, L=0.0)


def test_invalid_r1_raises() -> None:
    with pytest.raises(BankParameterError, match="r1 must be > 0"):
        BankParameters(R=1.5, r1=0.0, L=0.0)


def test_invalid_L_raises() -> None:
    with pytest.raises(BankParameterError, match=r"L must be in \[0, 1\)"):
        BankParameters(R=1.5, r1=1.2, L=1.0)


def test_collapse_above_critical() -> None:
    contract = DiamondDybvigContract(BankParameters(R=1.5, r1=1.2, L=0.0))
    # f_critical = 0.5; withdrawal 0.6 → collapse
    assert contract.is_collapse(0.6)
    assert not contract.is_collapse(0.4)


def test_no_collapse_at_critical() -> None:
    """Boundary: f == f_critical is not collapse (strict inequality)."""
    contract = DiamondDybvigContract(BankParameters(R=1.5, r1=1.2, L=0.0))
    assert not contract.is_collapse(0.5)


def test_evaluate_returns_outcome() -> None:
    contract = DiamondDybvigContract(BankParameters(R=1.5, r1=1.2, L=0.0))
    outcome = contract.evaluate(0.6)
    assert isinstance(outcome, RunOutcome)
    assert outcome.collapsed is True
    assert outcome.f_critical == pytest.approx(0.5)


def test_evaluate_no_collapse() -> None:
    contract = DiamondDybvigContract(BankParameters(R=1.5, r1=1.2, L=0.0))
    outcome = contract.evaluate(0.3)
    assert outcome.collapsed is False
    assert outcome.withdrawal_rate == pytest.approx(0.3)


def test_withdrawal_rate_out_of_range() -> None:
    contract = DiamondDybvigContract(BankParameters(R=1.5, r1=1.2, L=0.0))
    with pytest.raises(BankParameterError):
        contract.is_collapse(1.5)


def test_withdrawal_rate_negative() -> None:
    contract = DiamondDybvigContract(BankParameters(R=1.5, r1=1.2, L=0.0))
    with pytest.raises(BankParameterError):
        contract.is_collapse(-0.1)


def test_reproducibility_identical_outcomes() -> None:
    """Same params → identical f_critical (no stochasticity in E01)."""
    p1 = BankParameters(R=1.5, r1=1.2, L=0.0)
    p2 = BankParameters(R=1.5, r1=1.2, L=0.0)
    assert f_critical(p1) == f_critical(p2)


def test_params_property() -> None:
    params = BankParameters(R=1.5, r1=1.2, L=0.0)
    contract = DiamondDybvigContract(params)
    assert contract.params is params


def test_f_critical_property_matches_function() -> None:
    params = BankParameters(R=1.5, r1=1.2, L=0.0)
    contract = DiamondDybvigContract(params)
    assert contract.f_critical == pytest.approx(f_critical(params))
