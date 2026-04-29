# AsPredicted.org Pre-Registration

**DRAFT v0.1 — to be submitted to AsPredicted.org before main run execution. Timestamp will be locked at submission.**

**Study title**: Signal Governance: An AI-Era Integration of Diamond-Dybvig, Gorton-Pennacchi, Acemoglu, and Shannon Frameworks for Synchronized Bank Run Detection

**Author**: Kiwon Cho  
**Affiliation**: KAIST PMBA; ZEISS Korea  
**Submission target**: AAAI 2027 (deadline 2026-08-15)  
**Pre-registration covers**: Experiments E02, E03, E04, E05, E06, E07, E08

---

## Question 1 — Have any data been collected for this study already?

No. No data have been collected for the main study. Pilot calibration runs of E01 (an analytical Diamond-Dybvig parameter sweep that does not involve any large-language-model calls) may exist in the repository at the time of this submission, but those runs are pre-experimental. They were used solely for parameter sanity checks and are not used for hypothesis testing, model fitting, or any analysis reported in the paper. All experiments covered by this pre-registration (E02–E08) have not been initiated.

---

## Question 2 — What's the main question being asked?

In synthetic populations of large-language-model-backed depositor agents, does decreasing effective foundation-model diversity K_eff causally increase bank-run probability P(run), holding fundamental shock magnitude σ_fund constant?

**Null hypothesis (H0)**: The regression coefficient β(1/K_eff) is not statistically distinguishable from zero after controlling for σ_fund. That is, effective model diversity has no measurable effect on bank-run probability in the studied simulation environment.

**Alternative hypothesis (H1)**: P(run) is a strictly decreasing function of K_eff in the sub-critical σ_fund regime [0.3, 0.5]. Formally, the regression coefficient β(1/K_eff) > 0 with p < 0.05 (Holm-Bonferroni corrected). The direction of the effect is pre-specified: higher 1/K_eff (lower diversity) is hypothesized to increase P(run).

The theoretical motivation is grounded in the Shannon entropy argument from the Signal Governance framework: when K_eff = 1, all agents share an identical internal model, so their withdrawal decisions are perfectly correlated; the effective entropy H_eff collapses, and the run equilibrium becomes the unique outcome even at sub-critical shock magnitudes where a heterogeneous population would coordinate on the no-run equilibrium (Diamond and Dybvig 1983; Acemoglu 2024 working paper).

---

## Question 3 — Describe the key dependent variable(s) specifying how they will be measured.

**Primary DV: P(run) per experimental cell**

Operationalized as the fraction of simulation trials in which the simulated withdrawal rate f exceeds the critical threshold f_critical within the terminal timestep of the simulation. The threshold is derived analytically from the Diamond-Dybvig model parameters:

f_critical = (R − r1) / (r1 · (R − 1))

where R is the long-run return on illiquid investment and r1 is the early-liquidation return. Parameter values are fixed at R = 1.5, r1 = 1.0 across all experiments unless otherwise noted.

For a given cell c = (σ_fund, K_eff), P(run)_c = (number of trials where f > f_critical) / (total valid trials in cell c). This is a proportion bounded in [0, 1] and computed entirely from simulation logs with no human judgment involved.

**Secondary DVs (all pre-registered, none used for H1 gating):**

1. Effective Shannon entropy H_eff: the Shannon entropy of the binary agent action distribution (withdraw vs. stay) aggregated across all agents at each timestep. Measured in bits. Reported as time-series mean and minimum per trial.

2. Lead-time: the number of simulation timesteps between the Signal Governance detector (SG-Detect) crossing Stage 1 threshold and the price-based reference detector triggering. Measured in integer timesteps per run-occurrence trial.

3. Cosine alignment: the cosine similarity of the N-dimensional binary withdrawal-decision vector across all agents at the terminal timestep, relative to the all-withdraw vector. Ranges from 0 (maximally heterogeneous) to 1 (all withdraw).

4. Time-to-run: the median timestep at which f first exceeds f_critical, conditional on the trial being classified as a run. Measured in integer timesteps.

All DVs are computed deterministically from simulation log files. No human coders, no rating scales, no subjective assessments.

---

## Question 4 — How many and which conditions will participants be assigned to?

This study uses simulation conditions, not human participants. The unit of analysis is a simulation trial (a single run of the multi-agent model with a fixed random seed).

**Main experiment E03: 8 × 6 full factorial design**

- σ_fund (fundamental shock magnitude): 8 levels — {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0}
- K_eff (effective number of distinct foundation models): 6 levels — {1, 2, 3, 5, 7, 10}
- 48 cells × 50 trials per cell = 2,400 simulation runs

**Auxiliary experiments (all pre-registered):**

- E02 — K_eff sweep at fixed σ_fund = 0.4: 10 K_eff levels × 100 trials = 1,000 runs
- E04 — Correlation structure: 4 ρ_intra levels × 4 ρ_inter levels at fixed K_eff = 5; 16 cells × 50 trials = 800 runs
- E05 — Time pressure: 3 t_press levels × 6 K_eff levels × 50 trials = 900 runs
- E06 — Prompt variants: 5 prompt variant conditions × main E03 specification replication = 500 runs
- E07 — Model swap: 4 model configurations × K_eff = 1 baseline × 100 trials = 400 runs
- E08 — Counter-mechanism: 2 mechanism conditions (active vs. inactive) × E03 grid subset (σ_fund ∈ {0.3, 0.4, 0.5} × K_eff ∈ {1, 3, 5}) = 300 runs

