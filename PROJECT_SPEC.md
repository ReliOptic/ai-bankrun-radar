# PROJECT_SPEC.md — AI Bank Run Radar v2 (Mythos Edition)

**Project**: `ai-bankrun-radar-mythos`
**Owner**: Kiwon Cho (@kiwon-cho / KAIST PMBA 13기)
**Spec version**: 0.1
**Last updated**: 2026-04-18
**Target**: Claude Code Spec-Driven Development (parallel agent implementation)

-----

## §0. Problem Statement

### §0.1 The Situation

2026년 4월 현재, 세 가지 사건이 동시에 진행 중입니다:

1. **Mythos 도래 (2026-04-07)**: Anthropic이 자율적 취약점 발견·익스플로잇 역량을 가진 frontier 모델을 Project Glasswing 12개 파트너에 한정 배포. 백악관은 미 연방기관 rollout을 준비.
1. **GENIUS Act 구현 단계 (2026 Q1-Q2)**: FDIC 최종 가이드라인 4월 확정. 은행 예금 $6.6조가 스테이블코인으로 이동 가능하다는 은행협회 경고.
1. **AI 에이전트의 금융시장 침투 가속**: LLM 기반 트레이딩/DeFi 에이전트 활성 계정 수 지수적 증가, 그러나 foundation model 종류는 소수.

기존 AI Bank Run Radar 프로젝트(KAIST AI Future Challenge 제출본)는 이 세 변수가 어느 하나도 확정되기 전에 설계되었습니다. 프로토타입의 4-엔진 프레임(Acemoglu/Diamond-Dybvig/Gorton-Pennacchi/Shannon)은 이 새 환경에서 **가설 검증 실험의 기반 인프라**가 되어야 합니다.

### §0.2 What We Are Building

**Not**: 실시간 뱅크런 예측기 (아직 가설 미검증)
**Yes**: Mythos-post 환경에서 5개 독립 실험(E23-E27)을 실행하는 관측·분석 파이프라인 + 결과를 축적하는 Knowledge Base

### §0.3 Success Definition

- 90일 내 5개 실험 모두 acceptance criteria 통과
- 양방향 가치 유지: 가설 지지든 기각이든 재현 가능한 결론 도출
- 총 운영비 < $30, Claude API 비용 < $15
- Knowledge Base는 프로젝트 종료 후 후속 연구에 재활용 가능

-----

## §1. Scope

### §1.1 In Scope

- 스테이블코인(USDC, USDT, PYUSD, DAI, FDUSD, RLUSD) 온체인 트랜잭션 수집
- 시간당 Shannon 엔트로피 계산 파이프라인
- Mythos 발표 이벤트 스터디 (T=2026-04-07)
- 네트워크 상관 분석 (spectral radius, participation ratio)
- AI 에이전트 행동 프록시 측정 (3종)
- SVB counterfactual ABM 시뮬레이션
- SQLite Knowledge Base + nightly recalibration
- 실험 결과 Markdown 보고서 자동 생성

### §1.2 Out of Scope

- 실시간 알림 시스템 (future phase)
- 프로덕션 trading integration
- 규제 당국 실시간 API 연동
- 한국 원화 페그 스테이블코인 (E28+ 확장)
- 비-스테이블코인 crypto (BTC/ETH는 컨트롤 변수로만)
- Front-end dashboard (텍스트 보고서 + 정적 차트로 시작)

### §1.3 Explicit Non-Goals

- Mythos 모델에 직접 접근하거나 프로빙 시도 (Anthropic AUP 위반)
- 스테이블코인 발행사의 비공개 reserve 데이터 접근
- Social engineering으로 AI 에이전트 운영자 식별

-----

## §2. Stakeholders

|Role                  |Person                                |Responsibility     |
|----------------------|--------------------------------------|-------------------|
|Principal Investigator|Kiwon Cho                             |실험 설계, 결과 해석, 논문 집필|
|Technical Architect   |Kiwon Cho (with Claude Code)          |파이프라인 구현, 코드 리뷰    |
|Academic Advisor      |TBD (KAIST PMBA 교수)                   |계량 방법론 검토          |
|Primary Audience      |KAIST AI Future Challenge 심사단, SSRN 독자|결과 소비              |
|Secondary Audience    |금융위·한국은행·FSS 정책연구원                    |정책 브리프             |

-----

## §3. Requirements

### §3.1 Functional

**F1. Data Ingestion**

