# EXPERIMENT_DESIGN.md — Two-Set Structure

**Companion to**: PROJECT_SPEC.md v0.2
**Governed by**: ADR-006 (AI agent = observation target), ADR-007 (milestone resequencing)
**Version**: 0.2 (two-set reorganization)
**Last updated**: 2026-04-18

---

## §0. Structure at a Glance

5개 실험을 **두 세트**로 묶는다. 세트의 목적이 독립적이므로 구현·일정·보고서도 세트 단위로 분리한다.

```
┌────────────────────────────────────────────────────────────────┐
│  실험 1 — Direct Hypothesis Test (primary)                      │
│  목적: AI 에이전트의 행동 엔트로피가 Mythos 이후 실제로 급락하며,      │
│        그 효과가 LLM-특이적(generic automation이 아님)인가?        │
│  구성: E23 (foundation) → E26 (primary DiD)                    │
│  출력: 본 프로젝트의 main result                                   │
└────────────────────────────────────────────────────────────────┘
                              │ main result
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  실험 2 — Triangulation & Simulation (supporting)              │
│  목적: 실험 1의 결론을 자산 표면·네트워크 구조·행동 시뮬레이션으로 삼각   │
│        측량하여 외부 타당성(external validity)을 강화한다.         │
│  구성: E24 (asset channel) + E25 (network) + E27 (SVB ABM)     │
│  출력: Robustness appendices + policy brief evidence           │
└────────────────────────────────────────────────────────────────┘
```

세트 간 관계: 실험 1의 결과가 main claim을 결정한다. 실험 2는 독립적으로 해석되지 않고, 항상 실험 1과 **어떻게 일치/충돌하는가**의 축에서 보고된다.

| Order | Exp | Set | Role | Primary DV |
|-------|-----|-----|------|-----------|
| 1 | E23 | 실험 1 | Foundation (agent-ID calibration) | Layer 1/2 classifier metrics |
| 2 | **E26** | **실험 1** | **Primary 3-arm DiD** | **`H_agent(t)`** |
| 3 | E24 | 실험 2 | Asset-channel corroboration | `H_asset(t)` |
| 4 | E25 | 실험 2 | Network correlation (AI subset) | λ₁, participation ratio |
| 5 | E27 | 실험 2 | SVB counterfactual ABM | Run-size distribution |

v0.1의 E24-주·E26-보조 순서는 폐기되었다.

---

# 실험 1 — Direct Hypothesis Test

**세트 목적**: 본 프로젝트의 Core Hypothesis — "AI 에이전트의 행동 엔트로피가 Mythos 도래 이후 집단적으로 급락한다" — 를 **직접 측정·검정**한다. 이 세트가 실패하면 프로젝트의 main claim은 성립하지 않는다.

**세트 성공 조건**:
1. AI 에이전트 라벨링이 재현 가능 수준의 정확도로 가능함을 E23에서 입증
2. E26의 3-arm DiD에서 `ΔH_agent < ΔH_human` AND `ΔH_agent < ΔH_MEV` 유의성 판정 (지지/기각 무관, 명확한 결론)

**세트 실패 조건**: E23이 H23.2 미달 → E26 자체가 실행 불가. 실패 시 §1.6 soft-fail plan.

---

## §1. E23 — Foundation: Agent Identification Calibration

### §1.1 Purpose (한 문장)

E26이 측정할 대상인 "AI 에이전트"를 온체인 데이터로 라벨링 가능하게 만드는 인프라 실험. 이 실험이 통과하지 못하면 E26의 DV(`H_agent`)는 정의되지 않는다.

### §1.2 Hypotheses

- H23.1: Layer 1 (self-declared + ERC-4337) 합쳐 N ≥ 5,000 distinct addresses 수집
- H23.2: Layer 2 분류기가 held-out Layer 1 set에서 precision ≥ 0.85, recall ≥ 0.70
- H23.3: Layer 1 vs Layer 2의 `H_agent(t)` baseline (2026-03-01 ~ 2026-04-06) 추정치가 ±10% 내 일치

### §1.3 Data

