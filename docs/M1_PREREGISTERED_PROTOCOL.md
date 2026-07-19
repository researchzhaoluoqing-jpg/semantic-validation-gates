# Pre-Registered Protocol: M1 Field Study

## Sheaf Energy versus Contradiction Counting under a Real NLI Instrument

**Protocol version:** 1.0 (frozen 2026-07-19, prior to any field data collection)
**Companion manuscript:** *Semantic Validation Gates: A Computable, Statistically Calibrated Framework for Runtime Verification of Language-Model Outputs* (v3.1), §6 (mechanism study) and §7 (pre-registered protocol), ablation (b).
**Registry of record:** this document, version-controlled at `github.com/researchzhaoluoqing-jpg/semantic-validation-gates`; any deviation is logged in §9 before unblinding.

---

### 1. Background and rationale

The manuscript's §6 mechanism study establishes a *conditional* claim: **if** pairwise NLI confidence on contradiction edges decays with reasoning distance (assumption S1) and hedged constructions produce false-positive contradiction edges (assumption S2), **then** the weighted sheaf energy `f3` (§3.3) separates structurally from threshold-based contradiction counting — graceful degradation versus threshold collapse, and top-1 localization the baseline lacks by construction. Table 1 of the manuscript demonstrates this mechanism under *simulated* confidences drawn from (S1)/(S2).

The present study replaces every simulated quantity with a measured one, per the manuscript's own commitment: "the harness used here becomes the real experiment by replacing simulated confidences with model outputs." It is the empirical linchpin identified in §7(3)(b): the framework's claim to a *new mathematical tool* (as opposed to a certified composition of existing ones) stands or falls with this comparison.

**Theoretical basis of each measured object.**

| Object | Manuscript basis |
|---|---|
| Sheaf energy `f3` (weighted cellular sheaf Laplacian; unified relaxed energy; holonomy statistic on numeric cycles) | §3.3; Hansen–Ghrist spectral sheaf theory; Prop. 3.1 (Lipschitz sensitivity in NLI confidences); Amendment F1 (holonomy replaces diluted least-squares residual) |
| Relax-and-certify / SAT arm | §3.3, Props. 3.2–3.3 (relaxation gap; no exact polynomial unification unless P = NP) |
| Contradiction counting baselines | §6 (the standard production baseline family) |
| Conformal coverage law of the calibrated gate | Thm. 4.2; coverage distribution Beta(m, n+1−m) (Vovk 2012; Angelopoulos–Bates 2023) |
| Instrument-inclusive validity | Prop. 4.1 (instrument frozen before calibration; scores composite) |
| Detection-power accounting | Prop. 4.6 (ε_D, ε_NLI, π₃ factorization) |

### 2. Instrument (frozen before any E1 case is scored)

- **NLI model:** `microsoft/deberta-large-mnli` (pinned checkpoint), label map read from the model config and asserted at load time.
- **Calibration:** temperature scaling (Guo et al., 2017) fitted on a fixed random subsample of MNLI validation-matched (n = 2,000; seed 20260719); the scalar T is frozen for the entire study. ECE (15-bin) reported pre- and post-calibration.
- **Leakage guard:** the instrument never receives the ground-truth injection location or distance; all confidences are functions of text pairs only.
- **Encoder/decomposition:** GSM8K's own step segmentation (newline-delimited solution steps) and its native `<<a op b = c>>` calculator annotations serve as the claim-decomposition and numeric-extraction channels; no learned extractor is introduced in this study (ε_D for this corpus is the parse-failure rate, reported).

### 3. Materials

GSM8K training split (public; test split reserved for later phases). Items whose gold solution parses into 4–8 steps of ≥ 10 characters form the chain corpus (target N = 450 chains). Each chain carries its step texts and the numeric results of its calculator annotations.

### 4. Design

Paired clean/violated design: every case yields a clean and a violated instance built from the same chain; all arms score both members. Cells (`vtype`, k) with n = 150 cases per cell:

- **V1 (k = 1):** template negation of the final step, appended after it. Direct-pair contradiction.
- **V2 (k ∈ {2, 3, 4, 5}):** template negation of the step k positions before the end, appended at the end — transitive distance k in the claim graph.
- **V3 (k = 0):** compositional numeric violation. A closing sentence asserts the ratio between the final and initial computed quantities; the violated twin misstates the ratio by a factor U(1.45, 1.9) (sign-symmetric), the clean twin states it with 2% rounding noise. Every *pair* of sentences remains individually consistent — pairwise detectors are blind by construction; the sheaf's holonomy on the numeric cycle (chain edges from real annotation values + the asserted closing edge) is the detection channel.
- **V4 (k = 1):** hedged contamination. Both classes carry a hypothetical clause ("Suppose, hypothetically, that … — but that cannot be the case") attached as a *non-asserted* node; the violated class additionally carries a V1 negation. Tests assertion-awareness under S2 noise.

