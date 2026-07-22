# Pre-submission QA report

Date: 2026-07-22. Artifact: `paper/v3_2/SVG_submission.pdf` (18 pp).
Reproduce with `python paper/v3_2/paper_qa.py` and
`python paper/v3_2/ref_qa.py`.

## Result

**0 failures.** Every number reported in the manuscript reconciles with the
raw experimental artifacts; all cross-references resolve; the bibliography is
consistent; SSRN's stated submission requirements are met by the PDF.

## What was checked

**A. Numeric reconciliation against raw artifacts (86 checks).** Every
reported quantity was compared against the JSON produced by the run that
generated it — `m1_full_v7` (confirmatory), `m1_scale_v8` (scale-up),
`m1_repl_B` (replication). This covers the full §6 results table (7 cells ×
6 arms = 42 values), all confidence intervals, Holm-adjusted p-values,
FPR-at-95%-TPR operating points, localization rates, instrument calibration
statistics, S1/S2 measurements, E2 coverage figures, and every sample size.

**B. Structural checks.** All 32 `\ref` targets defined; no broken `??`
references; no residual internal version markers; no draft-status labels; no
TODO markers; no doubled words.

**C. Bibliography.** 31 entries, 31 cited, no uncited entries, no undefined
citations, no duplicate keys (see `REFERENCE_VERIFICATION.md` for the
source-by-source audit).

**D. SSRN requirements.** Title present; author affiliation on the PDF;
abstract present; generative-AI declaration present on the PDF and positioned
with the abstract; reference list present.

## Defects found and corrected

**Q-1 (material). Instrument statistics were taken from the wrong run.** §6.2
reported the calibration ECE as `0.047` pre-calibration and MNLI accuracy as
`0.917`. Those are the **smoke-run (v6) diagnostic values**; the confirmatory
run's are `0.0396` and `0.9115`. The temperature (`1.452`) and every other
figure in the section were correctly from the confirmatory run, so this was a
localized transcription slip that mixed a diagnostic run's instrument report
into the confirmatory one. Corrected to `0.040` and `0.911` in the manuscript
and in `M1_RESULTS_AND_ANALYSIS.md`.

**Q-2 (minor). Rounding error in a reported interval.** The replication's
hedged false-positive Clopper–Pearson upper bound is `0.04748`, reported as
`4.8%`. Corrected to `4.7%`.

## Notes (not defects)

- Two propositions (`prop:nomask`, `prop:wellposed`) carry labels that are
  never `\ref`'d. Harmless; labels retained for future cross-referencing.
- One cosmetic LaTeX font warning (`T1/lmr/m/scit`, small-caps italic falls
  back). No effect on output.

## Standing caution

Both defects above were transcription errors from experimental logs into
prose, and neither was visible on a read-through — they were only caught by
mechanical reconciliation against the artifacts. Any future revision that
touches reported numbers should re-run `paper_qa.py` before the PDF is
regenerated, and the expected values inside that script should be updated in
the same commit as the manuscript so the two cannot drift apart.