| Source | Window | Target size |
|--------|--------|-------------|
| Virtuals Protocol (Dune) | 2025-10-01 ~ 현재 | all listed agents |
| Fetch.ai (REST) | 2025-10-01 ~ 현재 | active agents |
| Olas / Autonolas | 2025-10-01 ~ 현재 | active services |
| ERC-4337 paymaster events | 2025-10-01 ~ 현재 | top-100 paymasters filtered |
| Farcaster bot labels (Neynar) | 2025-10-01 ~ 현재 | all flagged |
| MEV searcher (EigenPhi, libMEV) | 2025-10-01 ~ 현재 | top 500 by volume |
| Farcaster human-verified | 2025-10-01 ~ 현재 | stratified sample 10k |

### §1.4 Method

1. Layer 1 수집 및 cross-source dedup. 주소별 `source_tag` 유지.
2. Feature engineering per address per day:
   - `interval_uniformity`: Gini of inter-tx intervals
   - `activity_24_7`: entropy of hour-of-day distribution
   - `gas_optimization`: residual of gas_price ~ f(mempool_median)
   - `multihop_composition_speed`: count of >3-hop tx constructed within 60s
3. XGBoost 분류기, 5-fold CV on Layer 1 positives + human/MEV negatives
4. Threshold tuning via Youden's J on held-out fold
5. Baseline `H_agent(t)` 계산 (Layer 1-only and Layer 2-score-weighted)

### §1.5 Acceptance

- [ ] H23.1 통과 (N ≥ 5,000)
- [ ] H23.2 통과 (precision/recall)
- [ ] H23.3 통과 (baseline 수렴)
- [ ] Classifier card `docs/model_cards/E23_agent_classifier.md` (features, metrics, failure modes)
- [ ] Reproducible: seed fixed, raw Parquet committed, features deterministic

### §1.6 Soft-Fail Plan

H23.2 미달 시:
- Plan A: feature 재설계, Layer 1 확대 (Bittensor subnet 추가)
- Plan B: Layer 2 포기, Layer 1 단독으로 E26 진행 (표본 축소 수용)
- Plan C: E26 자체 재설계 — MEV arm을 broader "automation" arm으로 통합

결정은 `docs/adr/ADR-008-E23-outcome.md`에 기록.

---

## §2. E26 — Primary: AI Agent Behavioral Entropy under Mythos

### §2.1 Purpose (한 문장)

Mythos 도래(T=2026-04-07)를 기점으로 AI 에이전트의 행동 엔트로피가 **인간 대비·비-LLM 자동화 대비 모두** 유의하게 하락하는지 3-arm DiD로 식별한다. 본 프로젝트의 **main claim을 결정하는 단 하나의 실험**.

### §2.2 Hypotheses

- H26.1 (primary): Mythos 후 `ΔH_agent < 0` 유의 (α=0.05)
- H26.2 (identification): `ΔH_agent − ΔH_human < 0` 유의 AND `ΔH_agent − ΔH_MEV < 0` 유의
- H26.3 (robustness): Layer 1-only 결과와 Layer 2-weighted 결과의 방향 일치 및 95% CI overlap

**귀무 (공통 정보 충격 모델)**: 모든 arm에서 비슷한 ΔH. 이 귀무가 기각되지 않으면 "LLM-특이 효과" 주장은 근거 부족으로 본다.

### §2.3 Design — 3-arm DiD

| Arm | Population | N target | Source |
|-----|------------|----------|--------|
| Treatment | Layer 1 + Layer 2 high-conf AI agents | ≥ 5,000 | E23 pipeline |
| Control 1 | Farcaster-verified humans | ≥ 5,000 (stratified) | Neynar |
| Control 2 | MEV searcher bots | ≥ 500 | EigenPhi, libMEV |

- **Event**: T = 2026-04-07 00:00 UTC
- **Pre-window**: T − 60d (확장, short post-window 보완)
- **Post-window**: T + 11d 현재, T + 30d까지 확장 (§2.8)
- **Frequency**: hourly `H(t)`, daily aggregated for regression

### §2.4 Estimator

Two-way fixed-effects DiD on hourly panel:

```
H_{i,t} = α_i + λ_t + β₁·(Agent_i · Post_t) + β₂·(MEV_i · Post_t) + ε_{i,t}
```

- `β₁` = AI agent treatment effect vs humans
- `β₁ − β₂` = LLM-specific effect (generic-automation 경로 제거)
- SEs: clustered by arm × day, block-bootstrap (n=1000) backup