**Total across all experiments: approximately 6,000 simulation runs.**

The mapping from K_eff to agent assignments is deterministic: K_eff = k means the N agents are divided into k equal-sized groups, each group assigned a distinct foundation model from the pre-registered model list (Q8). For K_eff values that do not divide N evenly, the remainder agents are assigned to model index 1 (the primary model).

---

## Question 5 — Specify exactly which analyses you will conduct to examine the main question/hypothesis.

**Primary analysis (H1 test, pre-specified):**

Mixed-effects logistic regression on trial-level binary outcome y_ij ∈ {0 = no run, 1 = run}, where i indexes cell and j indexes trial within cell.

Fixed effects: 1/K_eff (continuous), σ_fund (continuous), 1/K_eff × σ_fund (interaction term).

Random effects: random intercept for cell (i), random intercept for trial seed nested within cell.

Model fitted via lme4 (R, version ≥ 4.4) or statsmodels MixedLM (Python, version ≥ 0.14). If both are run, lme4 is the pre-specified primary. Model selection between specifications (with vs. without interaction) is via AIC; the interaction term is retained regardless if AIC difference < 2.

Primary test statistic: one-sided z-test on β(1/K_eff). One-sided because H1 pre-specifies direction (higher 1/K_eff increases P(run)). Significance threshold: α = 0.05 after Holm-Bonferroni correction across the family of three main coefficients: β(1/K_eff), β(σ_fund), β(interaction). The corrected thresholds, ordered by p-value ascending, are α/3, α/2, α for the three tests.

**Secondary analyses (pre-registered, not gated on H1):**

1. Two-way ANOVA on cell-level P(run) with σ_fund and K_eff as fixed factors (treating each as categorical). Effect size reported as Cohen's f. Pre-registered threshold for a "meaningful" effect: f ≥ 0.25.

2. Phase-diagram visualization: heatmap of P(run) over the 8×6 σ_fund × K_eff grid with isoclines at P(run) ∈ {0.1, 0.3, 0.5, 0.7, 0.9}.

3. Lead-time secondary (E02 data): paired t-test comparing SG-Detect lead-time against price-based detector trigger time, calibrated against the SVB 2023 historical timeline (March 9–10, 2023).

4. Shannon entropy correlation: Pearson r between cell-level mean H_eff and cell-level P(run), reported as exploratory.

**Power analysis (pre-study):**

To detect Cohen's f = 0.25 at α = 0.05 with 80% power in a two-way 8×6 ANOVA, the minimum required n per cell is approximately 35 (computed via pwr::pwr.anova.test in R). The pre-registered n = 50 per cell exceeds this minimum. No post-hoc power adjustments will be made.

All analysis scripts will be committed to the repository before the first experiment run is initiated, and the commit hash will be reported in the paper.

---

## Question 6 — Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

