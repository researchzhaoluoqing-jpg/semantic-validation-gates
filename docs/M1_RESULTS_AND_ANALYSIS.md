# M1 Field Study — Results and Analysis

**Study:** Sheaf energy vs. contradiction counting under a real NLI instrument
(pre-registered protocol: `docs/M1_PREREGISTERED_PROTOCOL.md`, frozen 2026-07-19)
**Confirmatory run:** kernel `svg-m1-field-study` v7, 2026-07-19, NVIDIA T4.
Smoke runs v1–v6 were diagnostic only; all deviations (D1–D4) were registered
before the confirmatory run.

---

## 1. Instrument report (§4.6 reporting requirements)

DeBERTa-large-MNLI, fp32 (D1), temperature-scaled on MNLI validation-matched
(n = 2,000): **T = 1.452, ECE 15-bin = 0.0112 post-calibration** (0.047
pre-calibration), MNLI accuracy 0.917. 22,706 ordered sentence pairs scored;
per-chain caching; the instrument never received injection locations or
distances. Corpus: 450 GSM8K training-split chains (4–10 steps).

## 2. E0 — field adjudication of the mechanism assumptions

**(S1) Distance decay — fails for verbatim negations.** Calibrated
contradiction confidence on the *direct* pair (¬c_i, c_i) is flat in k:
0.749, 0.740, 0.742, 0.764, 0.756 for k = 1…5 (SD ≈ 0.17). The simulated decay
law c(k) = 0.95 − 0.13k does **not** transfer: a modern NLI recognizes a
template negation of a claim regardless of where it sits in the chain.
Cross-pair confidence (¬c_i vs. c_{i+k}) sits at ≈ 0.50 with a mild downward
drift — real but not threshold-crossing. **Consequence:** the Table-1
"threshold collapse at k ≥ 4" mechanism is not reproduced for verbatim
negations; prediction P-C resolved on its first branch.

**(S2) Hedged false positives — fails outright.** Hedged-hypothetical
constructions were flagged as contradictions (w ≥ 0.5) in **0 of 300** trials
(Clopper–Pearson 95%: [0, 0.012]). The simulated U(0.55, 0.85) false-positive
regime does not exist under this calibrated instrument; V4's reconciliation
mechanism is vacuous in this field setting.

## 3. E1 — five-arm paired comparison (n = 150/cell; 45 calibration + 105 evaluation)

AUROC (evaluation split), primary arm **SHEAF_MAX** (P3 max-aggregation over
channel-calibrated pairwise energy and numeric holonomy; deviation D2), with
the as-specified quadrature energy (SHEAF-quad) as sensitivity arm:

| Cell | SHEAF_MAX | SHEAF-quad | COUNT | WSUM | NLIMAX | SAT | ΔAUROC vs best bl [95% CI] | Holm p | Loc S/B |
|---|---|---|---|---|---|---|---|---|---|
| V1 k=1 | 0.719 | 0.719 | 0.696 | 0.719 | 0.531 | 0.514 | 0.000 [0.000, 0.000] | 1.000 | 0.21 / 0.94 |
| V2 k=2 | 0.741 | 0.741 | 0.710 | 0.741 | 0.520 | 0.505 | 0.000 | 1.000 | 0.17 / 0.91 |
| V2 k=3 | 0.756 | 0.756 | 0.734 | 0.756 | 0.513 | 0.505 | 0.000 | 1.000 | 0.06 / 0.94 |
| V2 k=4 | 0.717 | 0.717 | 0.685 | 0.717 | 0.503 | 0.500 | 0.000 | 1.000 | 0.03 / 0.90 |
| V2 k=5 | 0.739 | 0.739 | 0.701 | 0.739 | 0.502 | 0.500 | 0.000 | 1.000 | 0.02 / 0.92 |
| **V3 k=0** | **0.990** | 0.586 | 0.498 | 0.501 | 0.500 | 0.500 | **+0.489 [0.470, 0.503]** | **0.0018** | **0.24 / 0.00** |
| V4 k=1 | 0.751 | 0.751 | 0.696 | 0.732 | 0.518 | 0.510 | +0.019 [0.009, 0.030] | 0.0018 | 0.14 / 0.91 |

Operating point on V3 (FPR at 95% TPR): **SHEAF_MAX 0.010**; COUNT/WSUM/NLIMAX
0.943; SAT 1.000.

### Pre-registered prediction adjudication

