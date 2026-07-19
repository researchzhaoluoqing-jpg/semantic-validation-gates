# Research State and Direction — Semantic Validation Gates

**Status:** provisional (v0.1, 2026-07-19). Consolidates the experimental
campaign to date, the problems it surfaced, the resulting re-scoped thesis, and
the theory/experiment agenda. Companion documents:
`M1_PREREGISTERED_PROTOCOL.md` (frozen protocol + deviations),
`M1_RESULTS_AND_ANALYSIS.md` (confirmatory results), `EXPERIMENT_LOG.md`
(chronological run log). This document is the single entry point.

---

## 1. Where the project stands

The manuscript (v3.1 "all-in") proposes a five-gate runtime verification
framework whose guarantees (conformal false-rejection control across three
drift regimes, safety veto, complete error taxonomy) are theorems, and whose
one *candidate for genuinely new capability* — the sheaf-Laplacian logic gate
`f3` — rested on a simulated mechanism study. The strategy document identified
a single decisive question ("does the sheaf energy empirically beat
contradiction counting?") with pre-registered GREEN/YELLOW/RED outcomes.

**That question is now answered in the field: GREEN** (confirmatory run
2026-07-19, frozen rules): the sheaf energy attains **AUROC 0.990 /
FPR@95TPR 1%** on compositional violations where every pairwise baseline sits
at chance by construction, and it is the only method with nonzero localization
there. The win survives the WSUM anti-artifact clause. The project's "single
point of risk" has resolved in favor of the high-upside branch: the framework
now owns both a certified architecture (P1 material) and a demonstrated new
detection capability (P2 material).

## 2. The experimental campaign and what each problem taught

### Study A — v1-instantiation control (complete)

The v1 preprint's geometric operators (W2-to-reference, EVT/Fréchet
thresholds, lexicographic Π) were instantiated faithfully and run at N=300
(GSM8K + TruthfulQA, Qwen2.5-1.5B generator). Outcome: **empirically inert** —
10.6% detection of incorrect outputs, f3-AUROC 0.39 (below chance), 44%
classification flips under the smallest perturbations, EVT bounds satisfied
only vacuously (FR = 0, no power). *Lesson:* the v1→v3 rewrite is not just a
theoretical repair; the v1 construction fails in the field, and Appendix A can
now cite data, not only defects.

### Study B — M1 field study (confirmatory run complete)

Replaced the §6 simulation's mock NLI with a temperature-calibrated
DeBERTa-large-MNLI (T = 1.452, ECE 0.011) on 450 real GSM8K chains; four
violation families; five detector arms; frozen decision rules.

Problems surfaced, in order, and their dispositions:

| # | Problem | Type | Disposition |
|---|---|---|---|
| 1 | Kaggle infra: missing kernelspec; P100/torch incompatibility; silent invalid accelerator enums; dataset mount path | infrastructure | fixed in the loop driver; documented in EXPERIMENT_LOG |
| 2 | DeBERTa-v1 fp16 incompatibility | infrastructure | fp32 (deviation D1) |
| 3 | **Simulated assumption S1 fails**: NLI confidence on verbatim negations is flat in distance (0.74–0.76), not decaying | scientific | Table-1 "threshold collapse" narrative does not transfer to verbatim negations; P-C resolved on its null branch |
| 4 | **Simulated assumption S2 fails**: hedged false-positive rate 0/300 under a calibrated instrument | scientific | V4's reconciliation mechanism vacuous in this setting; retire (S2) as a field premise |
| 5 | **Sheaf ≡ WSUM on V1/V2** (identical AUROC to 3 decimals, every cell) | scientific → theory | not an accident: provable structural equivalence (Prop. NEW-1 below); converts a null into the theory of where the tool works |
| 6 | **Quadrature dilution inside f3**: as-specified channel combination scores 0.586 on V3 vs 0.990 for max-aggregation | scientific → design | the manuscript's own dilution principle (P3 / Prop. 3.4) applied one level down; registered pre-confirmatory as deviation D2 |
| 7 | Real NLI flags spurious contradictions between ordinary math steps | scientific | caps all pairwise arms at ≈ 0.72–0.76 on V1/V2; drives SAT to chance; sheaf hotspot localization loses to the above-threshold rule outside V3 |
| 8 | E2 coverage-distribution law rejected (39.7% score ties) while the exceedance bound holds (0.0952 ≤ 0.10) | scientific | Theorem 4.2's bound is field-verified; the Beta refinement needs a continuity caveat (D4) |

## 3. The new direction (re-scoped thesis)

**Old implicit claim (simulation-backed):** sheaf energy degrades gracefully
where counting collapses with distance, on transitive contradictions.

**New claim (field-backed, sharper, and partly provable):**

> On claim graphs without structure — all-asserted, acyclic — the relaxed
> sheaf energy provably *coincides* with weighted contradiction counting
> (Prop. NEW-1). Its added capability is therefore exactly the structured
> regime: **compositional violations that no sentence pair witnesses**, where
> it attains near-perfect detection (0.990) and is the only localizing method,
> and **hedged/free-vertex reconciliation**, whose field relevance is
> instrument-dependent. The correct aggregation across f3's channels is the
> calibrated max-form, forced by the dilution theorem.

