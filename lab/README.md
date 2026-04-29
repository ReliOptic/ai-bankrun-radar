# AI Bank Run Lab — AAAI 2027 Experimental Framework

**프로젝트**: AI-driven bank run simulation  
**목적**: AAAI 2027 Signal Governance 논문 실험 코드  
**랜딩**: https://relioptic.github.io/ai-bankrun-radar/  
**방법론**: `lab/docs/methodology.md` (작성 중)

---

## Directory Layout

```
lab/
├── pyproject.toml              # project metadata + dependency pins
├── core/
│   ├── bank.py                 # Diamond-Dybvig contract: f_critical, DiamondDybvigContract
│   ├── errors.py               # Typed errors: LabError, BankParameterError, ExperimentError
│   └── types.py                # Frozen dataclasses: BankParameters, RunOutcome, CalibrationCell
├── experiments/
│   └── e01_calibration.py      # E01: parameter sweep + f_critical heatmap
├── tests/
│   ├── test_bank.py            # Unit tests for core.bank
│   └── test_e01.py             # Integration tests for E01
└── data/
    └── experiment_outputs/     # Generated PNG and JSON (git-ignored)
```

---

## Quick Start

```bash
cd lab
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run E01 experiment (writes to data/experiment_outputs/)
python -m experiments.e01_calibration
```

Expected outputs after E01:
- `data/experiment_outputs/e01_f_critical_heatmap.png`
- `data/experiment_outputs/e01_results.json`

---

## Experiment Status

| ID  | Name                        | Status      |
|-----|-----------------------------|-------------|
| E01 | Calibration baseline (D-D)  | Implemented |
| E02 | LLM-agent withdrawal model  | Pending     |
| E03 | Information cascade          | Pending     |
| E04 | Network contagion            | Pending     |
| E05 | Regulatory counter-measures | Pending     |
| E06 | Stochastic time compression | Pending     |
| E07 | Multi-bank systemic risk    | Pending     |
| E08 | Historical calibration      | Pending     |

---

## Core Theory

E01 implements the Diamond-Dybvig (1983) f_critical formula:

```
f* = (R - r1) / (r1 * (R - 1))
```

A bank collapses when the withdrawal fraction f > f*. E02–E08 extend
this substrate with LLM-backed agents that observe signals and decide
whether to withdraw, testing Proposition 1:

```
P(run | σ_fund, K_eff) ≥ Φ((σ_fund · α(K_eff) − θ_DD) / σ_idio)
where α(K_eff) = 1 + λ/K_eff
```

---

## Reproducibility

All experiments use fixed seeds (E01: `SEED = 42`). Re-running any
experiment produces byte-identical JSON output.

```bash
# Verify reproducibility
pytest tests/test_e01.py::test_e01_reproducibility -v
```
