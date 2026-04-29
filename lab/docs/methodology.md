# 방법론 문서 (Methodology)

**논문 제목**: Signal Governance: An AI-Era Integration of Diamond-Dybvig, Gorton-Pennacchi, Acemoglu, and Shannon Frameworks for Synchronized Bank Run Detection

**저자**: Kiwon Cho, KAIST PMBA / ZEISS Korea

**문서 위치**: 본 문서는 논문 §3(이론적 프레임워크) 및 §4(실험 설계)의 anchor이며, Supplementary Material S2의 상세 사양 출처로 기능한다.

**최종 수정일**: 2026-04-29

---

## §0. 한 문단 요약

본 연구는 AI 에이전트가 금융 의사결정의 핵심 행위자로 편입되는 시대에 뱅크런(bank run) 메커니즘이 어떻게 구조적으로 변형되는지를 이론적으로 정식화하고 실험실 환경에서 검증하는 가설 검증 프레임워크를 제시한다. Diamond-Dybvig(1983)의 2기간 예금 계약 이론, Gorton-Pennacchi(1990)의 정보 비민감성(information-insensitivity) 분석, Acemoglu et al.(2015)의 금융 네트워크 전파 모형, 그리고 Shannon(1948)의 정보 엔트로피 이론을 통합하여, **유효 기반 모형 다양성** $K_{\text{eff}} = \exp(H_{\text{action}})$이 감소할수록 협조 실패(coordination failure) 확률이 임계값 이하의 외생적 충격 수준에서도 급격히 상승함을 이론적으로 도출한다. 이 주장을 검증하기 위해 대형 언어 모형(LLM) 에이전트 군집 시뮬레이터를 구축하고, 3차원 직교 파라미터 공간에서 8개 실험 셀을 실행하며, 사전등록(pre-registration)·프롬프트 중립성·모형 교체 강건성 검사를 포함한 5개의 객관성 서약(objectivity commitment)을 준수함으로써 결과의 재현 가능성과 반증 가능성을 확보한다.

---

## §1. 연구 목표 및 Contribution 분리

### §1.1 두 가지 Contribution

본 연구의 학술적 기여는 성격이 서로 다른 두 층위로 구분된다. 이 구분은 심사 과정에서 두 기여가 혼동되어 평가받는 것을 방지하기 위해 명시적으로 유지된다.

**Contribution 1 — 4-모형 AI 시대 통합 프레임워크 (이론적 기여, 약 40%)**

기존 뱅크런 문헌은 기초 자산의 외생적 불확실성(fundamental uncertainty)을 중심으로 발전해 왔다. Diamond-Dybvig(1983)는 유동성 변환 계약의 내생적 다중 균형을 분석하였고, Gorton-Pennacchi(1990)는 안전 부채(safe debt) 생산의 조건으로 정보 비민감성 개념을 정식화하였다. 이후 Acemoglu et al.(2015)은 금융 네트워크의 위기 전파 임계값을 엄밀하게 분석하였다. 그러나 이 세 문헌 계보 중 어느 것도 AI 에이전트가 상호 연결된 신호 생산자(signal producer)이자 소비자(signal consumer)로 기능하는 상황을 명시적으로 다루지 않는다. 본 연구는 Shannon 엔트로피를 행동적 다양성의 자연스러운 측도로 도입함으로써 이 공백을 채우고, 네 이론을 단일 분석 구조 안에서 결합한 **신호 거버넌스 프레임워크(Signal Governance Framework)**를 제안한다.

**Contribution 2 — 실험실 검증 결과 (실증적 기여, 약 60%)**

이론에서 도출된 핵심 예측, 즉 "$K_{\text{eff}}$ 감소가 임계값 미만 충격 영역에서도 뱅크런 확률을 인과적으로 증가시킨다"는 명제를 LLM 에이전트 군집 시뮬레이터를 통해 검증한다. 이 기여는 결과 그 자체보다 **실험 설계의 객관성 인프라**가 핵심이다. 프롬프트 중립성, 사전등록, 반증 가능한 귀무가설 설정, 다중 LLM 교체 검사를 포함하는 설계 원칙은 생성형 AI를 사용한 사회과학 실험 일반에 방법론적 표준을 제시하는 것을 부차 목표로 한다.

### §1.2 본 문서의 위치

본 방법론 문서는 투고 논문의 다음 구조와 대응한다.

- 논문 **§3 (이론적 프레임워크)**: 본 문서 §2의 요약본
- 논문 **§4 (실험 설계)**: 본 문서 §3–§6의 요약본
- 논문 **§5 (통계 분석)**: 본 문서 §7의 요약본
- **Supplementary Material S2 (상세 실험 사양)**: 본 문서 §6 전체를 그대로 수록
- **Supplementary Material S3 (재현성 인프라)**: 본 문서 §8 전체를 수록

---

## §2. 이론적 통합 프레임워크

### §2.1 Diamond-Dybvig 2기간 계약 및 임계값 $\theta_{\text{DD}}$

Diamond-Dybvig(1983)의 표준 설정을 간략히 재현한다. 경제에는 세 시점 $t \in \{0, 1, 2\}$가 있다. $t=0$에서 은행은 $N$명의 예금자로부터 1단위씩 예금을 수취하고 비유동 자산에 투자한다. 자산은 $t=2$에 총수익 $R > 1$을 실현하지만, $t=1$에 청산하면 $c_1 < 1$의 조기 청산가치만 갖는다. 예금자 유형은 다음의 두 가지이다. 조기 소비자(impatient type, 비율 $f$)는 $t=1$에만 효용을 얻으며, 지연 소비자(patient type)는 $t=2$까지 대기할 수 있다.

Diamond-Dybvig 계약은 $t=1$ 인출에 $r_1 > 1$을 지급하고 잔존 예금자에게는 $t=2$에 $r_2$를 지급한다. 지속 가능성 조건에서 $r_2 = (1 - f \cdot r_1) \cdot R / (1 - f)$이다. 뱅크런이 발생하지 않는 조건은 patient-type 예금자가 대기를 선택할 유인이 존재하는 것인데, 이를 위해서는 인출 행렬에서의 기대수익이 $r_2 > r_1$을 만족해야 한다.

선형화된 payoff 설정에서, patient type이 조기 인출을 선택하는 동인은 충분히 많은 다른 예금자가 인출할 것이라는 기대이다. Goldstein and Pauzner(2005)의 global games 확장에서 이 임계 비율을 형식화하면 다음과 같다.

$$f_{\text{critical}} = \frac{R - r_1}{r_1 \cdot (R - 1)}$$