This is a stronger position than the original: the boundary of the tool's
value is now a theorem plus a measurement, not a hope.

## 4. Theory agenda (current formal targets)

**Prop. NEW-1 (structural equivalence; to add to §3.3).** Let G be a claim
graph in which every vertex is asserted (clamped to 1) and whose edges are
entailments and contradictions with weights w_e. Then the relaxed unified
energy satisfies f3(y)² = Σ_{e ∈ C(G)} w_e, where C(G) is the contradiction
edge set; in particular f3 is a strictly monotone function of WSUM and induces
identical rankings (AUROC, FPR at any operating point). *Proof:* with all
vertices clamped there is no free variable; entailment residuals max(0, x_u −
x_v) vanish and each contradiction residual is x_u + x_v − 1 = 1; the minimum
is attained trivially. ∎ — Corollary: any detection separation requires free
vertices, cycles in the (affine/numeric) view, or the certificate layer.

**Def. NEW-2 (max-form f3; replaces the quadrature combination).**
f3(y) = max(E_pair(y)/τ_pair, E_num(y)/τ_num) with channel thresholds
calibrated on clean data (split conformal per channel). Justified by P3 /
Prop. 3.4; field evidence: 0.586 → 0.990 on V3. A per-channel union-bound
validity statement follows directly from Theorem 4.2 applied channel-wise.

**Target THM-A (detection power on cycles; the "first ★★★★ theorem").** In a
random-chain model with a planted closing-claim violation of gap γ and
extraction noise σ, the holonomy statistic has power → 1 as γ/σ → ∞ at a rate
governed by the cycle's minimum edge confidence — formalizing why V3 works.
Route: the holonomy h is Gaussian under H0 with variance σ²·L-independent
(length-invariance already implemented); power is a one-dimensional
z-test computation. This upgrades observed 0.990 into a predictive theorem.

**Target THM-B (conditional coverage; Phase-2.1 of the plan).** Mondrian
conformal by prompt-difficulty strata; Thm 4.2′ with per-stratum bounds. The
E2 ties finding adds a second motivation: discrete score atoms break the Beta
refinement, and stratification plus randomized tie-breaking restores it.

**Deferred (unchanged):** Tarski-Laplacian unification (own paper); encoder
invariance (weak Lipschitz version only).

## 5. Experiment roadmap

| Run | Config | Purpose | Status |
|---|---|---|---|
| Scale-up A (v8) | GSM8K, 1,000 chains, n = 300/cell, 6 negation + 3 closing templates | tighten CIs; template-family robustness for V3 | **complete — V3 0.995, all findings reproduce** |
| Replication B | second instrument (`FacebookAI/roberta-large-mnli`, architecture-distinct), key cells (V1, V3, V4), n = 300 | instrument-independence of the V3 result | **complete — V3 0.999, GREEN replicated; V4 activates under S2=2.3% (dose–response with Scale-up's S2=0.7% → +0.015)** |
| Organic-error corpus | model-generated GSM8K solutions; execution-labeled compositional errors | replace template insertion for the P2 headline | design |
| MATH extension | requires an equation extractor (no `<<>>` annotations in MATH) | corpus generality | after extractor audit |
| E3 instrument audit | ε_D / ε_NLI, n = 400 dual human annotation | activates Prop. 4.6 power certificate | **needs human annotators — user decision** |
| Drift/E-process (Regime III) | injected covariate shift, ACI tracking | field test of Thm 4.4 | Phase 3 |

## 6. Publication mapping (updated)

- **P1 (architecture + guarantees; SaTML/AISTATS/TMLR):** unconditionally
  viable; now carries Study A (v1 falsification) + E2 field coverage + the
  veto/taxonomy theorems.
- **P2 (sheaf logic gate; ACL/EMNLP/NeurIPS):** GREEN-gated — gate passed.
  Headline: V3 field result + Prop. NEW-1 boundary theorem + THM-A power
  theorem + localization. Needs Replication B and preferably the organic-error
  corpus before submission.
- **P3 (Tarski unification; LICS/JACT):** unchanged, independent.

## 7. Open items and decisions taken

1. **E3 human annotation (400 items, dual-coded)** — no annotators available
   at present. Interim path (clearly labeled non-confirmatory): a pilot
   machine-audit with a second model as adjudicator to estimate ε_D/ε_NLI
   ranges; the Prop. 4.6 power certificate remains "pending human audit" in
   all reporting until the dual-coded audit exists.
2. **Publication channel: SSRN revision** (author has no arXiv account; the
   v1 preprint is already on SSRN). SSRN-ready PDF built at
   `paper/v3_2/SSRN_Semantic_Validation_Gates_v3_2.pdf` (17 pp); upload as a
   revision of the existing SSRN submission so the DOI/abstract page carries
   the corrected, field-validated version.
3. Whether P2 is split out now or after the organic-error corpus — still
   open.