Robustness:
- GARCH(1,1) on arm-level H for variance-adjusted CAR
- Placebo T' ∈ {T − 30d, T − 21d, T − 14d, T − 7d}
- Synthetic control donor pool: Layer 1 agents active before 2026-01

### §2.5 Data

| Source | Use | Window |
|--------|-----|--------|
| E23 classifier output | Treatment labels | 2025-10-01 ~ |
| Neynar verified users | Control 1 labels | 2025-10-01 ~ |
| EigenPhi / libMEV | Control 2 labels | 2025-10-01 ~ |
| On-chain tx logs | Action-type distribution | 2026-02-06 ~ rolling |
| Action taxonomy | 21-class (see §2.6) | — |

### §2.6 Action Taxonomy (21 classes)

Finalized in E23:
- Transfer (native / ERC-20 / ERC-721 / ERC-1155)
- Swap (DEX / aggregator)
- Liquidity (add / remove / range adjust)
- Lending (supply / borrow / repay / liquidate)
- Staking (deposit / withdraw / claim)
- Governance (propose / vote / delegate)
- Bridge (L1→L2 / L2→L1)
- AA operation (paymaster pay / session key)

`p_i(t) = count_i(t) / Σ_j count_j(t)`, `H_agent(t) = −Σ p_i log₂ p_i`.

### §2.7 Acceptance

- [ ] H26.1 결과 보고 (support / reject / inconclusive)
- [ ] H26.2 식별 유의성 3-arm 보고
- [ ] H26.3 Layer 1/2 cross-validation 테이블
- [ ] Placebo null distribution 첨부
- [ ] Pre-registration `docs/preregistration/E26.md` (post-window unlock 이전 커밋)
- [ ] Honest-null report 작성 (H26.1 기각 시에도 동일 quality)

### §2.8 Sample Size & Power

Pre-window 60d × 24h = 1,440 obs/arm. Post T+11d = 264 obs/arm. T+30d → 720 obs.
α=0.05, power=0.8, clustered SEs 기준 MDE ≈ 0.12 bits (≈ pre-baseline의 5%).
**T+11d는 통계력 부족 → main result 보고는 T+30d 확보 전까지 보류**, 그 전에는 pre-registered interim analysis만.

---

# 실험 2 — Triangulation & Simulation

**세트 목적**: 실험 1이 측정한 agent-level 효과를 **세 개의 독립 관측축**에서 교차 검증한다:
(a) 자산 표면의 엔트로피 (E24 — Mythos 효과가 agent → asset으로 전달되는가)
(b) 시장 전체의 상관 구조 (E25 — agent 참여가 높은 자산에서 spectral radius가 더 크게 움직이는가)
(c) 과거 실제 bank run의 시뮬레이션 재현 (E27 — AI 비중을 변주했을 때 run 크기가 어떻게 달라지는가)

이 세트의 각 실험은 **독립 결론이 아닌 실험 1과의 일치/충돌을 보고**한다.

**세트 성공 조건**: 세 실험 모두 실험 1과의 **방향 일치 여부를 명시적으로 판정**하고, 그 결과가 논문 robustness appendix + 정책 브리프 근거로 사용 가능할 것. 유의성 자체가 성공의 조건은 아님.

**세트 실패 조건**: 세 실험 결과가 서로 그리고 실험 1과 모두 충돌할 때 — 이 경우 ADR로 귀무(공통 정보 충격) 채택을 기록한다.

---

## §3. E24 — Asset-Channel Corroboration

### §3.1 Purpose (한 문장)

스테이블코인 자산 표면에서 관측되는 엔트로피 변화가 E26의 agent-level 결과와 **같은 방향**인지 확인. "agent 행동 변화가 실제 자산 흐름으로 전이되는가"의 간접 증거.

### §3.2 Hypotheses

- H24.1: `ΔH_asset`의 기호가 `ΔH_agent`와 동일 (main check)
- H24.2: CAR 유의성 (GARCH(1,1))

E24는 유의성보다 **E26과의 방향 일치**가 더 중요한 판정 기준이다.

### §3.3 Method

- Assets: USDC, USDT, PYUSD, DAI, FDUSD, RLUSD
- `H_asset(t)` = Shannon entropy of redemption-vs-issuance-category 분포
- GARCH(1,1) CAR, Placebo, Synthetic control (v0.1 설계 유지)
- 결과 해석 핵심: `sign(ΔH_asset) == sign(ΔH_agent)` 여부

