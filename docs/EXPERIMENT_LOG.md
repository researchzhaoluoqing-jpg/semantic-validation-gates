# Experiment Log — Semantic Validation Gates

All runs executed on Kaggle (NVIDIA T4, fp16) via the API loop in
`experiments/run_loop.py`. Seeds, configs, and full outputs are archived under
`experiments/results/`. Confirmatory analyses follow
`docs/M1_PREREGISTERED_PROTOCOL.md`; smoke runs are diagnostic only.

---

## Study A — v1-instantiation control (kernel `semantic-validation-gates-v1`)

**Purpose.** Empirical audit of the *v1* operator instantiation (Wasserstein
distances to reference measures, EVT/Fréchet thresholds, lexicographic Π) that
the v3 manuscript replaces; provides the field evidence for Appendix A's
correction table. Design E1–E4 in `experiments/EXPERIMENT_DESIGN.md`.

| Ver | Date | Config | Status | Outcome |
|---|---|---|---|---|
| v1 | 2026-07-19 | smoke (QUICK, N=40, Qwen2.5-0.5B) | ERROR | missing notebook kernelspec (papermill); fixed in build step |
| v2 | 2026-07-19 | smoke | ERROR | Kaggle default P100 (sm_60) unsupported by torch build (`no kernel image`) |
| v3 | 2026-07-19 | smoke, `--accelerator nvidia-tesla-t4x2` | ERROR | invalid accelerator enum silently ignored → still P100 |
| v4 | 2026-07-19 | smoke, `--accelerator NvidiaTeslaT4` | COMPLETE | pipeline validated on T4; two methodological defects found (below) |
| v5 | 2026-07-19 | **full**: N=300 (GSM8K 150 + TruthfulQA 150), Qwen2.5-1.5B-Instruct, MiniLM embeddings, POT exact W2, nli-deberta-v3-xsmall, toxic-bert | COMPLETE | confirmatory results below |

**Smoke-run defects fixed before v5** (recorded per protocol discipline):
(i) degenerate-threshold artifact — gates identically zero on valid data
received τ = 1e−6, exploding normalized deviations; replaced by
half-minimum-positive-deviation floor. (ii) perturbation format re-check —
sentence-drop perturbations unconditionally re-scored f1 even when the format
constraint remained satisfied, inflating Π-flip rates.

**Study A results (v5, N=300).** Generator accuracy: GSM8K 64.7%,
TruthfulQA 47.3%.

- **EVT calibration (v1's Conjecture 5.3):** false-rejection control holds but
  vacuously — held-out FR = 0.000 at every α ∈ {0.01, 0.05, 0.10} on every
  gate (bound ≤ α never tight). Fréchet fits are over-conservative, consistent
  with the v3 observation that bounded scores lie in the Weibull, not Fréchet,
  max-domain of attraction.
- **Detection power (the cost of that conservatism):** only **10.6%** of
  incorrect outputs fail any gate; per-gate AUROC for answer incorrectness:
  f1 0.476, f2 0.600, f3 0.392 (below chance), f4 0.505, f5 0.623; ρ_max 0.567.
  The W2-to-reference instantiation has **no usable detection power**.
- **Stability (v1's Conjecture 5.4):** Π flips on **44%** of
  smallest-quartile perturbations — local constancy fails in this
  instantiation.
- **Verdict:** the v1 geometric instantiation is empirically inert as well as
  theoretically defective; this is direct field support for the v3 rewrite
  (exact/calibrated gates + conformal thresholds). Feeds the manuscript's
  Appendix A narrative and motivates Study B.

Artifacts: `experiments/results/full_v5/` (records.csv, evt_validation.json,
auroc.json, lipschitz.csv, summary.json, plots).

---

## Study B — M1 field study (kernel `svg-m1-field-study`)

**Purpose.** The pre-registered empirical linchpin (manuscript §7(3)(b);
protocol `docs/M1_PREREGISTERED_PROTOCOL.md`): sheaf energy vs. contradiction
counting under a real, temperature-calibrated NLI on real GSM8K chains, with
frozen GREEN/YELLOW/RED decision rules.

| Ver | Date | Config | Status | Outcome |
|---|---|---|---|---|
| v1 | 2026-07-19 | smoke | ERROR | harness dataset mount path not found; dynamic discovery added |
| v2/v4 | 2026-07-19 | smoke | ERROR | DeBERTa-v1 fp16 incompatibility (D1: fp32); V2 k=5 empty chain pool (D3) |
| v6 | 2026-07-19 | smoke (140 chains, 20/cell) | COMPLETE | pipeline validated; E0 field: S1-direct flat, S2 = 0; quadrature dilution diagnosed → deviation D2 registered |
| **v7** | 2026-07-19 | **confirmatory**: 450 chains, 150/cell (45 cal + 105 eval), 4000 bootstrap, 22.7k NLI pairs | COMPLETE | **VERDICT: GREEN** — V3: SHEAF_MAX AUROC 0.990 vs chance baselines, Δ=+0.489 [0.470, 0.503], Holm p=0.0018, FPR@95TPR 1% vs 94%, localization 0.24 vs 0.00; V1/V2: SHEAF ≡ WSUM (structural equivalence on assertion-only chains); V4: +0.019 (S2 vacuous); E2: Thm 4.2 bound holds (0.0952 ≤ 0.10), Beta law rejected via ties (39.7%) |

Full analysis: `docs/M1_RESULTS_AND_ANALYSIS.md`. Artifacts:
`experiments/results/m1_full_v7/`.

---

## Infrastructure notes

- Kernel pushes require `--accelerator NvidiaTeslaT4`; the default P100 is
  incompatible with current torch builds, and invalid enum values are silently
  ignored (discovered v3 of Study A).
- Notebooks are generated from percent-format `.py` sources via jupytext; a
  `kernelspec` block must be injected post-conversion (papermill requirement).
- Harness modules are attached as Kaggle dataset `luoqingzhao/svg-harness`;
  local wiring tests (`scratchpad/test_m1_wiring.py`) run the full E1/E2
  interface against a stub NLI before any GPU push.
