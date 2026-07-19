# Semantic Validation Gates — v3.2 manuscript

Modular LaTeX source (`main.tex` + `sections/*.tex`). Build: `pdflatex main`
(twice). Compiles clean: 17 pages.

**Provenance note.** The v3.1 LaTeX source was not available on this machine;
this tree was reconstructed from the v3.1 PDF (`../../paper_v3_AllIn.pdf`)
full-text extraction and then revised to v3.2. Sections 1–5, 7–9 and
Appendix A are faithful transcriptions of v3.1 (please diff against your
original source if you have it — especially the math in §3–§5); the v3.2
revisions are:

- **Abstract + Contribution 5**: field-study result replaces the
  simulation-only claim.
- **§3.3**: new Prop. 3.x "structural equivalence" (sheaf ≡ WSUM on
  assertion-only acyclic graphs) + Remark on where the sheaf adds capability;
  new Definition "max-form f3" channel aggregation (P3), replacing quadrature.
- **§6**: restructured into 6.1 mechanism simulation (v3.1 Table 1 retained as
  illustration) + 6.2 pre-registered field study (confirmatory results
  table, S1/S2 adjudication) + 6.3 calibration field test (Thm 4.2 bound
  verified; Beta-law ties caveat).
- **§7**: protocol items annotated with execution status; item (8) registered
  next steps.
- **§8**: added 8.4 scope of field evidence; ties caveat in 8.2; V4
  instrument-dependence in 8.1; new open problem (holonomy power theorem).
- **Appendix A**: v1 empirical audit paragraph (Study A results) added; EVT
  row updated.

**Transcription verification (2026-07-19).** 14 load-bearing formulas in
§3–§5 (Thm 4.2 bounds, order-statistic threshold, Thm 4.3 α/5, Thm 4.4 ACI
bound, Prop 4.6 product, Thm 5.2 partition sets, Dec veto case, Prop 5.7
margin condition, Prop 5.9 one-sided chain, Prop 3.1 Lipschitz bound,
Prop 3.4 MMD bound, f₂ min-form, margin definition) were mechanically
compared against the v3.1 PDF text extraction: all identical.

**Theorem numbering map (v3.1 → v3.2).** New §3.3 insertions shift the shared
counter: v3.1 Prop 3.1 → 3.1 (unchanged); Prop 3.2 (gap) → 3.3;
Prop 3.3 (no-poly) → 3.4; Prop 3.4 (dilution) → 3.7; Prop 3.5 (unit
sensitivity) → 3.8. New objects: Def 3.2 (max-form f3), Prop 3.5
(structural equivalence), Remark 3.6. §4–§5 numbering unchanged. External
documents citing v3.1 numbers (protocol, strategy docs) refer to the v3.1
scheme.

Experimental basis: `docs/M1_RESULTS_AND_ANALYSIS.md`,
`docs/M1_PREREGISTERED_PROTOCOL.md` (deviations D1–D4),
`docs/EXPERIMENT_LOG.md`.
