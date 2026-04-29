# AAAI 2027 Paper Skeleton
## Signal Governance: AI-Era Bank Run Detection

**제목 (Title):** Signal Governance: An AI-Era Integration of Diamond-Dybvig, Gorton-Pennacchi, Acemoglu, and Shannon Frameworks for Synchronized Bank Run Detection

**저자 (Author):** Kiwon Cho, KAIST PMBA / ZEISS Korea

---

## 컴파일 방법 (Compile)

```bash
make build
```

요건: `pdflatex` + `bibtex` 설치 필요 (TeX Live 2023+ 또는 MiKTeX 권장).

공식 `aaai24.sty` (또는 2027 후속 버전) 취득 시, `main.tex` 상단 주석 처리된 두 줄을 활성화하고 `\documentclass[letterpaper]{article}` 블록을 주석 처리할 것. 현재 `\documentclass{article}` fallback은 추가 패키지 없이 깨끗하게 컴파일됨.

---

## 목표 분량 (Word Target)

~10,000 단어 (20페이지 기준, 이론 40% / 실험 60% 구성).

---

## 섹션 상태 체크리스트 (Section Status)

| 파일 | 섹션 | 상태 |
|------|------|------|
| `sections/01_intro.tex` | Introduction | [ ] DRAFT |
| `sections/02_related.tex` | Related Work | [ ] DRAFT |
| `sections/03_theory.tex` | Theoretical Framework | [ ] DRAFT |
| `sections/04_design.tex` | Experimental Design | [ ] DRAFT |
| `sections/05_results.tex` | Main Results | [ ] DRAFT |
| `sections/06_robustness.tex` | Robustness | [ ] DRAFT |
| `sections/07_theoretical_validation.tex` | Theoretical Validation | [ ] DRAFT |
| `sections/08_counter.tex` | Counter-Mechanisms | [ ] DRAFT |
| `sections/09_implications.tex` | Implications | [ ] DRAFT |
| `sections/10_limitations.tex` | Limitations | [ ] DRAFT |
| `sections/11_conclusion.tex` | Conclusion | [ ] DRAFT |

---

## 제출 일정 (Deadlines)

| 마일스톤 | 날짜 |
|----------|------|
| AAAI 2027 논문 제출 마감 | 2026-08-15 (예정) |
| AAAI 2027 보충 자료 마감 | 2026-09월 중 (예정) |
| 내부 초안 완성 목표 | 2026-07-31 |

---

## AAAI 스타일 파일 안내 (Style File Notes)

- 공식 `aaai24.sty`는 [AAAI 공식 사이트](https://aaai.org/authorkit) 또는 Overleaf AAAI 템플릿에서 취득.
- AAAI 2027 키트 출시 시 해당 연도 버전으로 교체할 것.
- 현재 `\documentclass{article}` + `times` + `geometry` 조합은 임시 fallback으로, 별도 패키지 없이 컴파일 가능.

---

## 빠른 정리 (Quick Clean)

```bash
make clean
```

---

## 단어 수 확인 (Word Count)

```bash
make wordcount
```

(`detex` 설치 필요: `brew install detex` 또는 `apt install texlive-extra-utils`)
