# ADR-006: Reframe observation target from stablecoin behavior to AI agent behavior

- **Status**: Accepted
- **Date**: 2026-04-18
- **Supersedes (partial)**: PROJECT_SPEC v0.1 §1.1, §3.1-F2, §3.1-F5
- **Related**: ADR-001..005

## Context

PROJECT_SPEC v0.1은 관측 대상 모집단(population)을 암묵적으로 "스테이블코인 시장"으로 잡았다. 원래 덱의 Core Hypothesis는 **AI 에이전트의 행동 엔트로피 급락**이지, 스테이블코인 가격 행동이 아니었다. 대상 모집단을 잘못 잡으면 어떤 식별 전략도 가설과 무관한 것을 측정하게 된다.

핵심 장벽: AI 에이전트는 EOA와 온체인에서 겉보기에 구분되지 않는다. 블록체인은 트랜잭션이 LLM 호출로 생성됐는지 사람이 지갑 앱을 눌러서 생성했는지 기록하지 않는다. 따라서 첫 번째 식별 질문은 "Mythos 효과 vs 변동성 효과 분리"가 아니라 **"AI 에이전트 트랜잭션을 어떻게 라벨링할 것인가"** 이다.

## Decision

### D1. 관측 대상 재정의

- **Population**: AI 에이전트 (LLM 기반 자율 트랜잭션 발신자)
- **Primary DV**: `H_agent(t)` = AI 에이전트 트랜잭션 행동의 Shannon 엔트로피
- **Stablecoin의 역할**: 에이전트가 움직이는 자산 표면(asset surface), 즉 관측 채널. 관측 대상 아님.
- **Secondary DV**: `H_asset(t)` (v0.1의 `H_stable(t)`)는 맥락 증거(context evidence)로 유지.

### D2. 실험 우선순위 재배치

| 실험 | v0.1 위상 | v0.2 위상 |
|------|-----------|-----------|
| E24 (event study) | 주 실험 (DV = H_stable) | 맥락 증거 (DV = H_asset), 보조 |
| E26 (monoculture / agent proxy) | 부록격 보조 | **주 실험** (DV = H_agent) |
| E25 (correlation) | 주 실험 | 유지, but AI-agent subset에도 적용 |
| E23, E27 | 변화 없음 | 변화 없음 |

### D3. 두 층 식별 전략 (Two-Layer Identification)

**Layer 1 — Narrow but Certain**

- Self-declared AI agent 프로토콜의 온체인 활동
  - Virtuals Protocol (AI agents as tokens)
  - Fetch.ai agents
  - Olas / Autonolas
  - Bittensor subnet participants
- ERC-4337 paymaster 경유 트랜잭션 중 특정 AI agent framework 시그니처 (Coinbase OnchainKit, Alchemy AA 등)
- Farcaster `client: bot` 또는 self-identified AI agent 계정 (Neynar bulk API)
- N: 수천 계정 규모. 라벨 확실.

**Layer 2 — Wide but Uncertain**

- Layer 1을 supervised training label로 사용하여 behavioral fingerprinting 분류기 학습
  - 트랜잭션 간격의 균일성 (cron-scheduled 시그니처)
  - 24/7 활동 패턴 (인간 수면 시간 부재)
  - Gas price optimization 패턴
  - 복잡한 multi-hop transaction을 초 단위로 구성
- 전체 EOA에 AI-agent-score 부여, threshold로 "high-confidence AI" 분리.

**Cross-validation logic**

- Layer 1과 Layer 2가 **같은 방향** → 신뢰성 확보
- **다른 방향** → 식별 방법에 따라 결론 다름을 정면으로 명시. 양쪽 결과 모두 보고.

### D4. DiD 구조 재설계 (3-arm)

| Arm | 정의 | 식별 원천 |
|-----|------|-----------|
| Treatment | Layer 1 AI agents | Virtuals / Fetch.ai / Olas / Neynar bot labels |
| Control 1 | Farcaster verified human-only accounts | Neynar bulk API + verification filter |
| Control 2 | MEV searcher bots (non-LLM automation) | EigenPhi, libMEV public classification |

**식별 논리**:
- `ΔH(AI) - ΔH(human)` 유의 → AI 특이적 효과
- `ΔH(AI) - ΔH(MEV)` 유의 → "LLM-specific" 효과 (단순 자동화가 아님)
- 둘 다 유의하지 않음 → "공통 정보 충격" 가설 채택, AI 동조화 가설 기각

### D5. 솔직한 한계 명시 (N3.2 준수)

가장 영향력 있는 AI 에이전트(기관 운영 헤지펀드용 LLM 트레이더 등)는 Layer 1/2 어디에도 들어오지 않는다. Layer 1은 "공개 실험실급" AI 에이전트에 한정되고, 시장을 실제로 움직일 규모의 에이전트는 보이지 않을 가능성이 높다. 논문·정책 브리프 모두에서 이 한계를 정면으로 명시한다 (§7 Risks에 추가).

## Consequences

### Positive

- 측정량이 Core Hypothesis와 정렬된다 (agent 행동 엔트로피 ↔ agent monoculture)
- 3-arm DiD가 "공통 정보 충격 vs LLM-특이 효과"를 식별 가능하게 만든다
- Layer 1/2 교차검증이 식별 불확실성을 반감적(self-refuting) 검증으로 전환한다

### Negative / Costs

- 데이터 수집 범위 확대: Virtuals, Fetch.ai, Olas, ERC-4337 logs, EigenPhi, libMEV 추가
- F5 (Agent Proxy)가 주 실험 인프라로 격상, 엔지니어링 부하 증가
- ML 분류기 요구 → §8.1 Unit Tests에 분류기 precision/recall 테스트 추가 필요
- Institutional AI blind spot (D5)로 인해 결론의 external validity 제한

### Data access viability (확인 완료)

- Virtuals Protocol 온체인: Dune dashboards 다수 존재 → 가능
- Fetch.ai / Olas: Cosmos 체인, API 제공 → 가능
- ERC-4337 paymaster events: Etherscan event logs → 가능
- Farcaster AI bot labels: Neynar `/user/bulk` API → 가능
- MEV searcher labels: EigenPhi, libMEV public data → 가능

### Spec sections affected

- §0.2 Observation target (명시 필요)
- §1.1 Scope: stablecoin을 channel로 재분류, AI agent identification 명시적 in-scope
- §3.1 F2: H_agent를 primary DV로 승격
- §3.1 F3: DiD arms 재정의
- §3.1 F5: "Agent Proxy" → "AI Agent Identification & Behavioral Entropy" (primary)
- §5.1 External APIs: EigenPhi, libMEV, Virtuals dashboard IDs, Olas endpoints 추가
- §7 Risks: institutional AI blind spot 추가
- §9.1 Q2: 본 ADR의 cross-validation으로 부분 해결, 잔여 Q13으로 이관

## Open items spawned by this ADR

- **OQ-13**: Behavioral fingerprinting 분류기의 false-positive rate 허용 상한은? (권고 시작점: ≤ 10% on Layer 1 held-out)
- **OQ-14**: Layer 1 / Layer 2 결과가 상반될 때 논문에서 어떤 결론을 main result로 제시할지 사전 등록(pre-registration)이 필요한가?
- **OQ-15**: MEV searcher와 LLM-driven arbitrage agent의 경계 사례 처리 규칙?
