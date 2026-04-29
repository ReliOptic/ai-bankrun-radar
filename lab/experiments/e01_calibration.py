"""E01 — Calibration baseline.

Sweeps Diamond-Dybvig parameters and verifies f_critical formula.
Produces:
  - data/experiment_outputs/e01_f_critical_heatmap.png
  - data/experiment_outputs/e01_results.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import numpy as np
import structlog

from core.bank import f_critical
from core.errors import ExperimentError
from core.types import BankParameters, CalibrationCell

__all__ = ["run_e01", "REFERENCE_CELLS"]

_log = structlog.get_logger(__name__)

# Reference (R, r1) pairs drawn from Allen-Gale (2007) Table 2.1 range.
# Computed f* values: (1.5,1.2)->0.5; (2.0,1.5)->1/3; (1.2,1.05)->~0.7143
REFERENCE_CELLS: Final[tuple[tuple[float, float], ...]] = (
    (1.5, 1.2),
    (2.0, 1.5),
    (1.2, 1.05),
)

OUTPUT_DIR: Final[Path] = Path("data/experiment_outputs")
SEED: Final[int] = 42  # E01 is deterministic; kept for E02+ reproducibility hooks


def _sweep_grid(
    R_grid: np.ndarray,  # type: ignore[type-arg]
    r1_grid: np.ndarray,  # type: ignore[type-arg]
) -> list[CalibrationCell]:
    """Compute f_critical for all valid (R, r1) pairs in the grid."""
    cells: list[CalibrationCell] = []
    for R_val in R_grid:
        for r1_val in r1_grid:
            if float(r1_val) >= float(R_val):
                continue  # invalid: short payout must not exceed long return
            try:
                params = BankParameters(R=float(R_val), r1=float(r1_val), L=0.0)
                fc = f_critical(params)
                cells.append(CalibrationCell(R=float(R_val), r1=float(r1_val), f_critical=fc))
            except Exception as exc:
                _log.warning("e01.cell_skipped", R=float(R_val), r1=float(r1_val), error=str(exc))
    return cells


def _save_heatmap(cells: list[CalibrationCell], output_path: Path) -> None:
    """Render and save f_critical heatmap to PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    R_vals = sorted({c.R for c in cells})
    r1_vals = sorted({c.r1 for c in cells})
    grid = np.full((len(R_vals), len(r1_vals)), np.nan)
    for c in cells:
        i = R_vals.index(c.R)
        j = r1_vals.index(c.r1)
        grid[i, j] = c.f_critical

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(
        grid,
        aspect="auto",
        origin="lower",
        extent=(min(r1_vals), max(r1_vals), min(R_vals), max(R_vals)),
        cmap="viridis",
    )
    ax.set_xlabel("r1 (short payout)")
    ax.set_ylabel("R (long return)")
    ax.set_title("E01 — Diamond-Dybvig f_critical heatmap")
    fig.colorbar(im, ax=ax, label="f_critical")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    _log.info("e01.heatmap_saved", path=str(output_path))


def _build_summary(cells: list[CalibrationCell]) -> dict[str, object]:
    """Assemble JSON-serialisable summary dict including reference cells."""
    fc_values = [c.f_critical for c in cells]
    ref_entries: list[dict[str, float]] = []
    for R, r1 in REFERENCE_CELLS:
        params = BankParameters(R=R, r1=r1, L=0.0)
        ref_entries.append({"R": R, "r1": r1, "f_critical": f_critical(params)})
    return {
        "n_cells": len(cells),
        "f_critical_mean": float(np.mean(fc_values)),
        "f_critical_min": float(np.min(fc_values)),
        "f_critical_max": float(np.max(fc_values)),
        "reference_cells": ref_entries,
    }


def _save_summary(cells: list[CalibrationCell], output_path: Path) -> None:
    """Write JSON summary to disk."""
    summary = _build_summary(cells)
    output_path.write_text(json.dumps(summary, indent=2))
    _log.info("e01.summary_saved", path=str(output_path), n_cells=summary["n_cells"])


def run_e01(output_dir: Path = OUTPUT_DIR) -> None:
    """Execute E01 calibration sweep end-to-end.

    Args:
        output_dir: Directory for PNG and JSON outputs. Created if absent.

    Raises:
        ExperimentError: If the sweep produces no valid cells.
    """
    _log.info("e01.start", seed=SEED)
    output_dir.mkdir(parents=True, exist_ok=True)

    R_grid: np.ndarray = np.linspace(1.05, 2.0, 20)  # type: ignore[type-arg]
    r1_grid: np.ndarray = np.linspace(0.95, 1.5, 20)  # type: ignore[type-arg]

    cells = _sweep_grid(R_grid, r1_grid)
    if not cells:
        raise ExperimentError("E01 sweep produced zero valid cells — check parameter ranges")

    _save_heatmap(cells, output_dir / "e01_f_critical_heatmap.png")
    _save_summary(cells, output_dir / "e01_results.json")
    _log.info("e01.complete", n_cells=len(cells))


if __name__ == "__main__":
    run_e01()