이 분수가 의미하는 것은, 조기 인출자 비율이 $f_{\text{critical}}$을 초과하는 순간 은행의 지급 능력이 훼손된다는 것이다. 좌변의 분자 $(R - r_1)$은 투자 수익률 프리미엄이고, 분모 $r_1 \cdot (R - 1)$은 조기 인출 1단위당 장기 수익 희생분이다. 따라서 $r_1$이 클수록, 즉 조기 유동성 보장이 클수록 $f_{\text{critical}}$이 낮아져 소수의 이탈만으로도 뱅크런이 촉발된다.

본 연구의 모형에서는 이 임계값을 Diamond-Dybvig 협조 임계값으로 정의한다.

$$\theta_{\text{DD}} = f_{\text{critical}} = \frac{R - r_1}{r_1 \cdot (R - 1)}$$

AI 에이전트 설정에서 각 에이전트의 인출 결정은 자신이 보유한 신호와 타 에이전트의 예상 행동에 대한 믿음에 기반한다. 고전 설정과의 핵심 차이는 AI 에이전트들이 동일한 기반 모형(foundation model)에서 파생되었을 때 이 믿음이 구조적으로 상관될 수 있다는 점이다.

### §2.2 Gorton-Pennacchi 정보 비민감성 및 비용 구조

Gorton-Pennacchi(1990)는 안전 부채가 거래 가능하기 위한 조건으로 **정보 비민감성(information-insensitivity)**을 제시한다. 이 개념의 핵심은 다음과 같다. 부채 증권이 발행자의 기초 자산 가치 $V$에 대해 민감하지 않을 때, 즉 $\partial \text{Debt Price} / \partial V \approx 0$일 때, 정보 비대칭을 가진 거래 상대방과의 역선택(adverse selection) 문제 없이 거래가 성립한다.

정보 비민감성이 붕괴하는 조건을 간략히 정식화한다. 정보 생산 비용을 $c$라 하고, 정보를 생산했을 때의 기대 차익거래 이익을 $\pi(c)$라 하면, 시장은 $\pi(c) > c$인 경우에 한해 정보 민감 거래자(information-sensitive trader)를 끌어들인다. Gorton-Pennacchi(1990)는 초기 안전 부채 설계가 $\pi(c) < c$인 영역에 부채 가격을 위치시키도록 구조화된다는 것을 보인다.

AI 에이전트 맥락에서 이 분석은 다음과 같이 재해석된다. AI 에이전트가 정보 생산자로 기능할 때, 단일 기반 모형(즉 $K_{\text{eff}} = 1$)을 공유하는 에이전트 군집은 사실상 **단일한 대형 정보 생산자**를 구성한다. 이 경우 기존의 분산된 정보 생산 구조가 해체되고, 정보가 동시에 동방향으로 생산됨으로써 $\pi(c)$가 급격히 상승한다. 즉, $K_{\text{eff}}$ 감소는 정보 비민감성 영역을 축소시키고 동질화된 신호 공간을 만들어낸다. 이 메커니즘은 §2.5의 $\alpha(K_{\text{eff}})$ 증폭 인수의 직접적 동기를 제공한다.

### §2.3 Acemoglu et al. 네트워크 전파 및 허브 집중

Acemoglu et al.(2015)은 금융 네트워크를 유향 가중 그래프 $\mathcal{G} = (V, E, w)$로 표현하고, 시스템적 위험의 전파가 두 가지 상이한 체제(regime)에서 발생함을 보인다.

**희박 충격 체제(sparse shock regime)**: 충격이 소수 은행에 국한되고 연결 강도가 낮을 때, 네트워크 연결성은 위험 분산(risk-sharing)으로 기능하여 시스템 안정성을 증진시킨다.

**집중 충격 체제(concentrated shock regime)**: 충격이 허브(hub) 노드에 집중되거나 상호 노출(mutual exposure)이 높아질 때, 동일한 연결 구조가 전염(contagion)을 가속화한다.

임계 조건은 연결 행렬의 최대 고유값 $\lambda_{\max}(\mathbf{W})$와 충격 크기의 곱으로 표현된다. $\lambda_{\max}(\mathbf{W}) \cdot \sigma_{\text{fund}} > \kappa_{\text{cascade}}$가 성립하면 연쇄 부도가 발생한다.

본 연구의 AI 에이전트 설정에서 이 네트워크 전파 논리는 **행동적 상관(behavioral correlation)**을 통해 재활성화된다. 동일 기반 모형을 사용하는 에이전트들은 대차대조표 연결 없이도 행동적으로 허브를 구성한다. 구체적으로, 단일 기반 모형 클러스터 내 에이전트들의 인출 결정 상관계수 $\rho_{\text{intra}}$가 높아지면, Acemoglu의 허브 집중 조건이 물리적 네트워크가 아닌 행동 공간에서 충족된다. 이 재해석이 고전 모형에서 AI-era 모형으로의 이행을 가능하게 하는 핵심 논리이다.

### §2.4 Shannon 엔트로피를 행동적 다양성 측도로

Shannon(1948)은 이산 확률 분포 $P = (p_1, p_2, \ldots, p_K)$의 정보 엔트로피를

$$H(P) = -\sum_{k=1}^{K} p_k \log_2 p_k$$

로 정의하였다. 이 측도는 분포의 불확실성 또는 다양성을 나타내며, $K$가 균등 분포일 때 최대값 $\log_2 K$를 갖는다.

본 연구에서는 Shannon 엔트로피를 에이전트 행동 공간의 다양성 측도로 적용한다. $N$명의 에이전트가 인출 여부를 결정할 때, 각 에이전트의 결정 규칙은 해당 에이전트가 사용하는 기반 모형의 추론 패턴에 의존한다. 기반 모형 $k$를 사용하는 에이전트 비율을 $p_k$라 하면, 행동 분포의 엔트로피는

$$H_{\text{action}} = -\sum_{k=1}^{K} p_k \log p_k$$

로 계산된다. 여기서 자연로그 기반을 사용하면 **유효 다양성 수** (Hill number of order 1)는

$$K_{\text{eff}} = \exp(H_{\text{action}})$$

가 된다. 이 수치는 주어진 행동 다양성과 동등한 Shannon 엔트로피를 갖는 균등 분포의 카테고리 수, 즉 실질적으로 독립적으로 행동하는 에이전트 군집의 수를 나타낸다.

이 정의의 핵심 성질은 다음과 같다. 모든 에이전트가 동일 기반 모형을 사용하면 $H_{\text{action}} = 0$이고 $K_{\text{eff}} = 1$이다. 에이전트들이 $K$개의 서로 다른 기반 모형을 균등하게 사용하면 $K_{\text{eff}} = K$이다. 비균등 분포에서는 항상 $K_{\text{eff}} < K$이다. 이 측도는 단순한 기반 모형 수보다 훨씬 정보량이 많으며, 시장 참여자의 실질적 다양성을 포착한다.

