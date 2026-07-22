# Error catalog and writing checklist

A record of every defect found while preparing this manuscript, kept so the
same classes of mistake can be caught earlier next time. Each entry states
what happened, why it survived normal review, and the check that would have
caught it.

The single most useful generalization from this list:

> **Every defect that survived to the final audit was a plausible-looking
> number or a plausible-looking citation.** None of them looked wrong on a
> read-through. Errors that look wrong get fixed immediately; errors that look
> right are the ones that reach print. Proofreading cannot catch this class —
> only mechanical reconciliation against the source of truth can.

---

## 1. Reported numbers (highest severity)

### 1.1 Statistics silently taken from the wrong run

The instrument report in §6.2 gave pre-calibration ECE `0.047` and MNLI
accuracy `0.917`. Both were the **smoke run's** diagnostic values; the
confirmatory run's were `0.0396` and `0.9115`. The temperature in the same
sentence (`1.452`) *was* the confirmatory value, so a single sentence mixed
two runs.

*Why it survived:* the wrong values were the right order of magnitude, told a
consistent story (calibration improves ECE), and matched a real log — just
the wrong log. Nothing about the sentence read as suspicious.

*Check:* reconcile every reported quantity against the JSON artifact of the
run that produced it. Never transcribe from a scrollback, a chat summary, or
an intermediate note.

*Structural fix:* smoke/diagnostic runs and confirmatory runs should write to
clearly separate output directories, and the manuscript should cite the run
identifier alongside each number during drafting (stripped before submission).

### 1.2 Rounding a boundary value the wrong way

A Clopper–Pearson upper bound of `0.04748` was written as `4.8%`. Correct to
three significant figures is `4.7%`.

*Check:* derive rounded values programmatically from the artifact rather than
by hand; a boundary at `…4 8` is exactly where hand-rounding drifts.

### 1.3 A diagnosis that was itself wrong

The first reading of the E2 coverage audit was "the Beta law is rejected
because 39.7% of scores are tied." Plausible, and it was written into the
manuscript. It was **false**: randomized tie-breaking did not restore the law,
and null checks showed the same test rejects ideal continuous i.i.d. data
under the same procedure. The real cause was that empirical per-split
coverages convolve the exact conditional coverage with test-set binomial
noise — the *audit statistic* was miscalibrated, not the theorem.

*Why it survived:* the wrong explanation was mechanistically reasonable and
matched a real observation (there were indeed 39.7% ties).

*Check:* before publishing a diagnosis of an anomaly, run the null — feed the
procedure data that satisfies the assumption and confirm it *passes*. An
explanation that has not been null-checked is a hypothesis, not a finding.

---

## 2. References

### 2.1 A truncated author list presented as complete

`yadkori2024` listed four authors joined by *and*: "Y. Abbasi Yadkori,
I. Kuzborskij, A. György, and C. Szepesvári." The paper has **twelve**
authors. Writing *and* before the last name asserts the list is complete, so
this silently removed eight authors from the record. The surname was also
missing its hyphen (*Abbasi-Yadkori*).

*Why it survived:* four plausible names in correct format; nothing signals
truncation.

*Check:* for every multi-author entry, confirm the author count against the
abstract page. Use `et al.` when truncating — never `and`.

### 2.2 A reference with no authors at all

`cofact2026` consisted only of a title, venue, and year. The paper is real,
but an author-less entry is not a usable citation.

*Check:* mechanically assert that every entry has an author field.

### 2.3 Bibliographic fields inferred rather than looked up

While completing volume/page numbers, I wrote `J. ACM 42(6)` for
`goemans1995`. The volume and pages were verified; **the issue number was
not** — it was inferred from familiarity. It has been removed.

*Why it matters:* this is the mechanism by which fabricated citations enter a
paper. The failure mode is not deliberate invention; it is filling a field
that "obviously" has a known value without opening the source. Every such
field is either verified or omitted — an omitted issue number costs nothing,
a wrong one is a fabrication.

*Check:* if a bibliographic field was not read off a source in this session,
delete it.

---

## 3. Experimental method