- F1.1: Dune Analytics GraphQL로 스테이블코인 상환/발행 트랜잭션 수집 (1h interval)
- F1.2: CryptoPanic RSS로 뉴스 이벤트 수집 (15min interval)
- F1.3: FRED API로 매크로 컨트롤 변수 수집 (daily)
- F1.4: Farcaster/X public API로 에이전트 행동 프록시 수집 (rate-limited)
- F1.5: 모든 원자료는 Parquet으로 저장, 재수집 가능성 보장

**F2. Entropy Computation**

- F2.1: 시간당 Shannon 엔트로피 계산 `H(t) = -Σ pᵢ log pᵢ`
- F2.2: Volume-weighted 엔트로피 `H_w(t)` 병기
- F2.3: Rolling 30-day baseline과 z-score 계산
- F2.4: Change point detection (Bai-Perron)

**F3. Event Study**

- F3.1: Mythos 발표 시점(T=0) 중심 event window 설정
- F3.2: GARCH(1,1) 기반 CAR 계산
- F3.3: Placebo test 자동화 (random T)
- F3.4: Synthetic control 생성

**F4. Network Analysis**

- F4.1: 6-asset 상관행렬 rolling computation
- F4.2: Eigendecomposition → λ₁, participation ratio
- F4.3: Bootstrap confidence intervals (n=1000)

**F5. Agent Proxy**

- F5.1: 공개 DeFi 에이전트 액션 로그 수집
- F5.2: Semantic clustering (UMAP + HDBSCAN)
- F5.3: KL divergence 시계열 계산

**F6. ABM Simulation**

- F6.1: SVB 데이터로 모델 파라미터 calibration (MCMC)
- F6.2: 2026 counterfactual 5000-agent 시뮬레이션
- F6.3: 1000회 Monte Carlo + 민감도 분석

**F7. Knowledge Base**

- F7.1: SQLite 기반, 모든 관측/결과/메타 저장
- F7.2: Nightly recalibration job (cron)
- F7.3: 실험 간 의존성 추적

**F8. Reporting**

- F8.1: 실험별 자동 생성 Markdown 보고서
- F8.2: 정적 차트 (matplotlib/seaborn)
- F8.3: 통합 논문 초안 스캐폴딩

### §3.2 Non-Functional

**N1. Cost**

- N1.1: 총 클라우드 비용 ≤ $30 over 90 days
- N1.2: Claude API 호출은 threshold 초과 시에만 (≤ $15 total)
- N1.3: 무료 tier API 우선 사용

**N2. Reproducibility**

- N2.1: 모든 결과는 원자료 + seed로 재현 가능
- N2.2: 의존성은 `requirements.txt` 또는 `pyproject.toml` 고정
- N2.3: 주요 결정은 ADR(Architecture Decision Record)로 기록

**N3. Honesty**

- N3.1: Negative result도 positive result와 동일한 quality로 보고
- N3.2: 모든 프록시의 identifiability 한계를 명시
- N3.3: 가설 기각 시 "왜 틀렸는가" 분석 포함

**N4. Performance**

- N4.1: 일일 nightly recalibration ≤ 15분
- N4.2: 단일 실험 full run ≤ 4시간
- N4.3: Knowledge Base 쿼리 p95 < 500ms

-----

## §4. Architecture

### §4.1 High-Level Layout

```
ai-bankrun-radar-mythos/
├── PROJECT_SPEC.md          (this document)
├── EXPERIMENT_DESIGN.md     (E23-E27 detailed design)
├── CLAUDE.md                (Claude Code context)
├── README.md
├── pyproject.toml
├── data/
│   ├── raw/                 (Parquet, immutable)
│   │   ├── onchain/
│   │   ├── news/
│   │   ├── macro/
│   │   └── social/
│   ├── intermediate/        (computed metrics)
│   └── kb.sqlite            (knowledge base)
├── src/
│   ├── ingest/              (F1)
│   ├── entropy/             (F2)
│   ├── event_study/         (F3)
│   ├── network/             (F4)
│   ├── agent_proxy/         (F5)
│   ├── abm/                 (F6)
│   ├── kb/                  (F7)
│   └── reports/             (F8)
├── experiments/
│   ├── E23_baseline/
│   ├── E24_event_study/
│   ├── E25_correlation/
│   ├── E26_monoculture/
│   └── E27_svb_abm/
├── reports/
│   └── output/
├── jobs/
│   ├── nightly_recalibrate.py
│   └── weekly_digest.py
├── tests/
└── docs/
    └── adr/                 (Architecture Decision Records)
```

