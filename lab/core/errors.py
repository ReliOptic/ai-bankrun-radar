"""Typed errors for the lab framework."""
from __future__ import annotations

__all__ = ["LabError", "BankParameterError", "ExperimentError"]


class LabError(Exception):
    """Base for all lab-framework errors."""


class BankParameterError(LabError, ValueError):
    """Raised when bank contract parameters violate D-D constraints."""


class ExperimentError(LabError, RuntimeError):
    """Raised when an experiment cell fails to complete."""