기존 금융 안정성 문헌에서 다양성 측도로 Herfindahl-Hirschman Index(HHI)가 사용된 바 있으나, HHI = $\sum p_k^2$는 크기 집중도를 측정하며 Shannon 엔트로피와 단조적 관계($H = -\log \text{HHI}$는 근사)에 있다. 본 연구가 $K_{\text{eff}} = \exp(H)$를 선택하는 이유는 이 형식이 Hill number 이론과 일치하며, 후술하는 증폭 함수 $\alpha(K_{\text{eff}}) = 1 + \lambda / K_{\text{eff}}$의 분석적 처리를 단순화하기 때문이다.

### §2.5 통합: 유효 행동 다양성 $K_{\text{eff}}$

앞 네 절의 결과를 통합하여 단일 분석 구조를 도출한다.

에이전트 $i$는 두 가지 유형의 신호를 수신한다. **공통 신호(common signal)** $s_{\text{common}}^{(k)}$는 클러스터 $k$의 모든 에이전트가 공유하며, 해당 클러스터의 기반 모형에서 생성된다. **개별 신호(idiosyncratic signal)** $s_{\text{idio}}^{(i)}$는 에이전트 $i$ 고유의 잡음이다.

에이전트 $i$의 은행 건전성 사후 인식(perceived bank health)은

$$\hat{v}_i = v + \underbrace{\eta_k}_{\text{공통 충격}} + \underbrace{\varepsilon_i}_{\text{개별 잡음}}$$

로 표현된다. 여기서 $\eta_k \sim \mathcal{N}(0, \sigma_{\text{cluster}}^2)$는 클러스터 $k$ 수준의 공통 오차이고, $\varepsilon_i \sim \mathcal{N}(0, \sigma_{\text{idio}}^2)$는 개별 잡음이다.

$K_{\text{eff}}$가 감소하면, 즉 에이전트 군집이 소수의 기반 모형 클러스터에 집중되면, 공통 충격 $\eta_k$에 노출되는 에이전트 수가 증가하고 결과적으로 집합적 인식 오차의 분산이 커진다. 이를 외생적 기초 충격 $\sigma_{\text{fund}}$와의 상호작용으로 표현하면, 집합적으로 지각되는 충격 크기는

$$\tilde{\sigma}_{\text{eff}} = \sigma_{\text{fund}} \cdot \alpha(K_{\text{eff}}), \quad \alpha(K_{\text{eff}}) = 1 + \frac{\lambda}{K_{\text{eff}}}, \quad \lambda > 0$$

가 된다. 이 증폭 인수 $\alpha(K_{\text{eff}})$는 다음 세 가지 이론적 요소를 동시에 포착한다.

1. **Diamond-Dybvig 임계값 접근**: 집합적 충격 지각이 $\theta_{\text{DD}}$에 가까워짐
2. **Gorton-Pennacchi 정보 동질화**: 단일 신호 원천으로의 수렴이 정보 비민감성 영역을 축소
3. **Acemoglu 행동적 허브**: 클러스터 내 $\rho_{\text{intra}}$ 증가가 전파 조건 $\lambda_{\max} > \kappa$를 충족시킴

### §2.6 명제 1: 정식 서술, 증명 개요, 직관적 해석

#### 정식 서술

**명제 1 (유효 AI 다양성과 뱅크런 확률)**

설정: $N$명의 예금자-에이전트가 $K_{\text{eff}} = \exp(H_{\text{action}})$개의 유효 기반 모형 클러스터에 분포한다. 은행 기초 충격 크기 $\sigma_{\text{fund}} \in [0, 1]$. 개별 의사결정 잡음 표준편차 $\sigma_{\text{idio}} > 0$. Diamond-Dybvig 협조 임계값 $\theta_{\text{DD}} = (R - r_1) / (r_1 \cdot (R-1))$.

**주장**:

$$P(\text{run} \mid \sigma_{\text{fund}}, K_{\text{eff}}) \geq \Phi\!\left(\frac{\sigma_{\text{fund}} \cdot \alpha(K_{\text{eff}}) - \theta_{\text{DD}}}{\sigma_{\text{idio}}}\right)$$

여기서 $\alpha(K_{\text{eff}}) = 1 + \lambda / K_{\text{eff}}$, $\lambda > 0$, $\Phi(\cdot)$는 표준 정규 누적 분포 함수이다.

#### 증명 개요

이 부등식은 다음의 세 단계 논증으로 도출된다.

**단계 1 — 신호 집합화(signal aggregation)**: 클러스터 $k$ 내 에이전트들은 공통 신호 $s_k$에 가중치 $w_k = \sigma_{\text{cluster}}^2 / (\sigma_{\text{cluster}}^2 + \sigma_{\text{idio}}^2)$를 부여하는 Bayesian 업데이트를 수행한다. $K_{\text{eff}}$가 감소하면 대다수 에이전트가 소수의 $s_k$에 의존하게 되어 집합적 인식은 사실상 소수 공통 신호의 선형 결합에 수렴한다.

**단계 2 — 유효 충격 크기 하한(effective shock lower bound)**: 집합적 인출 결정 함수를 $D(\hat{v}_i) = \mathbf{1}[\hat{v}_i < \theta_{\text{DD}}]$로 정의하면, 총 인출 비율은

$$\bar{D} = \frac{1}{N} \sum_{i=1}^N D(\hat{v}_i) \approx \Phi\!\left(\frac{\theta_{\text{DD}} - v}{\sigma_{\text{eff}}}\right)$$

를 만족한다. 여기서 $\sigma_{\text{eff}} \geq \sigma_{\text{idio}} / \alpha(K_{\text{eff}})^{-1}$의 하한이 성립한다. $K_{\text{eff}} \to 1$일 때 $\sigma_{\text{eff}} \to \infty$가 아닌 대신 집합적 이탈 확률이 $\Phi((\sigma_{\text{fund}} \cdot \alpha - \theta_{\text{DD}}) / \sigma_{\text{idio}})$로 하한을 가짐을 보인다.

**단계 3 — 임계값 교차(threshold crossing)**: 뱅크런 발생 조건은 $\bar{D} > f_{\text{critical}} = \theta_{\text{DD}}$이다. 이 조건의 확률이 명제의 우변 $\Phi$식으로 하한이 됨을 표준 정규 집중 부등식(sub-Gaussian concentration)으로 보인다. $\square$ (상세 증명은 Supplementary S1 참조)

#### 직관적 해석