- **P-A (V3, load-bearing): CONFIRMED, exceeding its target.** Pairwise
  baselines are at chance (0.498–0.501; blind by construction — every sentence
  pair is individually consistent); SHEAF_MAX reaches 0.990 (target ≥ 0.85)
  with top-1 localization 0.24 vs. an exact 0.00 for all baselines.
- **P-B (V4): NOT met** (+0.019 vs. WSUM, below the 0.03 bar) — exactly as
  E0-S2 predicted: with a zero hedged-FP rate there is nothing for
  assertion-aware reconciliation to discount.
- **P-C: resolved on branch 1.** With S1-direct flat, COUNT does not collapse
  on V2, and SHEAF ≡ WSUM there (see §5.1).

### Frozen-rule verdict

> **GREEN** — PE1 satisfied on V3 (ΔAUROC = +0.489 ≥ 0.03, CI lower bound
> 0.470 > 0) **and** the WSUM anti-artifact clause holds on V3
> (SHEAF − WSUM = +0.489 ≥ 0.03). The sheaf win cannot be attributed to
> de-thresholding.

## 4. E2 — conformal coverage field test (Theorem 4.2)

Clean-chain sheaf scores (pool n = 735), n_cal = 200, α = 0.10, R = 1,000
splits: pooled exceedance **0.0952 ≤ α** (exact binomial p = 1.0 against
inflation) — the finite-sample false-rejection bound of Theorem 4.2 **holds in
the field**. The Beta(m, n+1−m) coverage-distribution law is rejected by KS
(p ≈ 0): 39.7% of pool scores are tied (many all-clean graphs score identically),
violating the law's continuity assumption. The tie-safe upper bound is the
correct field statement; the manuscript should cite the continuity caveat
explicitly (deviation D4).

## 5. Findings beyond the endpoints

### 5.1 A structural equivalence, not an empirical accident

On the V1/V2 cells the primary and WSUM columns are *identical to three
decimals in every cell*. This is mathematics, not noise: on a claim graph whose
vertices are all asserted (clamped to 1) and whose only structure is a chain of
entailments plus contradiction edges, every contradiction edge has fixed
residual 1, every entailment edge residual 0, and the relaxed unified energy
reduces to √(Σ_e w_e) — a strictly monotone transform of WSUM, hence identical
in rank metrics. **The sheaf construction adds detection capability precisely
when the graph carries structure a single edge cannot see: cycles (V3's
numeric holonomy), free vertices (hedged nodes), or certificate-layer
interactions.** We recommend stating this as a proposition in the manuscript;
it converts an apparent null result into the theory that explains where the
tool's value lives.

### 5.2 The dilution theorem strikes inside f3 — and P3 fixes it

The as-specified quadrature energy scores 0.586 on V3; the P3 max-aggregated
form scores 0.990 from the same channel values. Real pairwise-NLI noise on
mathematical text (mean clean pairwise energy ≈ 3.1 vs. holonomy signal
0.4–2.0) drowns the compositional signal under any additive combination. This
is the manuscript's own Prop. 3.4 dilution phenomenon recurring one level
down, and its P3 remedy applied one level down. The channel-calibrated
max-form should become the *defined* f3 aggregation in §3.3.

### 5.3 Field NLI noise taxes every pairwise method

Real NLI flags spurious contradictions between ordinary solution steps
(different numbers in different sentences), capping even the best pairwise
arms at ≈ 0.72–0.76 AUROC on V1/V2 and driving SAT to chance (both classes
contain w ≥ 0.5 edges). Sheaf top-1 localization on V1/V2 (0.02–0.21) loses to
the simple above-threshold rule (0.90–0.94) for the same reason: on
structure-less graphs the hotspot is just "the largest w," and noise edges
compete. Localization is a *V3-specific* capability (0.24 vs. an exact 0.00),
not a general one — the manuscript's localization claim must be scoped
accordingly.

## 6. Decision and recommended manuscript revisions

**Decision (per protocol §7): GREEN — no pivot.** The sheaf logic gate is
confirmed as the flagship contribution, with a sharper and more defensible
claim than the simulated Table 1 suggested:

> *The weighted sheaf energy adds detection capability exactly on the class of
> violations that is invisible to pairwise methods by construction —
> compositional (multi-claim) inconsistencies — where it attains AUROC 0.990
> and FPR@95TPR of 1% against chance-level baselines, and it is the only method
> with nonzero localization there. On pairwise-visible violations it provably
> coincides with weighted counting.*