### §4.2 Data Flow

```
[External APIs] → ingest/ → data/raw/*.parquet
                                    ↓
                          entropy/ + network/ + agent_proxy/
                                    ↓
                          data/intermediate/*.parquet
                                    ↓
                          event_study/ + abm/
                                    ↓
                              kb.sqlite
                                    ↓
                          reports/output/*.md + *.png
```

### §4.3 Key Design Decisions

**ADR-001: SQLite over DuckDB**

- 결정: KB는 SQLite. 분석 중간 결과는 Parquet.
- 이유: 설치 복잡도 최소화, 개인 프로젝트 규모, 단일 writer

**ADR-002: Python-only stack**

- 결정: Python 3.12 + pandas + statsmodels + scipy + mesa(ABM)
- 이유: 계량경제 표준 툴체인, 재현성

**ADR-003: No real-time; batch-only**

- 결정: nightly cron만 운영, 실시간 X
- 이유: 비용, 단순성, 연구 목적에 충분

**ADR-004: Parquet raw data is immutable**

- 결정: `data/raw/`는 append-only, 재가공은 `intermediate/`에서만
- 이유: 재현성, 디버깅

**ADR-005: Claude API는 reasoning 전용**

- 결정: 데이터 수집·수치 계산은 코드가, 해석·나라티브 생성만 Claude API
- 이유: 비용 규율, 결정적 재현성

-----

## §5. Interfaces

### §5.1 External APIs

|Service           |Endpoint                       |Auth   |Rate Limit        |
|------------------|-------------------------------|-------|------------------|
|Dune Analytics    |`api.dune.com/graphql`         |API key|1000 q/mo (free)  |
|Etherscan         |`api.etherscan.io/api`         |API key|5 req/s (free)    |
|CryptoPanic       |`cryptopanic.com/api/v1`       |none   |unlimited         |
|FRED              |`api.stlouisfed.org/fred`      |API key|unlimited         |
|Farcaster (Neynar)|`api.neynar.com/v2`            |API key|300 req/min (free)|
|Anthropic         |`api.anthropic.com/v1/messages`|API key|tier-based        |

### §5.2 Internal Contracts

**Entropy pipeline output schema** (Parquet):

```
ts: timestamp[ns, UTC]        # Hour boundary (UTC)
asset: string                  # USDC|USDT|PYUSD|DAI|FDUSD|RLUSD
H_shannon: float64             # bits
H_weighted: float64            # volume-weighted
n_obs: int64                   # number of transactions in window
z_score: float64               # vs 30d rolling baseline
```

**Event study output schema**:

```
event_id: string
asset: string
window_start: timestamp
window_end: timestamp
CAR: float64
CAR_ci_lower: float64
CAR_ci_upper: float64
p_value: float64
method: string                 # 'GARCH' | 'RDD' | 'SynthControl'
```

**KB schema**: §6 of EXPERIMENT_DESIGN.md 참조.

-----

## §6. Milestones

### §6.1 Phase 1: Foundation (Week 1-2)

- M1.1: Repo 초기화, CI/CD
- M1.2: Data ingestion layer (F1)
- M1.3: E23 baseline calibration 완료
- M1.4: KB 스키마 확정

**Exit criteria**: E23 acceptance criteria 모두 통과

### §6.2 Phase 2: Event Analysis (Week 3-4)

- M2.1: GARCH baseline 모델
- M2.2: E24 event study 실행
- M2.3: Placebo + synthetic control robustness checks

**Exit criteria**: CAR 추정치 + 강건성 검정 통과

### §6.3 Phase 3: Network + Monoculture (Week 5-7)

- M3.1: Correlation cascade (E25)
- M3.2: Agent proxy 3종 (E26)
- M3.3: 두 실험 결과의 교차 해석

**Exit criteria**: Spectral radius 변화 + agent proxy KL 시계열 완성

### §6.4 Phase 4: Simulation + Synthesis (Week 8-12)

- M4.1: SVB data ingestion + β calibration (MCMC)
- M4.2: 2026 counterfactual ABM 1000 runs
- M4.3: 통합 논문 초안 (SSRN 제출 가능 수준)
- M4.4: 정책 브리프 (한국어, 금융위 제출용)

**Exit criteria**: 논문 초안 + 정책 브리프 완성, KB 인수인계 가능 상태

-----

## §7. Risks