| # | Defect | Effect | Lesson |
|---|---|---|---|
| 3.1 | Degenerate gates (identically zero on valid data) received threshold τ = 1e-6 | Normalized deviations exploded; empirical Lipschitz constant reached 5×10⁵ | Every fallback branch needs a sanity bound, not just a nonzero guard |
| 3.2 | Sentence-drop perturbation re-scored the format gate unconditionally | Inflated classification-flip rates, wrongly indicting a stability claim | A perturbation must only change what it is meant to change; re-derive all preconditions per variant |
| 3.3 | Channel aggregation by quadrature let pairwise noise drown the compositional signal (0.586 vs 0.990) | Would have produced a false negative on the study's load-bearing prediction | The paper's own principle (max-aggregate localized signals) applied to itself; check whether your stated principles govern your implementation |
| 3.4 | k=5 cell drew from an empty chain pool | Crash mid-run | Assert non-empty strata before the run, not on first use |

Smoke runs earned their cost here: 3.1–3.4 were all caught at n=20 before any
confirmatory compute was spent.

---

## 4. Manuscript framing and submission

### 4.1 The v1 rejection was predictable from the document profile

The declined submission was 4 pages / ~1,370 words with **zero citations, no
reference section, no related-work section, no empirical content**, front
matter labelled "Work in Progress — Preliminary Draft", and four unproven
conjectures as its main content. SSRN's published guidelines list
"non-scholarly articles" — *particularly those lacking references* — among
content types not accepted.

*Lesson:* before submitting anywhere, check the venue's stated
not-accepted list literally, item by item, against the document. A paper can
be correct and still be unpostable on format grounds.

### 4.2 Internal version bookkeeping on a public artifact

The cover carried "Consolidated manuscript (v3.2) — July 2026 / (v3.1 revised
to incorporate…)", and the body referred to "unchanged from v3.1", "new in
v3.2". Readers have no access to those versions; on a paper with no public
version chain this reads as a draft in progress — the same signal that sank
v1.

*Lesson:* the public artifact carries a date, not a version number. Version
history belongs in the repository and in the DOI provider's versioning.

### 4.3 Self-correction is an asset; version autobiography is not

The correction table documenting withdrawn constructions was intellectually
honest and worth keeping in principle, but for a fresh submission it
foregrounded a defective predecessor the reader had never seen. The technical
substance was retained by rewriting each passage as design rationale ("an
isometric embedding of the W₂ geometry is impossible for d ≥ 3, so no such
claim is made") rather than version history ("this replaces the v1 claim
that…").

### 4.4 A procedural claim I got wrong

I advised uploading the revision "as a revision of the existing SSRN
submission." Since v1 had been **rejected**, nothing was posted and there was
nothing to revise. *Lesson:* confirm the state of a submission before
recommending a workflow that depends on it.

---

## 5. Pre-submission checklist

Run every item; do not substitute reading for any of them.

**Numbers**
- [ ] Every reported quantity reconciled programmatically against the artifact
      of the run that produced it (`paper_qa.py`)
- [ ] Confirmatory and diagnostic runs stored in separate directories; no
      number sourced from a diagnostic run
- [ ] All rounding derived from the artifact, not by hand
- [ ] Every anomaly diagnosis null-checked before it is written as a finding

**References**
- [ ] Every entry opened at a primary source in this session (`REFERENCE_VERIFICATION.md`)
- [ ] Author counts confirmed; `et al.` used for truncation, never `and`
- [ ] No bibliographic field present that was not read off a source
- [ ] Cross-check: entries = citations, no uncited entries, no undefined
      citations (`ref_qa.py`)

**Document**
- [ ] No internal version markers; cover carries a date only
- [ ] No draft-status language, TODO markers, or `??` references
- [ ] All `\ref` targets defined; compiles with zero errors
- [ ] Venue's not-accepted list checked literally against the document
- [ ] Author affiliation on the PDF; abstract present; AI-use declaration
      present and scoped to the *entire* drafting history, not only the most
      recent revision

**Process**
- [ ] Expected values inside the QA script updated in the same commit as any
      change to reported numbers, so the two cannot drift apart