Claim graphs are built by scoring **all** sentence pairs with the calibrated NLI (contradiction edges kept at confidence ≥ 0.05 — the soft-evidence floor; adjacent entailment edges at measured confidence). Per-chain pair scores are cached; the injected edge's index is recorded for the localization endpoint.

**Arms.** COUNT (contradiction edges with w ≥ 0.5), WSUM (sum of contradiction confidences — the de-thresholded control that prevents attributing a sheaf win to mere de-thresholding), NLIMAX (max contradiction confidence), SAT (DPLL on w ≥ 0.5 edges; exact numeric closure on the affine view), SHEAF (unified energy: pairwise relaxed energy ⊕ numeric holonomy, per manuscript §3.3 and Amendment F1).

### 5. Endpoints

- **PE1 (detection):** ΔAUROC = AUROC(SHEAF) − AUROC(best baseline in that cell), with paired bootstrap (4,000 resamples over base items) percentile CI and two-sided p; Holm step-down across the 7 cells.
- **PE2 (localization):** top-1 hotspot hit rate (SHEAF: largest weighted-residual element across pairwise and numeric views; baseline: injected edge above the w ≥ 0.5 threshold), compared at k ≥ 3 and on V3.
- **SE1:** FPR at 95% TPR per arm per cell. **SE2:** field S1 curves — calibrated contradiction confidence of (¬c_i, c_i) (direct) and (¬c_i, c_{i+k}) (cross) versus k, with the threshold-crossing point k*. **SE3:** field S2 — hedged false-positive rate with Clopper–Pearson 95% interval. **SE4:** conformal coverage field test of Theorem 4.2 on clean-chain SHEAF scores (n_cal = 200, α = 0.10, R = 1,000 random splits; KS test against Beta(m, n+1−m) plus one-sided exact binomial on pooled exceedances).

### 6. Pre-registered predictions

- **P-A (V3, structural):** COUNT/WSUM/NLIMAX AUROC ≤ 0.60 (pairwise-blind); SHEAF ≥ 0.85; SHEAF top-1 localization ≥ 0.60 with baseline localization = 0 by construction. *This is the load-bearing prediction: it does not depend on S1.*
- **P-B (V4, assertion-awareness):** AUROC(SHEAF) − AUROC(WSUM) ≥ 0.03.
- **P-C (V2 curve, conditional on S1):** if the field S1 *direct* curve stays above 0.5 at all k (template negations remain surface-detectable), COUNT does **not** collapse on V2 and the simulated Table-1 separation does not transfer to verbatim negations — the honest outcome is then that the sheaf's field advantage concentrates on V3/V4, and the manuscript's §6 narrative must be re-scoped accordingly. If the direct curve crosses 0.5 at some k* ≤ 5, the Table-1 collapse/graceful-degradation pattern is predicted to reproduce with the measured k*.

### 7. Decision rule (frozen; identical to the harness `e1_verdict`)

- **GREEN:** [any cell has ΔAUROC ≥ 0.03 with bootstrap CI lower bound > 0, **or** any k ≥ 3 cell has localization advantage ≥ 0.10] **and** SHEAF beats WSUM by ≥ 0.03 AUROC on V3 or V4 (anti-artifact clause). → The sheaf gate is the manuscript's flagship; proceed to full Phase-1 scale-up (n = 1,000/cell) and paper P2.
- **YELLOW:** detection or localization criterion met, but only against thresholded baselines (WSUM clause fails). → `f3` is repositioned as a *localization* capability; manuscript emphasis shifts to the calibration architecture.
- **RED:** neither criterion met. → Pivot: the manuscript is re-scoped as a certified verification architecture paper (guarantee layer + veto architecture, which are independent of this comparison); target SaTML/TMLR.

### 8. Statistical analysis plan

AUROC via Mann–Whitney U (ties half-credit). Paired bootstrap for ΔAUROC (resampling base items so each item's clean and violated scores move together across both methods; valid under arbitrary cross-method dependence, unlike DeLong). Holm step-down for family-wise control across cells (no independence assumption). Clopper–Pearson exact intervals for all proportions. Coverage field test per §5-SE4 with the exact Beta reference law. All seeds fixed (20260719); QUICK smoke runs (reduced n) validate the pipeline and are excluded from confirmatory analysis.

### 9. Deviations log

| Date | Deviation | Reason | Impact on confirmatory status |
|---|---|---|---|
| — | — | — | — |

### 10. Compute environment

Kaggle GPU kernel (NVIDIA T4, fp16 inference), internet enabled; code and harness version-controlled (kernel `luoqingzhao/svg-m1-field-study`, dataset `luoqingzhao/svg-harness`); all public models and data; no authentication tokens required.