명제 1의 핵심 직관은 다음과 같다. $K_{\text{eff}} = 10$인 환경에서는 에이전트들이 10가지 독립적 추론 패턴을 사용하므로 개별 신호 오차가 집계 과정에서 상쇄된다. 그러나 $K_{\text{eff}} = 1$이 되면 전체 에이전트가 동일한 오차 방향으로 움직이고, $\sigma_{\text{fund}}$의 실질적 '증폭도'는 $\alpha(1) = 1 + \lambda$에 달한다. 이것이 임계값 미만의 기초 충격(sub-critical fundamental shock)에서도 런이 발생할 수 있음을 의미하며, 이 현상을 **AI 모노컬처 증폭(AI monoculture amplification)**이라 명명한다.

이 명제는 Shannon 엔트로피를 다양성 측도로 사용하는 것의 필연성을 함의한다. 기반 모형 수만 세는 단순 카운트 $K$와 달리, $K_{\text{eff}} = \exp(H)$는 각 모형을 실제로 사용하는 에이전트 비율을 반영한다. 시장의 70%가 단일 기반 모형을 사용하고 나머지 30%가 9개 모형에 분산되어 있다면, $K_{\text{eff}} \approx 2.7$이지 10이 아니다.

### §2.7 4-모형 통합 다이어그램 (텍스트 표현)

아래 다이어그램은 네 이론이 통합 프레임워크에서 맡는 역할을 구조적으로 표현한다.

```
외생적 기초 충격
σ_fund ∈ [0,1]
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  SHANNON (측정 계층)                                              │
│  H_action = -Σ p_k log p_k                                      │
│  K_eff = exp(H_action)                → 행동적 다양성 수치화     │
└─────────────────────────┬───────────────────────────────────────┘
                          │ α(K_eff) = 1 + λ/K_eff
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  GORTON-PENNACCHI (정보 계층)                                     │
│  K_eff 감소 → 정보 동질화 → 정보 비민감성 붕괴                    │
│  단일 신호 원천 수렴 → π(c) > c 조건 충족                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │ 증폭된 유효 충격: σ_fund · α(K_eff)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  ACEMOGLU et al. (전파 계층)                                      │
│  ρ_intra 상승 → 행동적 허브 형성                                  │
│  λ_max(행동 상관 행렬) > κ_cascade → 연쇄 이탈 촉발             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ 집합적 이탈 비율 Ā
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  DIAMOND-DYBVIG (임계값 계층)                                     │
│  θ_DD = (R - r1) / (r1 · (R - 1))                               │
│  Ā > θ_DD → 뱅크런 균형 (coordination failure)                  │
│  P(run) ≥ Φ((σ_fund·α(K_eff) - θ_DD) / σ_idio)                │
└─────────────────────────────────────────────────────────────────┘
```

이 다이어그램에서 Shannon은 **측정 계층**으로 AI 다양성을 수치화하고, Gorton-Pennacchi는 **정보 계층**에서 동질화가 정보 구조에 미치는 영향을 포착하며, Acemoglu는 **전파 계층**에서 행동 상관이 어떻게 연쇄를 촉발하는지를 설명하고, Diamond-Dybvig는 **임계값 계층**에서 뱅크런 균형이 실현되는 조건을 제공한다.

---

## §3. 실험실 아키텍처

### 3.1 World Clock 및 T-step 시뮬레이터

시뮬레이터는 이산 시간 스텝 $t = 1, 2, \ldots, T$로 진행된다. 각 스텝은 다음의 순서적 서브-루틴으로 구성된다.

1. **신호 생성(signal generation)**: 정보 환경 모듈이 친-런(pro-run) 신호 및 반-런(anti-run) 신호를 에이전트에 배포한다.
2. **Bayesian 업데이트**: 각 에이전트가 수신 신호와 사전 믿음(prior)을 결합하여 은행 건전성 사후 분포를 업데이트한다.
3. **의사결정**: 에이전트가 인출 또는 대기를 선택한다. LLM 에이전트의 경우 표준화된 프롬프트 템플릿에 현재 신호와 이전 스텝 관찰을 입력하여 결정을 출력한다.
4. **은행 상태 갱신**: 인출 비율 $\bar{D}_t$를 계산하고, $\bar{D}_t > f_{\text{critical}}$이면 은행 파산 이벤트를 발화한다.
5. **지표 기록**: 메트릭 레코더가 해당 스텝의 모든 측정값을 저장한다.

World Clock는 시뮬레이션 전체에 걸쳐 단조 증가하는 타임스탬프를 유지하며, 이는 재현성 감사(reproducibility audit) 시 각 LLM API 호출과 매핑하는 데 사용된다.

### 3.2 Bank 모듈 (Diamond-Dybvig 계약 인스턴스화)

Bank 모듈은 다음의 파라미터로 초기화된다.

- 예금자 수 $N$, 장기 수익률 $R$, 단기 인출 수익률 $r_1$
- 이로부터 자동 계산: $\theta_{\text{DD}} = (R - r_1) / (r_1 \cdot (R-1))$
- 잔여 지급 여력 추적: $\text{Liquidity}_t = 1 - \sum_{\tau \leq t} \bar{D}_\tau \cdot r_1$

파산 이벤트는 $\text{Liquidity}_t < 0$ 또는 $\bar{D}_t > \theta_{\text{DD}}$ 중 하나가 먼저 충족될 때 발화된다. 파산 이벤트 발화 시점은 뱅크런 발생의 1차 종속변수이다.

### 3.3 에이전트 군집 ($N$ 에이전트, $K$ 클러스터, $\rho_{\text{intra}}/\rho_{\text{inter}}$)

에이전트 군집은 3개의 계층으로 구성된다.

**클러스터 할당**: 에이전트 $i$는 사전 지정된 확률 분포 $(p_1, \ldots, p_K)$에 따라 클러스터 $k \in \{1, \ldots, K\}$에 배정된다. 균등 분포 설정 ($p_k = 1/K$)이 기본값이다.

**클러스터 내 상관 구조**: 클러스터 $k$ 내 에이전트들의 충격 벡터는 분산-공분산 행렬 $\Sigma_k$를 따른다. 대각 원소는 $\sigma_{\text{idio}}^2$이고, 비대각 원소는 $\rho_{\text{intra}} \cdot \sigma_{\text{idio}}^2$이다.

**클러스터 간 상관**: 서로 다른 클러스터 $k \neq k'$의 에이전트 충격 간 공분산은 $\rho_{\text{inter}} \cdot \sigma_{\text{idio}}^2$이다. 실험 기본값은 $\rho_{\text{intra}} = 0.7$, $\rho_{\text{inter}} = 0.1$이다.

**LLM 에이전트 구현**: 각 에이전트는 클러스터 $k$에 해당하는 기반 모형(GPT-4, Claude, Llama, Mistral 중 하나)을 사용하며, 표준화된 중립 프롬프트 템플릿에서 인출 결정을 생성한다.

### 3.4 정보 환경 (신호 혼합, 기본값 50:50)

정보 환경은 각 시뮬레이션 스텝마다 다음을 생성한다.