### §3.4 Acceptance

- [ ] 6개 자산 × 3개 method 결과 매트릭스
- [ ] `H_asset` vs `H_agent` 방향 일치 테이블
- [ ] 충돌 시 discussion에 해석 추가 (asset 표면에서 효과가 감쇠/증폭되는 메커니즘)

---

## §4. E25 — Network Correlation (AI subset)

### §4.1 Purpose (한 문장)

6-asset 상관 구조의 spectral radius 변화가 **AI 에이전트 참여도가 높은 자산에 집중되는지** 검정. E26의 agent-level 효과가 네트워크 구조로 표출되는 경로를 포착.

### §4.2 Method

- Rolling 7d Pearson correlation, λ₁, participation ratio
- Bootstrap CI n=1000
- AI-agent subset: E23 high-conf addresses의 tx가 차지하는 자산별 비중으로 가중

### §4.3 Acceptance

- [ ] 전체 시장 λ₁ 시계열 + CI
- [ ] AI-agent-weighted λ₁ 시계열 + CI
- [ ] 두 계열 차이 검정 (Wilcoxon signed-rank)
- [ ] E26 방향과 일치 여부 명시

---

## §5. E27 — SVB Counterfactual ABM (Agent-Aware)

### §5.1 Purpose (한 문장)

과거 실제 bank run(SVB 2023)을 calibration 기반으로 재현한 뒤, AI agent 비중 α를 변주하여 **"AI 비중이 높을 때 run 규모가 더 커지는가"** 라는 반사실 질문에 답한다. 실험 1의 실증 결과를 시뮬레이션으로 외삽하는 다리 역할.

### §5.2 Method

- 5,000-agent ABM (Mesa), depositor heterogeneity + social signal propagation
- α ∈ {0, 0.1, 0.3, 0.5}; α agents는 E23 분류 특성 반영(interval 저분산, signal 동조화)
- MCMC β calibration on SVB 2023 hourly redemption rate
- 1,000 Monte Carlo runs / α

### §5.3 Acceptance

- [ ] Calibration R̂ < 1.01, ESS ≥ 400
- [ ] Run-size distribution per α + 95% CI
- [ ] Sensitivity: prior variance ±50%, α step 0.05
- [ ] E26 방향과 일치 여부 명시 (α↑일 때 run 규모↑가 E26 ΔH_agent↓ 방향과 consistent한가)

---

## §6. Cross-Experiment Consistency Rules

1. **Seed registry**: 모든 stochastic step은 `config/seeds.toml`에서 참조. 실험별 seed 겹치지 않음.
2. **Data snapshot hashes**: 각 실험 결과 JSON에 raw Parquet SHA256 포함.
3. **Pre-registration before post-window unlock**: E26 post-window 데이터는 T+30d까지 sealed. Pre-reg 파일 커밋 이후에만 unlock.
4. **Honest-null clause**: 모든 실험 보고서는 "가설 기각 시 왜 틀렸는가" 섹션 필수 (N3.3).
5. **Set-alignment reporting**: 실험 2의 세 실험 각각은 "실험 1과의 방향 일치 여부" 테이블을 보고서 상단에 포함.

---

## §7. Dependencies

```
실험 1
  E23 ──► E26 ─────────┐ main result
                       │
실험 2                  │
  E24 ◄────────────────┤ corroboration
  E25 ◄── E23 subset ──┤ corroboration
  E27 ◄── E23 params ──┘ corroboration
```

- E23 failure → E26, E25, E27 blocked (E24는 독립 실행 가능)
- 실험 2는 실험 1 main result가 interim이라도 집계된 뒤 보고서 작성 시작

---

## §8. Open Items

- OQ-13 (분류기 FP 상한): E23 §1.4 threshold tuning에서 결정
- OQ-14 (Layer 1/2 충돌 시 main result): E26 pre-registration 파일에 사전 규칙 명기
- OQ-15 (MEV vs LLM arbitrage 경계): E23 §1.4 라벨링 규칙 문서화
- OQ-16 (실험 2 세 실험 중 하나만 실험 1과 충돌 시 weight 부여 규칙): E24/E25/E27 결과 종합 시 결정

*End of EXPERIMENT_DESIGN.md v0.2.*
