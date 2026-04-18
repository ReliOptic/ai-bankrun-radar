# ADR-007: Two-set experiment structure (실험 1 / 실험 2)

- **Status**: Accepted
- **Date**: 2026-04-18
- **Depends on**: ADR-006
- **Affects**: PROJECT_SPEC §1.1, §4.1, §6, Appendix A.1; EXPERIMENT_DESIGN.md 전체

## Context

ADR-006으로 관측 대상이 AI 에이전트로 재정의된 후, 5개 실험(E23-E27) 사이의 논리적 위계가 달라졌다. v0.1의 평면적 E23-E27 나열은 **무엇이 main claim을 결정하고 무엇이 보조하는지** 명시하지 않아 보고서·마일스톤·세션 전략 모두에서 우선순위 혼선을 유발한다.

## Decision

다섯 실험을 목적 단위로 두 세트로 나눈다.

### 실험 1 — Direct Hypothesis Test (primary)

- **구성**: E23 (foundation) → E26 (primary DiD)
- **목적**: Core Hypothesis "AI 에이전트 행동 엔트로피가 Mythos 이후 급락한다"를 직접 측정·검정
- **출력**: 본 프로젝트의 main result
- **성공 조건**: E26의 3-arm DiD에서 `ΔH_agent` vs `ΔH_human`, vs `ΔH_MEV` 의 유의성 판정 (지지/기각 무관, 결론이 명확할 것)

### 실험 2 — Triangulation & Simulation (supporting)

- **구성**: E24 (asset channel) + E25 (network) + E27 (SVB ABM)
- **목적**: 실험 1의 결론을 세 개의 독립 관측축(자산 표면, 상관 구조, 반사실 시뮬레이션)에서 교차검증
- **출력**: Robustness appendices + policy brief evidence
- **성공 조건**: 세 실험 모두 실험 1과의 방향 일치 여부를 명시적으로 판정. 유의성 자체가 성공 조건은 아님.

### 보고 규율

실험 2의 각 실험 보고서 상단에는 **"실험 1과 방향 일치 여부"** 테이블이 반드시 포함된다. 실험 2는 독립 결론으로 보고되지 않는다.

## Consequences

### Positive

- Main claim이 어디서 결정되는지 문서·코드·일정 모두에서 단일화
- 실험 2의 세 실험이 서로 중복 보고하지 않고 각자의 관측축을 명료화
- Phase 3 (Week 5-7)이 Phase 2 (Week 3-4)보다 먼저 와야 했던 v0.1의 시퀀싱 오류 해소

### Negative / Costs

- E23·E26에 리소스가 집중되어 실험 2의 엔지니어링 시간 압박 가능
- 실험 2 결과가 실험 1과 충돌할 때의 weighting 규칙이 미정 (OQ-16으로 이관)

### Milestone resequencing

PROJECT_SPEC §6 재배열:
- Phase 1 → 실험 1 Foundation (E23 calibration)
- Phase 2 → 실험 1 Primary (E26 pre-registration + pre-window analysis)
- Phase 3 → 실험 2 (E24, E25 병렬; E27은 E23 결과 의존 후 시작)
- Phase 4 → Synthesis (논문·정책 브리프)

### Directory restructure (§4.1)

```
experiments/
├── set1_direct/
│   ├── E23_agent_id/
│   └── E26_agent_entropy/
└── set2_triangulation/
    ├── E24_asset_channel/
    ├── E25_network/
    └── E27_svb_abm/
```

### Session strategy (Appendix A.1) re-assignment

- Agent A: `src/ingest/` (both sets)
- Agent B: `src/agent_id/` (실험 1 Foundation, 최우선)
- Agent C: `src/entropy/` (실험 1 Primary)
- Agent D: `src/event_study/` + `src/network/` (실험 2 concurrent)
- Agent E: `src/abm/` (실험 2, E23 결과 의존)
- Orchestrator: 세트 간 통합, 실험 1 → 실험 2 방향 일치 보고 규율 감시

## Open items

- OQ-16: 실험 2 세 실험 중 하나만 실험 1과 충돌할 때의 weight 부여 규칙