- **친-런 신호** $n_{\text{pro}}$개: 은행 건전성에 대한 부정적 관련 정보
- **반-런 신호** $n_{\text{anti}}$개: 은행 건전성에 대한 긍정적 또는 중립적 정보

기본 설정은 $n_{\text{pro}} = n_{\text{anti}} = 5$ (대칭 혼합)이다. 비대칭 ablation은 §4의 대칭 정보 서약에서 상세히 다룬다.

신호 내용은 사전 작성된 템플릿 집합에서 무작위로 선택되며, 이 템플릿은 pre-registration 전에 SHA-256 해시가 기록된다. 특정 신호가 결과에 미치는 인과적 영향은 E06 프롬프트 강건성 실험에서 평가된다.

### 3.5 메트릭 레코더

다음의 지표가 매 스텝마다 기록된다.

| 지표 | 정의 | 단위 |
|------|------|------|
| $P(\text{run})$ | 100회 반복 시행 중 뱅크런 발생 비율 | 확률 [0,1] |
| $H_{\text{eff}}$ | 해당 스텝의 행동 분포 Shannon 엔트로피 | 비트 |
| $R_t$ | 인출 비율 시계열 집합자 | 비율 [0,1] |
| $\Delta t_{\text{lead}}$ | 런 발생 스텝 − 신호 수신 스텝 | 스텝 수 |
| $\cos\theta_{\text{align}}$ | 에이전트 결정 벡터의 방향 정렬도 | [-1, 1] |

$\cos\theta_{\text{align}}$는 에이전트 결정 벡터 $\mathbf{d} = (d_1, \ldots, d_N)^T \in \{0, 1\}^N$을 이진화하여 계산한다. 이 측도가 1에 가까울수록 에이전트 결정이 고도로 정렬(aligned)되어 있음을 의미한다.

---

## §4. 객관성 척추 — 5개 서약

합성 LLM 에이전트를 사용하는 실험은 특수한 형태의 편향 위협에 노출된다. 특히 (a) 프롬프트 설계자의 가설 방향에 유리한 언어 선택, (b) 특정 모형에 대한 과의존, (c) 사후적 파라미터 조정(HARKing)이 주요 위협이다. 본 연구는 이를 방지하기 위해 다음 5개의 객관성 서약을 채택한다.

**서약 1 — 프롬프트 중립성(Prompt Neutrality)**

모든 에이전트 프롬프트 템플릿에서 위험 강조 표현("심각한", "위기", "공황" 등)을 금지한다. 신호 내용은 "시나리오 A" / "시나리오 B"와 같은 중립 레이블로 제시된다. 프롬프트 중립성 준수 여부는 사전등록 전에 3인의 독립 검토자(본 연구 저자 외)가 확인한다. 이 서약의 직접적 검증은 E06 프롬프트 강건성 실험에서 수행된다.

**서약 2 — 대칭 정보(Symmetric Information)**

기본 실험 조건에서 친-런 신호와 반-런 신호의 수는 동일하다($n_{\text{pro}} = n_{\text{anti}}$). 비대칭 조건은 독립된 ablation 실험으로 분리하며, 이 ablation의 목적은 정보 비대칭의 한계 효과를 측정하는 것이다. 주 분석에서는 $K_{\text{eff}}$의 효과가 정보 혼합 비율이 아닌 에이전트 다양성에서 기인함을 구분할 수 있어야 한다.

**서약 3 — 사전등록(Pre-registration)**

주 실험 실행 전에 AsPredicted.org에 다음 항목을 등록한다. (a) 귀무가설 $H_0$ 및 대립가설 $H_1$의 정확한 서술, (b) 1차 종속변수 및 측정 방법, (c) 표본 크기 및 power 계산, (d) 통계 검정 방법 및 유의수준, (e) 제외 기준(exclusion criteria). 등록 타임스탬프는 §8에 명시된 방식으로 코드 레포지토리에 커밋된다.

**서약 4 — 반증 가능한 귀무가설(Falsifiable Null)**

귀무가설 $H_0$: "$K_{\text{eff}}$의 주 효과는 $P(\text{run})$에 통계적으로 유의미하지 않다 ($\sigma_{\text{fund}}$ 공변량 통제 후)"이며, 이 $H_0$을 $\alpha = 0.05$ 수준에서 기각할 power가 $\geq 0.80$이 되도록 파라미터 공간과 반복 횟수를 설계한다 (§7 power analysis 참조). $H_0$ 기각 실패는 연구 실패가 아니라 이론 수정의 신호로 해석된다.

**서약 5 — 적대적 강건성 감사(Adversarial Robustness Audit)**

결과 보고 전에 다음 6개 점검을 수행한다.

1. **프롬프트 변형 점검**: 5개의 의미론적으로 동등한 프롬프트 변형을 사용하여 결과 분산 측정 (E06)
2. **모형 교체 점검**: 4개 기반 모형(GPT-4, Claude, Llama, Mistral)으로 동일 실험 반복 (E07)
3. **시드 분산 점검**: 20개 독립 랜덤 시드로 결과의 시드 의존성 평가
4. **결정 순서 점검**: 에이전트 결정 처리 순서를 무작위화하여 순서 효과 확인
5. **정보 순서 점검**: 신호 제시 순서를 무작위화하여 최신 효과(recency effect) 확인
6. **표본 이분 점검**: 에이전트 집합을 무작위로 반으로 나눠 동일 패턴 복제 여부 확인

---

## §5. 3차원 직교 실험 공간

주 실험의 파라미터 공간은 다음의 세 축으로 정의된다.

**X축 — 기초 충격 크기**: $\sigma_{\text{fund}} \in [0, 1]$, 연속 값 (실험에서 이산화: 8개 수준)

**Y축 — 유효 다양성**: $K_{\text{eff}} \in \{1, 2, 3, 5, 7, 10\}$ (6개 수준, $K$ 설정으로 근사)

**Z축 — 시간 압박**: $t_{\text{press}} \in \{1\text{h}, 6\text{h}, 24\text{h}\}$ (에이전트 의사결정 시간 제약)

이 3차원 공간에서의 핵심 주장은 다음과 같다.

**대립가설 $H_1$**: "$P(\text{run})$ 표면에서, $\sigma_{\text{fund}}$의 임계값 미만(sub-critical) 영역에서 $K_{\text{eff}}$ 감소만으로도 뱅크런이 발생한다."

형식적으로, $\sigma_{\text{fund}} < \theta_{\text{DD}}$인 영역에서 $K_{\text{eff}}$를 1로 감소시켰을 때 $P(\text{run})$이 통계적으로 유의미하게 증가함을 주장한다.