All exclusion rules are pre-specified below. No data-driven outlier detection (Z-score trimming, IQR-based removal, Cook's distance culling) will be applied at any stage.

**Trial-level exclusions:**

1. LLM API failure: If an API call returns a timeout, rate-limit error (HTTP 429), or server error (HTTP 5xx), the call is retried once with a 10-second delay. If the retry also fails, the trial is dropped. A cell in which more than 5% of trials are dropped due to API failure is excluded from the primary analysis and reported separately in the paper appendix.

2. Malformed agent output: If the agent's response cannot be parsed as a "withdraw" or "stay" decision after 2 retries at temperature = 0, the trial is dropped. The same 5% cell-level exclusion rule applies.

3. Agent refusal: If the agent produces a refusal response (e.g., "I cannot make this financial decision"), the response is coded conservatively as "stay" (anti-run direction). The refusal rate is a pre-registered secondary outcome variable reported in the paper. Refusal decisions are not dropped; they contribute to the trial outcome.

**Cell-level exclusions:**

A cell with fewer than 0.95 × 50 = 47 valid (non-dropped) trials is excluded from the primary mixed-effects regression. Excluded cells are listed in a supplementary table and sensitivity analyses are reported using the reduced-cell dataset.

**Simulation-level bounds check (not exclusion):**

Trials where f = 0 (no agent withdrew) or f = 1 (all agents withdrew) are valid outcomes and are not excluded. These boundary values are meaningful and informative.

**No other exclusion rules will be applied.** Any deviation from these rules after data collection begins requires a versioned amendment to this pre-registration with a new timestamp.

---

## Question 7 — How many observations will be collected or what will determine sample size?

**Pre-determined and locked. Will not be modified after data collection begins.**

Primary experiment E03: 50 trials × 48 cells = 2,400 simulation runs.

Auxiliary experiments:
- E02: 100 trials × 10 K_eff levels = 1,000 simulation runs
- E04: 50 trials × 16 cells = 800 simulation runs
- E05: 50 trials × 18 cells = 900 simulation runs
- E06: 100 trials × 5 prompt variant conditions = 500 simulation runs
- E07: 100 trials × 4 model configurations = 400 simulation runs
- E08: 50 trials × 18 condition × grid cells = 900 simulation runs

Total planned: approximately 6,000 simulation runs.

The per-cell n = 50 for E03 is determined by the power analysis described in Q5 (minimum n = 35, pre-registered at 50 to provide margin). The per-cell n = 100 for E02 reflects its role as a high-resolution K_eff sweep at a single σ_fund value, warranting increased precision.

**Budget cap**: The total LLM inference cost will not exceed USD 3,000 (billed across OpenRouter and local vLLM). If this cap is reached mid-experiment, data collection will stop at the last completed cell boundary. The paper will report which cells were collected and which were not. The analysis will proceed on collected cells only, with the incomplete coverage explicitly disclosed. The sample size will not be augmented beyond the pre-registered figures even if H1 is not supported.

---

## Question 8 — Anything else you would like to pre-register?

**Foundation model version lock**

All foundation models are locked to specific version identifiers at the time of this pre-registration submission. Any model version change (including vendor-side silent updates) constitutes a protocol deviation and requires a new pre-registration.

Pre-registered model versions:
- GPT-4 Turbo: `gpt-4-turbo-2024-04-09` (OpenAI API)
- Claude 3.5 Sonnet: `claude-3-5-sonnet-20241022` (Anthropic API)
- Llama 3.1 70B Instruct: `meta-llama/Llama-3.1-70B-Instruct` (HuggingFace, served via local vLLM ≥ 0.6)
- Mistral Large 2: `mistral-large-2407` (OpenRouter)

**Prompt template lock**

A single neutral depositor prompt template (`lab/prompts/neutral_v1.txt`) is used in E02–E05 and E07. The SHA-256 hash of this file will be committed to the repository at the time of pre-registration submission and reported in paper §4. Any change to prompt wording, system message, or few-shot examples requires a new pre-registration. E06 uses five pre-registered prompt variant conditions; their hashes will likewise be committed before E06 begins.

**Seed registry**

All (exp_id, cell_id, trial_index, model_id, prompt_hash, numpy_seed, langchain_seed) tuples are logged deterministically to `lab/seeds/registry.json` before the first API call of each experiment. The registry is committed to the public GitHub repository at pre-registration submission. This enables full replay of any individual trial without additional API spend by loading from the response cache.

**LLM response cache**

All API responses are cached by a key of (model_version, prompt_text, temperature, seed) → SHA-256-named file stored in `lab/cache/llm_responses/`. Cache enables complete replay reproducibility. Cache miss rate on identical (model, prompt, temperature, seed) inputs at temperature = 0 is a pre-registered diagnostic variable; if the miss rate exceeds 10%, the foundation-model determinism assumption is considered violated and the primary analysis pivots to a deterministic-agent baseline as described below.

**Pre-registered failure modes and responses**

1. Null result: If E03 primary analysis yields p ≥ 0.05 (corrected) on β(1/K_eff), the paper will report the null result and reframe the contribution as: "At the studied agent population sizes and simulation horizons, LLM diversity is empirically sufficient to prevent coordinated runs at sub-critical shock magnitudes." This framing is the bidirectional-value commitment stated at project outset.

2. Non-determinism violation: If cache miss rate on identical temperature-0 inputs exceeds 10%, the primary analysis will use only locally-served Llama 3.1 70B (which is under full version control) and the OpenAI/Anthropic results will be reported as supplementary with a caveat.

3. Budget exhaustion mid-grid: As specified in Q7, collection stops at the last complete cell. Analysis proceeds on collected cells; all tables will clearly indicate which cells are missing.

**Exploratory secondary analyses (not primary, not power-justified; flagged as exploratory in paper)**

These analyses are pre-registered to distinguish them from post-hoc exploration, but they carry no confirmatory weight:

- E07 cross-model herding asymmetry: whether Claude-Llama mixed populations herd more or less than Claude-GPT mixed populations.
- E05 time-pressure × K_eff interaction: whether decision deadline modulates the K_eff effect on P(run).
- E08 counter-mechanism efficacy ranking: which intervention condition (smart-contract commitment vs. real-time attestation) reduces P(run) most, and effect magnitude.
- Cosine alignment trajectory: whether alignment increases monotonically in the timesteps preceding a run, as a process-tracing diagnostic.

**Relationship to non-LLM experiments**

E01 (analytical Diamond-Dybvig replication, no LLM) is not covered by this pre-registration. It is a calibration and replication exercise with no novel hypothesis test.

---

## Question 9 — Have any data been collected for this study already?

No. No data have been collected for the main study. Pilot calibration runs of E01 (analytical Diamond-Dybvig parameter sweep, no LLM) may exist but are pre-experimental and are not used for hypothesis testing. All experiments covered by this pre-registration (E02–E08) have not been initiated. This answer is identical to Question 1 per the AsPredicted template.

---

*End of pre-registration draft.*
