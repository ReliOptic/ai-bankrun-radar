"""Tests for experiments.e01_calibration."""
import json
from pathlib import Path

import pytest

from experiments.e01_calibration import REFERENCE_CELLS, run_e01


def test_e01_runs_and_produces_outputs(tmp_path: Path) -> None:
    run_e01(output_dir=tmp_path)
    assert (tmp_path / "e01_f_critical_heatmap.png").exists()
    assert (tmp_path / "e01_results.json").exists()


def test_e01_summary_has_reference_cells(tmp_path: Path) -> None:
    run_e01(output_dir=tmp_path)
    summary = json.loads((tmp_path / "e01_results.json").read_text())
    assert summary["n_cells"] > 0
    assert len(summary["reference_cells"]) == len(REFERENCE_CELLS)


def test_e01_summary_reference_values(tmp_path: Path) -> None:
    """Spot-check computed f_critical against known analytical values."""
    run_e01(output_dir=tmp_path)
    summary = json.loads((tmp_path / "e01_results.json").read_text())
    ref = {(r["R"], r["r1"]): r["f_critical"] for r in summary["reference_cells"]}
    # (R=1.5, r1=1.2) → 0.5
    assert ref[(1.5, 1.2)] == pytest.approx(0.5)
    # (R=2.0, r1=1.5) → 1/3
    assert ref[(2.0, 1.5)] == pytest.approx(1.0 / 3.0)
    # (R=1.2, r1=1.05) → 0.15/0.21
    assert ref[(1.2, 1.05)] == pytest.approx(0.15 / 0.21)


def test_e01_summary_stats_in_range(tmp_path: Path) -> None:
    """f_critical values should be positive and finite."""
    run_e01(output_dir=tmp_path)
    summary = json.loads((tmp_path / "e01_results.json").read_text())
    assert summary["f_critical_min"] > 0.0
    assert summary["f_critical_max"] < float("inf")
    assert summary["f_critical_mean"] > 0.0


def test_e01_reproducibility(tmp_path: Path) -> None:
    """Run E01 twice; output JSON must be byte-identical."""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    run_e01(output_dir=out1)
    run_e01(output_dir=out2)
    j1 = (out1 / "e01_results.json").read_text()
    j2 = (out2 / "e01_results.json").read_text()
    assert j1 == j2


def test_e01_heatmap_nonzero_bytes(tmp_path: Path) -> None:
    """PNG must be a non-empty file."""
    run_e01(output_dir=tmp_path)
    size = (tmp_path / "e01_f_critical_heatmap.png").stat().st_size
    assert size > 1000  # a valid PNG is always several KB