**귀무가설 $H_0$**: "$K_{\text{eff}}$의 주 효과는 $P(\text{run})$에 통계적으로 유의미하지 않다. $P(\text{run})$은 오직 $\sigma_{\text{fund}}$의 주 효과로 설명된다."

$H_1$이 지지될 경우의 예상 그림: $(\sigma_{\text{fund}}, K_{\text{eff}})$ 2D 단면에서 $P(\text{run})$ 등고선이 낮은 $K_{\text{eff}}$ 영역 방향으로 변형되어, $K_{\text{eff}} = 1$ 열에서 $\sigma_{\text{fund}} < \theta_{\text{DD}}$임에도 높은 런 확률이 관찰된다.

---

## §6. 8개 실험 셀 상세 설계

### E01 — 교정 기준선 (Calibration Baseline)

**목적**: LLM 에이전트 없이 Diamond-Dybvig 분석 모형을 수치적으로 풀어 $\theta_{\text{DD}}$와 $P(\text{run})$의 이론 곡선을 생성한다. 후속 실험의 비교 기준(ground truth) 역할을 한다.

**독립변수**: $\sigma_{\text{fund}} \in [0, 1]$ (50개 이산 수준), $K_{\text{eff}} \in \{1, 2, 3, 5, 7, 10\}$

**종속변수**: 이론적 $P(\text{run})$ (명제 1 우변 값), $\theta_{\text{DD}}$ 수치 (파라미터 설정별)

**시행 횟수**: LLM 호출 없음 (결정론적 계산)

**예상 LLM 비용**: \$0

**산출물**: Figure 1 (이론 $P(\text{run})$ 표면), Table 1 ($\theta_{\text{DD}}$ 파라미터 감도)

---

### E02 — $K$ 스윕 주 실험 (K Sweep Main)

**목적**: $\sigma_{\text{fund}}$를 고정하고 $K_{\text{eff}}$를 변화시켜 $K_{\text{eff}}$의 순수 효과를 측정한다. 명제 1의 $\alpha(K_{\text{eff}})$ 증폭 항에 대한 직접 검증이다.

**독립변수**: $K \in \{1, 2, 3, 4, 5, 6, 7, 8, 9, 10\}$ (10개 수준), $\sigma_{\text{fund}} = 0.4$ 고정 (임계값 미만 설정)

**종속변수**: $P(\text{run})$, $H_{\text{eff}}$, $\bar{D}_{\text{max}}$

**시행 횟수**: 100회/셀 × 10개 $K$ 수준 = 1,000회

**예상 LLM 비용**: $\sim$\$15–25 (에이전트 수 $N=30$, 모형 GPT-4o-mini 기준)

**산출물**: Figure 2 ($K_{\text{eff}}$ vs. $P(\text{run})$ 단조 관계 그래프)

---

### E03 — $(\sigma \times K)$ 2D 위상 다이어그램 ← 주요 도면

**목적**: 3차원 파라미터 공간의 핵심 단면. $(\sigma_{\text{fund}}, K_{\text{eff}})$ 2D 그리드에서 $P(\text{run})$ 표면을 생성하여 "sub-critical $\sigma$, low $K_{\text{eff}}$" 영역의 런 발생을 시각화한다.

**독립변수**: $\sigma_{\text{fund}} \in \{0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8\}$ (8개 수준), $K_{\text{eff}} \in \{1, 2, 3, 5, 7, 10\}$ (6개 수준) → 48개 셀

**종속변수**: $P(\text{run})$ per cell, $\bar{D}_{\text{max}}$, $\Delta t_{\text{lead}}$

**시행 횟수**: 50회/셀 × 48개 셀 = 2,400회

**예상 LLM 비용**: $\sim$\$60–90 (GPT-4o-mini, $N=20$ 에이전트/시행)

**산출물**: Figure 3 (주요 도면 — 2D 위상 다이어그램 히트맵), Figure 4 (이론 vs. 실험 표면 잔차)

---

### E04 — $(\rho_{\text{intra}} \times \rho_{\text{inter}})$ 상관 구조 실험

**목적**: 클러스터 내/간 상관이 런 확률에 미치는 영향을 분리한다. Acemoglu 전파 이론에서 연결 강도 파라미터에 해당한다.

**독립변수**: $\rho_{\text{intra}} \in \{0.2, 0.4, 0.7, 0.9\}$, $\rho_{\text{inter}} \in \{0.0, 0.1, 0.2, 0.4\}$ → 16개 셀, $K = 5$ 고정, $\sigma_{\text{fund}} = 0.4$ 고정

**종속변수**: $P(\text{run})$, $\cos\theta_{\text{align}}$

**시행 횟수**: 50회/셀 × 16개 셀 = 800회

**예상 LLM 비용**: $\sim$\$20–30

**산출물**: Figure 5 ($\rho_{\text{intra}} \times \rho_{\text{inter}}$ 히트맵), Table 2 (상관 구조 회귀 계수)

---

### E05 — 시간 압박 실험 (Time Pressure)

**목적**: 의사결정 시간 제약 $t_{\text{press}}$이 런 확률 및 정보 처리 품질에 미치는 영향을 측정한다. 실시간 AI 에이전트 환경의 τ → 0 한계를 부분적으로 시뮬레이션한다.

**독립변수**: $t_{\text{press}} \in \{1\text{h}, 6\text{h}, 24\text{h}\}$, $K_{\text{eff}} \in \{1, 5, 10\}$, $\sigma_{\text{fund}} = 0.4$ 고정 → 9개 셀

**종속변수**: $P(\text{run})$, $H_{\text{eff}}$, 결정 일관성(decision consistency between $t_{\text{press}}$ 조건)

**시행 횟수**: 50회/셀 × 9개 셀 = 450회

**예상 LLM 비용**: $\sim$\$10–15 (max_tokens 제한으로 시간 압박 구현)

**산출물**: Figure 6 (시간 압박 × $K_{\text{eff}}$ 상호작용), Table 3 (시간 압박 한계 효과)

---

### E06 — 프롬프트 강건성 실험 (Prompt Robustness)

**목적**: 5개의 의미론적으로 동등한 프롬프트 변형에 걸쳐 결과의 일관성을 검증한다. 서약 5(적대적 강건성 감사)의 직접 이행이다.

**독립변수**: 프롬프트 변형 $v \in \{1, 2, 3, 4, 5\}$ (중립 → 미세하게 다른 서술 순서), $K_{\text{eff}} \in \{1, 5, 10\}$, $\sigma_{\text{fund}} = 0.4$ 고정 → 15개 셀

**종속변수**: $P(\text{run})$의 변형 간 분산, 변형 쌍별 순위 상관계수

**시행 횟수**: 50회/셀 × 15개 셀 = 750회

**예상 LLM 비용**: $\sim$\$15–20

**산출물**: Figure 7 (프롬프트 변형 분산 박스플롯), Table 4 (변형 간 순위 상관 행렬)