|위험                                         |확률|영향|완화                                          |
|-------------------------------------------|--|--|--------------------------------------------|
|Mythos 발표 직후 관측 기간이 짧아 통계력 부족              |중 |고 |E24 baseline window를 60일로 확대, sensitivity 분석|
|Dune free tier 쿼리 제한 도달                    |중 |중 |쿼리 캐싱, 쿼리 최적화, Etherscan raw 백업             |
|Farcaster/X API 정책 변경                      |중 |중 |초기 90일치 미리 벌크 수집, 스크립트 아카이브                 |
|AI agent identification 근본적 불가능            |고 |고 |§0.2 기조대로 한계 명시, behavior correlation으로 포지셔닝|
|SVB 데이터 재구성 오차                             |중 |중 |복수 소스 교차검증, sensitivity 분석                  |
|Mythos 관련 post-announcement 시장 반응이 이미 가격 반영|중 |고 |intraday granularity로 15분 단위 분석 추가          |
|연구자 단일(bus factor=1)                       |고 |중 |모든 결정 ADR화, KB/데이터 완전 오픈소스화                 |
|Anthropic Mythos 관련 추가 정보 공개 → 연구 전제 변경    |중 |중 |spec version 관리, 변경 시 ADR 추가                |

-----

## §8. Testing Strategy

### §8.1 Unit Tests

- `src/entropy/`: 알려진 분포에 대해 Shannon H 정확성 검증
- `src/network/`: 합성 상관행렬에 대해 λ₁ 계산 정확성
- `src/event_study/`: Fama-French 고전 데이터셋으로 CAR 재현

### §8.2 Integration Tests

- 전체 파이프라인을 7일치 mock data로 E2E 실행
- KB 스키마 마이그레이션 테스트

### §8.3 Statistical Validation

- GARCH 잔차의 Ljung-Box test
- ABM 시뮬레이션의 convergence diagnostic (R̂, ESS)
- Bootstrap CI coverage test (nominal 95% ≈ empirical 95%)

### §8.4 Reproducibility Test

- 외부 머신에서 `git clone` → `make reproduce` → 동일 결과
- Seed 고정, 데이터 hash 검증

-----

## §9. Open Questions for Iteration

### §9.1 Methodology

- Q1: Mythos 발표 효과와 T+1 (2026-04-08) 크립토 시장 전반 변동성 효과의 분리 전략?
- Q2: AI 에이전트 프록시의 validity 검증 gold standard는?
- Q3: SVB 모델 파라미터 calibration 시 prior 설정의 민감도?

### §9.2 Technical

- Q4: Dune rate limit 도달 시 대안 (The Graph? Alchemy?)
- Q5: ABM 5000 에이전트의 병렬화 필요성?
- Q6: 한국어 뉴스(블록미디어, 코인니스)도 감정 분석에 포함?

### §9.3 Scope

- Q7: Wave 2로 한국 원화 페그 KRW 스테이블코인 관련 법안 추적?
- Q8: MiCA (EU) regime 비교 분석을 E28에 포함?
- Q9: Project Glasswing 12개 파트너 기업의 주가·CDS 이벤트 스터디 추가?

### §9.4 Dissemination

- Q10: 결과 발표 플랫폼 (SSRN vs arXiv vs 학회)?
- Q11: 정책 브리프의 최적 타이밍 (FDIC final rules 전/후)?
- Q12: 코드베이스 오픈소스화 라이선스 (MIT vs Apache 2.0)?

-----

## Appendix A. Claude Code Execution Notes

### A.1 Session Strategy

- Agent A: `src/ingest/` 구현 (혼자 진행 가능)
- Agent B: `src/entropy/` + 테스트 (A와 병렬)
- Agent C: `src/event_study/` (A, B 완료 후)
- Agent D: `src/abm/` (독립, 병렬 가능)
- Orchestrator: 메인 세션에서 통합, ADR 작성, 결정

### A.2 Context Handoff Pattern (from Harness Engineering book)

각 세션 종료 시 `docs/session_log/YYYYMMDD_agent_X.md` 작성:

- 완료한 작업
- 미완 작업 + 다음 agent가 이어받을 지점
- 남은 open questions
- 주요 decision points

### A.3 Cost Guardrails

- Claude API 호출은 해석·narrative 생성에만
- 수치 계산·시뮬레이션은 전부 로컬 Python
- Nightly recalibration은 Claude API 없이 실행
- 주간 digest 생성 시에만 Claude API 호출 (1회/week, ≤ 10k tokens)

-----

*End of PROJECT_SPEC.md v0.1. Companion document: EXPERIMENT_DESIGN_E23-E27.md*
