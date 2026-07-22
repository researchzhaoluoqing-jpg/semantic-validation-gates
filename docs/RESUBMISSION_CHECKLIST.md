# Resubmission checklist and version policy

Submission file: `paper/v3_2/SVG_submission.pdf` (18 pp, compiles clean).
Supersedes the earlier `SSRN_SVG_v3_2_rev1.pdf` / `SSRN_Semantic_Validation_Gates_v3_2.pdf`
builds, which still carried internal version markers on the cover.

---

## 0. Decisions taken (2026-07-22)

- **No correspondence with SSRN.** No appeal, no query about the rejection
  reason. SSRN does not reconsider and does not explain; the email drafted in
  `SUBMISSION_CORRESPONDENCE.md` will not be sent.
- **Reapply as a new submission** with the revised manuscript
  (`paper/v3_2/SVG_submission.pdf`).
- **Working assumption on the rejection cause:** the missing reference list.
  This is the most likely single trigger — SSRN's published not-accepted list
  names "non-scholarly articles… particularly those lacking references", the
  letter cited *submission type*, and v1 had zero citations. It remains an
  inference: the letter is a template and SSRN gives no individualized reason.
  The second named ground that cannot be excluded is **undisclosed AI use**;
  both are addressed in the revised manuscript (31 references; AI declaration
  on the PDF), so the resubmission does not depend on which one was decisive.

## 1. It is a NEW submission, not a revision

The v1 manuscript (Abstract ID 7031058) was **declined at screening**, so
nothing was ever posted. There is no abstract page, no DOI, and no version
chain to revise. Any route that starts from "revise my existing submission"
does not apply. Submit through the normal new-submission flow.

Do **not** file an appeal: SSRN states it does not reconsider rejections and
gives no individualized reasons.

---

## 2. Why the earlier submission most likely failed, and what now clears it

SSRN's published guidelines list, among content types **not accepted**,
"non-scholarly articles" — naming in particular *those lacking references*.
The rejection letter cited "submission type and screening criteria," which is
the bucket that category sits in.

| Screening signal | v1 (declined) | Present submission |
|---|---|---|
| References section | **absent** | present (20 entries) |
| In-text citations | **0** | 44 |
| Related-work section | absent | present |
| Empirical content | none | pre-registered field study, 3 runs, released artifacts |
| Front-matter status label | "Work in Progress – Preliminary Draft" | none |
| Main content | 4 unproven conjectures | proved propositions + theorems |
| Length | 4 pp / ~1,370 words | 18 pp |
| AI disclosure | absent | present (with abstract and on the PDF) |

---

## 3. Version policy going forward

**Rule: no internal version numbers on the public artifact.** Version history
lives in the git repository and in the DOI provider's own versioning; the PDF
cover carries only a date.

Changes applied for this build:

- Cover date line: `Consolidated manuscript (v3.2) — July 2026 / (v3.1
  revised to incorporate…)` → **`July 2026`**. The old line was internal
  working-paper bookkeeping; on a paper with no public version chain it reads
  as a draft-in-progress, which is the same category signal that sank v1.
- All in-body `v3.1` / `v3.2` markers removed (§6 "unchanged from v3.1",
  "new in v3.2"; §7 "registered in v3.1", "next steps (v3.2)"). A reader has
  no way to know what those versions are.
- Introduction now defines the earlier draft explicitly as **unpublished**
  ("An earlier, unpublished draft of this work (referred to below as v1)"),
  so nothing implies a prior public posting.
- Appendix A retitled "Correction Table: Withdrawn Constructions from the
  Earlier Draft"; column headers `v1 construct` / `v3 replacement` →
  `Earlier construct` / `Present replacement`.

**Keep the `v1` references in the body.** They are honest scholarly
self-correction backed by an empirical audit, and they are an asset, not a
liability — provided they clearly denote an unpublished earlier draft, which
they now do.

**Where versioning does live:**
- git: tag each submitted build (`git tag submission-2026-07`).
- Zenodo (if used): native concept-DOI + per-version DOIs handle this
  properly, which is the right place for a version chain.
- `paper/v3_2/README.md`: internal changelog and the v3.1→present numbering
  map.

---

## 4. Pre-submission checks (from SSRN's stated requirements)

- [x] Full-text PDF in English
- [x] Title and author affiliation shown on the PDF ("Luoqing Zhao,
      Independent Researcher")
- [x] Reference list present
- [x] AI disclosure statement on the PDF and positioned with the abstract
- [ ] **AI disclosure verified by the author** — the drafted statement covers
      the field study and the present revision only. If generative AI was
      also used in preparing the earlier v3.1 text (before the current work),
      the statement must be widened. Under-disclosure is a named rejection
      ground; err on the side of disclosing more.
- [ ] Complete SSRN author profile (required before submission)
- [ ] Abstract entered in the metadata form (check the field's length limit;
      trim if needed — the paper abstract is ~250 words)
- [ ] Date written: July 2026
- [ ] Subject-area / network selection — the residual risk. CS/AI is marginal
      to SSRN's social-science core; if no suitable network is available this
      may be declined on scope regardless of quality.

---

## 5. Honest expected value

The screening defects that plausibly sank v1 are fixed, and the present paper
is a materially different object. The residual risk is **scope**, which no
amount of revision addresses.

Recommended allocation of effort, unchanged: **TMLR** (rolling submissions,
no page limit, real peer review — where the released code and pre-registered
protocol count as strengths) as the primary route, with **Zenodo** for an
immediate citable DOI. An SSRN submission is cheap to attempt in parallel and
costs nothing but the form-filling.