---

### E07 — 기반 모형 교체 실험 (Foundation Model Swap)

**목적**: 4개 기반 모형에 걸쳐 $K_{\text{eff}}$ 효과가 일관되게 나타나는지 검증한다. 특정 모형의 특성에 결과가 과의존하는 것을 방지한다.

**독립변수**: 기반 모형 $m \in \{\text{GPT-4}, \text{Claude Sonnet}, \text{Llama-3}, \text{Mistral}\}$, $K_{\text{eff}} \in \{1, 5, 10\}$, $\sigma_{\text{fund}} = 0.4$ 고정 → 12개 셀

**종속변수**: $P(\text{run})$ (모형별), 모형 간 $P(\text{run})$ 분산

**시행 횟수**: 50회/셀 × 12개 셀 = 600회

**예상 LLM 비용**: $\sim$\$40–60 (모형별 상이한 단가 반영)

**산출물**: Figure 8 (4-모형 $P(\text{run})$ 비교 바 차트), Table 5 (모형 × $K_{\text{eff}}$ 이원 분산 분석)

---

### E08 — 역 메커니즘 실험 (Counter-mechanism)

**목적**: 적대적 서사 삽입(adversarial narrative injection) 및 $K_{\text{eff}}$ 개입이 런 억제 효과를 갖는지 검증한다. S06 안정화 메커니즘과 연결된다.

**독립변수**: 개입 유형 $c \in \{\text{없음}, \text{서사 삽입}, K_{\text{eff}} \text{ 증가}, \text{복합}\}$, $\sigma_{\text{fund}} \in \{0.4, 0.7\}$ → 8개 셀

**종속변수**: $P(\text{run})$ 감소율 (무개입 대비), $\Delta t_{\text{lead}}$ 변화

**시행 횟수**: 100회/셀 × 8개 셀 = 800회

**예상 LLM 비용**: $\sim$\$20–30

**산출물**: Figure 9 (개입 효과 크기 비교), Table 6 (개입별 $P(\text{run})$ 감소 추정치 및 신뢰 구간)

---

## §7. 통계 분석 계획

### 7.1 혼합 효과 분산 분석 (Mixed-effects ANOVA)

주 분석 모형은 다음과 같다.

$$P(\text{run})_{ijl} = \mu + \beta_K \cdot K_{\text{eff},i} + \beta_\sigma \cdot \sigma_{\text{fund},j} + \beta_{K\sigma} \cdot K_{\text{eff},i} \cdot \sigma_{\text{fund},j} + u_l + \varepsilon_{ijl}$$

여기서 $i$는 $K_{\text{eff}}$ 수준, $j$는 $\sigma_{\text{fund}}$ 수준, $l$은 실험 셀(무작위 효과), $u_l \sim \mathcal{N}(0, \tau^2)$는 셀 수준 무작위 절편이다.

1차 관심 파라미터는 $\beta_K$이다. $H_0: \beta_K = 0$를 기각함이 $K_{\text{eff}}$ 주 효과 확인의 충분 조건이다. 이차 관심 파라미터는 교호작용 $\beta_{K\sigma}$이며, 이는 $K_{\text{eff}}$ 효과가 $\sigma_{\text{fund}}$ 수준에 따라 차별화되는지(즉, sub-critical 영역에서만 강하게 나타나는지)를 검증한다.

### 7.2 효과 크기

Cohen's $f$를 사전 결정 탐지 가능 효과 크기로 설정한다: $f = 0.25$ (중간 수준). 이 기준은 "실질적으로 의미 있는 $K_{\text{eff}}$ 효과가 존재한다면 탐지해야 한다"는 최소 기준을 반영한다.

회귀 분석에서는 $R^2$ 증분($\Delta R^2$)을 통해 $K_{\text{eff}}$ 항이 $\sigma_{\text{fund}}$만의 모형에 비해 설명 분산을 얼마나 추가하는지 보고한다.

### 7.3 다중 비교 보정

8개 실험 셀에서 파생되는 다수의 통계 검정에 대해 Holm-Bonferroni 순차 기각(sequential rejection) 절차를 적용한다. 가족별 1종 오류율(family-wise error rate, FWER) = 0.05. Holm-Bonferroni는 Bonferroni보다 power가 높으면서도 FWER 통제를 보장하므로, 실험 수가 적은(8개) 본 연구에 적합하다.

E03(주 실험)의 48개 셀에서 파생되는 쌍별 비교는 별도의 Holm-Bonferroni 패밀리로 관리한다.

### 7.4 Power 분석

$f = 0.25$에서 $1 - \beta = 0.80$을 달성하기 위한 샘플 크기를 G*Power 공식으로 사전 계산한다.

혼합 효과 ANOVA (3 요인: $K_{\text{eff}}$, $\sigma_{\text{fund}}$, $K_{\text{eff}} \times \sigma_{\text{fund}}$)에서 필요한 셀 당 시행 횟수는 $n_{\text{cell}} \approx 50$으로 추정된다. E03의 경우 48셀 × 50회 = 2,400회 시행이 이 기준을 충족한다. 이 사전 power 계산은 사전등록 시 포함된다.

### 7.5 1차 종속변수 및 회귀 계수

사전등록된 1차 분석 결과 지표: **$K_{\text{eff}}$ 회귀 계수 $\hat{\beta}_K$ 및 95% 신뢰 구간**. 논문 §5의 메인 테이블은 이 계수 추정치, 표준 오차, $p$-값, 효과 크기 $f$로 구성된다.

---

## §8. 재현성 및 감사 인프라

### 8.1 시드 레지스트리

파일 `seeds/registry.json`에 모든 시뮬레이션의 (실험 ID, 에이전트 ID, 시드) 삼중항을 기록한다. 형식 예시:

```json
{
  "E03": {
    "cell_0_0": {"sigma": 0.1, "K_eff": 1, "seed_list": [42, 137, 901, ...]},
    "cell_0_1": {"sigma": 0.1, "K_eff": 2, "seed_list": [1024, 2048, ...]}
  }
}
```

이 레지스트리를 기반으로 임의의 셀을 재실행하면 동일 결과가 생성됨을 보장한다.

### 8.2 LLM 응답 캐시

각 LLM API 호출의 입력(프롬프트 해시 + 파라미터)과 출력(응답 텍스트)을 SHA-256 키 기반으로 캐시에 저장한다. 캐시 파일은 `cache/llm_responses.jsonl`에 저장되며, 재실행 시 API 호출 없이 동일 응답을 재생할 수 있다. 이 메커니즘은 LLM API 비용 절감과 동시에 재현성 감사의 핵심 인프라가 된다.

### 8.3 프롬프트 템플릿 해시