Concrete revisions to the v3.1 manuscript:

1. **§6 (mechanism study):** replace the S1/S2-conditional simulation narrative
   with the field results; keep Table 1 as the *mechanism illustration* and add
   the field table above as the confirmatory evidence. Report S1-direct
   flatness and S2 = 0 as measured facts retiring both simulated assumptions.
2. **§3.3:** (i) add the structural-equivalence proposition (§5.1 above) with
   its two-line proof; (ii) define f3's channel aggregation as the calibrated
   max-form, citing P3/Prop. 3.4 (§5.2 above); the quadrature form becomes a
   remark.
3. **§7 ablation (b):** mark as executed; success criteria met on the
   compositional cell; record V4's vacuity under a calibrated instrument as an
   assumption-test outcome, not a failure.
4. **Theorem 4.2 presentation:** cite the field coverage result (0.0952 ≤ 0.10)
   and add the ties caveat for the coverage-distribution refinement.
5. **Localization claim:** scope to compositional violations.
6. **Appendix A:** cite Study A (v1-instantiation control, `EXPERIMENT_LOG.md`)
   as empirical confirmation that the v1 geometric construction has no
   detection power (10.6% detection, f3 AUROC 0.39, 44% small-perturbation
   classification flips).

## 6b. Replication B — second instrument (added same day)

Key cells replicated with an architecture-distinct instrument
(`FacebookAI/roberta-large-mnli`; T = 1.337, ECE 0.012, MNLI acc 0.900; 600
chains, n = 150/cell, 25,786 pairs):

| Cell | SHEAF_MAX | SHEAF-quad | COUNT | WSUM | SAT | Δ vs best bl | Holm p | Loc S/B | FPR@95TPR (MAX) |
|---|---|---|---|---|---|---|---|---|---|
| V1 k=1 | 0.752 | 0.752 | 0.679 | 0.752 | 0.505 | 0.000 | 1.000 | 0.17/0.63 | 0.605 |
| **V3** | **0.999** | 0.593 | 0.499 | 0.500 | 0.510 | **+0.489 [0.479, 0.498]** | **0.0008** | **0.33/0.00** | **0.005** |
| V4 k=1 | 0.743 | 0.743 | 0.639 | 0.707 | 0.514 | **+0.035 [0.029, 0.042]** | 0.0008 | 0.15/0.68 | 0.657 |

Verdict: **GREEN replicated.** All three structural findings reproduce
(V3 headline, quadrature dilution, V1 counting-equivalence), and the E2 bound
holds again (0.0995 ≤ 0.10; ties only 6.7% under this instrument's more
continuous scores). The instructive difference: this instrument's hedged
false-positive rate is **nonzero** (S2 = 2.3% [0.9%, 4.8%]) and, exactly as
the mechanism predicts, **V4's assertion-aware capability activates**
(+0.035 ≥ the 0.03 bar) where it was vacuous under the zero-S2 instrument.
P-B is therefore not falsified but *instrument-conditional* — switched on
precisely when S2 > 0 — which the two instruments jointly demonstrate.

## 7. Threats to validity

- **Synthetic insertion:** violations are template-inserted into real chains
  (the §7 pre-registered method); model-generated organic errors are the next
  corpus (Phase 3).
- **Single instrument / single corpus:** one NLI checkpoint, GSM8K only;
  replication with a second checkpoint and MATH is required before P2
  submission.
- **V3 closing-claim template:** the compositional violation is asserted via
  one synthetic English sentence built from real chain values; varying the
  template family is a cheap robustness check.
- **In-study calibration split:** channel τ's use 30% of each cell's cases;
  they are excluded from evaluation, and pairing is preserved, but a
  deployment-grade τ would come from an independent clean corpus.

## 8. Next steps (GREEN branch of the research plan)

1. Scale-up per ERS: n = 1,000/cell, MATH corpus added, second NLI checkpoint
   (replication); template-family robustness for V3.
2. Organic-error corpus: model-generated solutions with naturally occurring
   compositional errors, labeled by execution.
3. E3 instrument audit (ε_D, ε_NLI with human annotation, n = 400 dual-coded)
   to activate the Prop. 4.6 power certificate.
4. Manuscript revision per §6 above; then P2 (sheaf logic gate) manuscript
   with the V3 field result as the headline.
