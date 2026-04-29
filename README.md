# Signal Governance · AI Bankrun Radar

**A low-cost framework for early detection of behavioral correlation spikes as AI agents enter financial markets.**

[![Live](https://img.shields.io/badge/live-relioptic.github.io%2Fai--bankrun--radar-5B8DEF.svg)](https://relioptic.github.io/ai-bankrun-radar/)
[![KAIST AI Future Challenge 2026](https://img.shields.io/badge/KAIST-AI%20Future%20Challenge%202026-9CC2FF.svg)]()
[![AAAI 2027 Submission](https://img.shields.io/badge/AAAI%202027-Submission-E8B14B.svg)]()
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)]()

---

## 한국어 요약

가격이 무너지기 전, **AI 동조화 신호**가 먼저 수렴합니다.

AI 에이전트가 같은 정보·같은 모델을 보고 동시에 판단하면, 뱅크런은 인출률이 오르기 전에 이미 **행동의 차원**에서 시작됩니다. **Signal Governance**는 그 집단 행동 수렴을 시간축에서 포착해, 결정론적 규칙으로 단계 개입하고, 모든 조치를 감사 가능한 기록으로 남기는 시장 안전망입니다.

- **Lead time**: 가격 기반 경보 대비 +14h (SVB 2023 calibrated synthetic test)
- **이론 통합**: Diamond–Dybvig · Gorton–Pennacchi · Acemoglu · Shannon — 4 canonical models의 AI-era 확장
- **실시간 의사결정 경로 LLM 비중**: 0% (deterministic core, LLM은 사후 설명·감사 보조에 한정)

### 빠른 탐색

| | |
|---|---|
| 🌐 **랜딩 페이지 (Layer 2)** | **[relioptic.github.io/ai-bankrun-radar](https://relioptic.github.io/ai-bankrun-radar/)** — 8개 섹션, 시간축 라더, 5 신호, 3-tier 시스템, Track A/B/C 검증 |
| 📄 **Project Spec** | [`PROJECT_SPEC.md`](./PROJECT_SPEC.md) — 시스템 사양 |
| 🧪 **Reference implementation** | `src/contagion_radar/` · `tests/` (아래 Implementation Reference 참조) |

### 정직한 자기검증 (이 프로젝트가 아닌 것)

- 실시간 뱅크런 감지기가 아닙니다. 가설 검증 프레임워크입니다.
- 기관급 프로덕션 시스템이 아닙니다. 개인 프로젝트 규모입니다.
- 가설 검증이 완료된 연구가 아닙니다. 양방향 가치(지지·기각 모두 학술 기여)를 지향합니다.

> **제출 트랙**: KAIST AI Future Challenge 2026 / AAAI 2027 Submission Package
> **저자**: Kiwon Cho · KAIST PMBA 13기 · ZEISS Korea
> **라이선스**: MIT (code) · CC-BY (docs)

---

## Implementation Reference (English)

The `src/` tree contains a reference implementation of the deterministic rule engine described in the landing page's Tier 2. It is provided as part of the AAAI 2027 supplementary material — not as a deployed production system.

---

## The Problem

AI agents are autonomously participating in asset management, liquidity provision, and risk management. Existing on-chain monitoring tools (Chainalysis, Nansen, etc.) are designed for wallet-level anomaly detection — not for tracking **system-level behavioral correlation shifts** driven by rising agent participation.

Two established mechanisms create compounding risk:

- **Acemoglu et al. (2015)** proved that shock concentration at network hubs transmits micro-shocks into macro-level collapse.
- **Diamond & Dybvig (1983)** showed that bank runs operate as self-fulfilling prophecies.

In an agent-dominated market, these mechanisms may combine. Even when agents use the same underlying model, differences in configuration and context produce diverse outputs — **"same model ≠ same judgment."** However, whether agent behavioral correlations spike during market stress relative to calm periods **remains an open, unverified hypothesis.**

This framework provides a low-cost way to test it.

---

## Core Hypothesis

> **During market stress, does behavioral entropy among AI agents drop significantly compared to calm periods — indicating dangerous herding?**

If supported: the system becomes early-warning infrastructure for agent-driven bank runs.
If rejected: it provides empirical evidence that agent diversity is sufficient, reducing regulatory uncertainty.
Either outcome has academic and policy value. The Knowledge Base accumulates observations over time, improving detection precision automatically.

---

## Architecture

```
┌─── DATA LAYER ─────────────────────────────────────────────────┐
│  DeFiLlama · Etherscan · Yahoo Finance · Reddit · NewsAPI     │
│       ↓                                                        │
│  Quality Gate (FRESH | STALE | DEGRADED | OFFLINE)             │
│  + circuit breaker (3 consecutive failures → source offline)   │
└──────────────────────┬─────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│  RULE ENGINE  (deterministic, cost = $0)                       │
│                                                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ Topology   │  │ Narrative  │  │Monoculture │               │
│  │ Acemoglu   │  │ keyword    │  │ Shannon    │               │
│  │ network    │  │ velocity   │  │ entropy    │               │
│  │ + cascade  │  │ + momentum │  │ + correl.  │               │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘               │
│        └───────────┬────┴──────────────┘                       │
│                    ▼                                           │
│  Composite Scorer (weighted sum + cross-engine amplification   │
│                    + data quality discount + G&P / D&D models) │
└──────────────────────┬─────────────────────────────────────────┘
                       │ FeatureVector (full state, never scalar)
           ┌───────────┼────────────────────┐
           ▼           ▼                    ▼
    ┌──────────┐ ┌───────────┐  ┌───────────────────┐
    │ Cadence  │ │  Alerts   │  │  AI Layer         │
    │ 60min →  │ │ severity  │  │  (OpenRouter)     │
    │ → 30sec  │ │ × novelty │  │  triggered only   │
    │ adaptive │ │ multiplier│  │  when needed:     │
    └──────────┘ └───────────┘  │  · pre-mortem     │
                                │  · novelty eval   │
                                │  · crisis interp  │
                                │  model-agnostic   │
                                └────────┬──────────┘
                                         ↕
                              ┌──────────────────────┐
                              │   Knowledge Base     │
                              │   (SQLite)           │
                              │   hypotheses · anomalies
                              │   precedents · calibrations
                              │   ───────────────────│
                              │   compounds over time│
                              └──────────────────────┘
```

### Design Principles

| # | Principle | Implementation |
|---|-----------|----------------|
| 1 | **Monitoring is rule-based** | Deterministic engines, zero API cost |
| 2 | **AI for insight only** | OpenRouter calls only at threshold crossings |
| 3 | **Pre-mortem as differentiator** | "If this entity fails tomorrow, why?" → auto-generated watch items |
| 4 | **Adaptive cadence** | Score-driven: 1hr (calm) → 30sec (crisis) with hysteresis |
| 5 | **Time compounds value** | KB accumulates; precision improves with each observation |
| 6 | **Distrust bad data** | Quality gate + circuit breaker per source |
| 7 | **AI receives vectors, not scalars** | Full FeatureVector prevents information loss |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/ReliOptic/ai-bankrun-radar.git
cd ai-bankrun-radar
pip install -e ".[dev]"

# Initialize databases
radar db-init

# One-shot scan
radar scan --entity USDC

# Pre-mortem analysis (offline, no API key needed)
radar premortem --entity USDC

# Backtest against SVB 2023 scenario
radar backtest --scenario svb_2023

# Live dashboard
radar monitor --entity USDC
```

### Environment Variables (optional — for live data)

```bash
export OPENROUTER_API_KEY="sk-..."      # AI reasoning (any model)
export ETHERSCAN_API_KEY="..."           # on-chain data
export NEWS_API_KEY="..."               # news articles
```

Without API keys, the system runs in **offline mode** using rule-based engines only.

---

## Three Engines

### Topology Engine

Applies Acemoglu's network contagion model. Builds a directed exposure graph (nodes = entities, edges = USD exposure), computes per-node vulnerability scores (leverage, maturity mismatch, concentration, centrality), and runs Monte Carlo cascade simulations.

```python
from contagion_radar.engines.topology.engine import TopologyEngine, ExposureEdge

engine = TopologyEngine(config.engines.topology)
engine.build_graph([
    ExposureEdge("SVB", "USDC", 3_300_000_000),
    ExposureEdge("USDC", "Aave", 1_000_000_000),
])
score = engine.compute("SVB", metrics={"leverage": 0.7, "concentration": 0.8})
```

### Narrative Engine

Regex-based crisis keyword classifier across 6 categories (bank_run, de_peg, liquidity_crisis, contagion, confidence_loss, regulatory_action). Computes narrative momentum = spread velocity relative to historical baseline.

### Monoculture Engine

**The core measurement for the hypothesis.** Shannon entropy of wallet cluster strategy distributions. When entropy drops (strategies converge), monoculture index rises toward 1.0 — the flash-crash precursor signal. Cross-asset correlation analysis detects herding across price series.

```python
from contagion_radar.engines.monoculture.entropy import monoculture_index

monoculture_index([0.25, 0.25, 0.25, 0.25])  # → 0.0 (diverse)
monoculture_index([0.95, 0.02, 0.02, 0.01])  # → 0.87 (dangerous)
```

---

## Theoretical Foundations

| Model | Paper | Role in System |
|-------|-------|----------------|
| **Diamond & Dybvig (1983)** | Bank Runs, Deposit Insurance, and Liquidity | Tipping point: `f_critical = (R - r1) / (r1 × (R - 1))`. When withdrawal fraction exceeds this, rational agents run. |
| **Goldstein & Pauzner (2005)** | Demand-Deposit Contracts and the Probability of Bank Runs | Unique equilibrium threshold `θ*(r1)`. Maps bank parameters to run probability via global games. |
| **Acemoglu et al. (2015)** | Systemic Risk and Stability in Financial Networks | Network topology determines whether micro-shocks propagate. Hub concentration amplifies cascades. |
| **Shannon (1948)** | A Mathematical Theory of Communication | Entropy as diversity metric. Low entropy = monoculture = systemic fragility. |

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `radar scan -e <entity>` | One-shot risk analysis |
| `radar monitor -e <entity>` | Live Rich dashboard (6 panels) |
| `radar premortem -e <entity>` | Pre-mortem hypothesis generation |
| `radar backtest -s <scenario>` | Historical scenario replay |
| `radar calibrate [--dry-run]` | Recalibrate engine weights from KB |
| `radar db-init` | Initialize SQLite databases |
| `radar suppress --alert-id <id> --reason <text>` | Suppress alert |
| `radar override --entity <name> --severity <float>` | Manual severity override |
| `radar reevaluate --entity <name>` | Force re-scan |
| `radar acknowledge --alert-id <id>` | Mark alert as seen |

---

## Backtest Scenarios

Three historical scenarios are included for validation:

| Scenario | Period | Crisis Event |
|----------|--------|-------------|
| `svb_2023` | Feb–Mar 2023 | Silicon Valley Bank collapse + USDC de-peg |
| `terra_luna_2022` | Apr–May 2022 | UST/LUNA death spiral |
| `gfc_2008` | Sep 2007–Mar 2009 | Global Financial Crisis |

```bash
radar backtest --scenario svb_2023
```

The backtest runner generates synthetic data following the known crisis timeline, feeds it through the full rule engine, and reports detection lead time, precision, and recall.

---

## Operating Cost

| Component | Cost |
|-----------|------|
| Rule engine (3 engines + composite) | **$0** — deterministic, local |
| Data adapters (DeFiLlama, Reddit) | **$0** — public APIs |
| AI reasoning (OpenRouter) | **~$2–3/day** — budget-managed |
| SQLite storage | **$0** — local files |

AI calls are rate-limited by risk level:

| Risk Level | Daily AI Call Limit |
|------------|-------------------|
| Normal (< 0.3) | 20 |
| Elevated (0.3–0.6) | 50 |
| Warning (0.6–0.8) | 200 |
| Crisis (> 0.95) | Unlimited |

---

## Project Structure

```
contagion-radar/
├── config/                  # 7 YAML config files + backtest scenarios
├── src/contagion_radar/
│   ├── models/              # G&P bank run, D&D tipping point
│   ├── engines/             # topology, narrative, monoculture
│   ├── rule_engine/         # composite scorer, calibrator, main loop
│   ├── data/                # adapters (5 sources), quality gate, pipeline
│   ├── cadence/             # adaptive monitoring interval
│   ├── reasoning/           # OpenRouter client, budget, novelty
│   ├── premortem/           # hypothesis generator, Bayesian scorer
│   ├── knowledge/           # 3 SQLite DB schemas
│   ├── backtest/            # scenario replay framework
│   └── cli/                 # Typer CLI + Rich dashboard
└── tests/                   # 123 unit tests
```

---

## Contributing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

All thresholds live in `config/*.yaml` — engine code never hardcodes values.

---

## References

1. Acemoglu, D., Ozdaglar, A., & Tahbaz-Salehi, A. (2015). Systemic Risk and Stability in Financial Networks. *American Economic Review*, 105(2), 564–608.
2. Diamond, D. W., & Dybvig, P. H. (1983). Bank Runs, Deposit Insurance, and Liquidity. *Journal of Political Economy*, 91(3), 401–419.
3. Goldstein, I., & Pauzner, A. (2005). Demand-Deposit Contracts and the Probability of Bank Runs. *Journal of Finance*, 60(3), 1293–1327.
4. Shannon, C. E. (1948). A Mathematical Theory of Communication. *Bell System Technical Journal*, 27(3), 379–423.

---

<sub>Built with [Claude Code](https://claude.ai/code)</sub>