모든 프롬프트 템플릿 파일은 사전등록 전에 SHA-256 해시가 계산되고, 이 해시값이 사전등록 문서에 기록된다. 사전등록 이후 프롬프트 수정이 발생할 경우 해시 불일치로 감지되며, 이 경우 해당 수정의 이유와 결과 영향을 별도 부록에 보고한다.

### 8.4 Docker 컨테이너 동결

실험 환경은 `Dockerfile`로 고정되며, 기반 이미지 `python:3.12-slim`에서 다음을 정확한 버전으로 설치한다.

```
numpy==1.26.4
scipy==1.13.0
pandas==2.2.1
matplotlib==3.8.4
openai==1.25.0
anthropic==0.25.0
```

이미지 SHA-256 다이제스트가 레포지토리에 기록된다. 논문 심사자 또는 독립 연구자는 동일 이미지에서 실험을 완전히 재현할 수 있다.

### 8.5 사전등록 타임스탬프

AsPredicted.org 사전등록의 URL 및 타임스탬프는 레포지토리의 `preregistration/record.md`에 기록되며, 이 파일은 첫 LLM 기반 실험 실행 전에 커밋된다. 커밋 해시와 AsPredicted 타임스탬프의 선후 관계가 사전등록의 증거가 된다.

---

## §9. 한계 및 위협 검증

### 9.1 합성 에이전트와 실제 예금자의 간극

본 연구의 가장 중요한 한계는 LLM 에이전트가 실제 금융 시장의 인간 예금자 또는 금융 기관 AI 시스템을 대리하지 않는다는 점이다. 실제 뱅크런 의사결정은 유동성 제약, 법적 의무, 규제 환경, 사회적 관계망 등의 요소에 의해 결정되며, 이 요소들은 텍스트 기반 LLM 에이전트의 행동 모형에 포함되지 않는다.

**완화 전략**: E01 교정 기준선을 통해 이론 예측치와 에이전트 행동의 정합성을 사전 확인한다. 실험 결과는 "실제 뱅크런 예측"이 아닌 "AI-era 이론의 행동 예측 검증"으로 한정하여 해석한다.

### 9.2 프롬프트 민감성

LLM 에이전트의 결정은 프롬프트 표현에 민감하게 반응할 수 있다. 특히 금융 위기와 관련된 어휘는 사전 학습 데이터에서 특정 패턴과 연결되어 있어 연구자가 의도하지 않은 방향으로 에이전트 행동을 유도할 수 있다.

**완화 전략**: E06 프롬프트 강건성 실험 및 서약 1(프롬프트 중립성)이 이 위협을 체계적으로 평가하고 문서화한다.

### 9.3 기반 모형 진화

본 연구에서 사용하는 특정 기반 모형 버전(GPT-4o, Claude Sonnet 등)은 연구 기간 중 업데이트될 수 있으며, 업데이트 전후의 행동 차이가 결과에 영향을 미칠 수 있다.

**완화 전략**: 특정 모형 버전(API 버전 핀 고정)을 Docker 컨테이너와 함께 동결하고, 모형 버전을 논문 §4에 명시한다. 향후 재현 연구자는 동일 버전 엔드포인트 또는 오픈소스 대안을 사용해야 함을 안내한다.

### 9.4 단일 은행 가정

현재 설계는 단일 은행을 중심으로 한 뱅크런 분석이다. 실제 금융 시스템에서는 은행 간 전염(inter-bank contagion)이 핵심 메커니즘인데, 이는 본 연구의 범위에 포함되지 않는다.

**완화 전략**: 이 확장은 Acemoglu et al.(2015)의 네트워크 모형과 직접 연결되는 향후 연구(future work)로 명시적으로 지정한다. 현재 단일 은행 설정은 $K_{\text{eff}}$의 순수 효과를 격리하는 데 유리하며, 이 방법론적 선택을 §3.2에서 명시한다.

### 9.5 AI 에이전트 식별 문제

실제 금융 시장에서 AI 에이전트가 의사결정에 어느 정도 관여하는지, 그리고 AI 에이전트들이 실제로 소수의 기반 모형에 집중되어 있는지는 현재 관찰 가능한 데이터로 직접 확인하기 어렵다. 즉, 현실 세계의 $K_{\text{eff}}$ 추정이 근본적으로 어렵다는 식별 문제(identification problem)가 있다.

**완화 전략**: 본 연구의 주장은 $K_{\text{eff}}$의 관찰된 값에 대한 주장이 아니라, $K_{\text{eff}}$가 낮아지면 어떤 결과가 발생하는가에 대한 조건부 명제이다. 식별 문제는 논문 §6(한계 및 향후 연구)에서 솔직하게 서술하며, 행동 프록시(behavioral proxy) 구성 가능성을 탐색하는 방향을 제시한다.

---

## §10. 참고문헌

Diamond, D. W., & Dybvig, P. H. (1983). Bank Runs, Deposit Insurance, and Liquidity. *Journal of Political Economy*, 91(3), 401–419.

Gorton, G., & Pennacchi, G. (1990). Financial Intermediaries and Liquidity Creation. *Journal of Finance*, 45(1), 49–71.

Goldstein, I., & Pauzner, A. (2005). Demand-Deposit Contracts and the Probability of Bank Runs. *Journal of Finance*, 60(3), 1293–1327.

Acemoglu, D., Ozdaglar, A., & Tahbaz-Salehi, A. (2015). Systemic Risk and Stability in Financial Networks. *American Economic Review*, 105(2), 564–608.

Shannon, C. E. (1948). A Mathematical Theory of Communication. *Bell System Technical Journal*, 27(3), 379–423.

Allen, F., & Gale, D. (2007). *Understanding Financial Crises*. Oxford University Press.

Hill, M. O. (1973). Diversity and Evenness: A Unifying Notation and Its Consequences. *Ecology*, 54(2), 427–432.

Morris, S., & Shin, H. S. (2003). Global Games: Theory and Applications. In M. Dewatripont, L. P. Hansen, & S. J. Turnovsky (Eds.), *Advances in Economics and Econometrics*. Cambridge University Press.

\cite{TBD-llm-agent-2024a} [LLM 에이전트 기반 사회 시뮬레이션 — 저자 미확정, 2024년경]

\cite{TBD-llm-agent-2024b} [다중 LLM 에이전트의 군집 행동 연구 — 저자 미확정, 2024년경]

\cite{TBD-ai-monoculture-2024} [AI 모노컬처 및 시스템 취약성 — 저자 미확정, 2024년경]

---

*본 문서는 AAAI 2027 투고 논문의 방법론 anchor 문서입니다. 버전 관리는 GitHub 커밋 히스토리로 관리하며, 사전등록 이후의 수정은 `CHANGELOG.md`에 이유와 함께 기록됩니다.*
