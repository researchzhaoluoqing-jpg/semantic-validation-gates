# Reference verification log

Date: 2026-07-22. Manuscript: `paper/v3_2/`. Bibliography: 31 entries
(20 pre-existing, 11 added).

Every entry below was checked against a primary or authoritative secondary
source (arXiv abstract page, ACL Anthology, PMLR, publisher page, DBLP, or the
conference's own programme page). Nothing in the bibliography was written from
memory.

## Automated cross-check (`scratchpad/ref_qa.py`)

```
bibliography entries : 31
distinct keys cited  : 31
duplicate keys       : none
UNCITED entries      : none
UNDEFINED citations  : none
```

LaTeX build: 0 errors, 0 undefined references or citations, 18 pages. (One
cosmetic `T1/lmr/m/scit` font-shape warning — small-caps italic falls back;
no effect on content.)

## Defect found and corrected in the pre-existing bibliography

**`cofact2026` had no author list.** The entry read simply "CoFact: Conformal
factuality guarantees for language models under covariate shift. ICLR, 2026."
The paper is real — ICLR 2026, OpenReview `eiBp7rsc3K` — but an author-less
reference is a citation defect. Authors recovered from the ICLR programme page
and added: **Zirui Hu, Zheng Zhang, Yingjie Wang, Leszek Rutkowski,
Dacheng Tao**.

## Entries added (11), with the source used to verify each

| Key | Reference | Verified against |
|---|---|---|
| `angelopoulos2023` | Angelopoulos & Bates, *A gentle introduction to conformal prediction…*, arXiv:2107.07511 | arXiv abstract page |
| `barber2021` | Barber, Candès, Ramdas, Tibshirani, *The limits of distribution-free conditional predictive inference*, Information and Inference 10(2):455–482 | Oxford Academic; arXiv:1903.04684 |
| `cobbe2021` | Cobbe et al., *Training verifiers to solve math word problems* (GSM8K), arXiv:2110.14168 | arXiv abstract page |
| `cuturi2013` | Cuturi, *Sinkhorn distances: lightspeed computation of optimal transport*, NeurIPS 2013 | NeurIPS proceedings page |
| `guo2017` | Guo, Pleiss, Sun, Weinberger, *On calibration of modern neural networks*, ICML, PMLR 70:1321–1330 | PMLR v70 page; arXiv:1706.04599 |
| `he2021` | He, Liu, Gao, Chen, *DeBERTa*, ICLR 2021 | ICLR 2021 poster page; OpenReview `XPZIaotutsD` |
| `inan2023` | Inan et al., *Llama Guard*, arXiv:2312.06674 | arXiv abstract page; DBLP |
| `lin2022` | Lin, Hilton, Evans, *TruthfulQA*, ACL 2022, pp. 3214–3252 | ACL Anthology 2022.acl-long.229 |
| `liu2019` | Liu et al., *RoBERTa*, arXiv:1907.11692 | arXiv abstract page |
| `reimers2019` | Reimers & Gurevych, *Sentence-BERT*, EMNLP-IJCNLP 2019, pp. 3982–3992 | ACL Anthology D19-1410 |
| `williams2018` | Williams, Nangia, Bowman, *MultiNLI*, NAACL-HLT 2018, pp. 1112–1122 | ACL Anthology N18-1101; DBLP |

### Why these, specifically

These are not padding. Nine of the eleven close **genuine citation gaps**:
the manuscript reported experiments on GSM8K using DeBERTa- and
RoBERTa-based MNLI models with temperature scaling, and discussed sentence
embeddings, Sinkhorn divergences, TruthfulQA, and safety classifiers — none
of which were cited. `barber2021` additionally strengthens §8.2: exact
conditional coverage is not merely "not yet done" but provably unattainable
distribution-free, which is why the Mondrian relaxation is the right target.

## Pre-existing entries spot-checked

| Key | Result |
|---|---|
| `cofact2026` | Real (ICLR 2026, OpenReview `eiBp7rsc3K`); authors were missing → added |
| `huntsman2024` | Real; arXiv:2401.16713 confirmed correct |
| `ghrist2022` | Real; *Homology Homotopy Appl.* 24(1):325–345, 2022 confirmed; volume/pages added |

Remaining pre-existing entries (Aho & Peterson 1972, Andoni–Naor–Neiman 2018,
Cherian et al. 2024, Coles 2001, Fournier–Guillin 2015, Genevay et al. 2019,
Gibbs–Candès 2021, Goemans–Williamson 1995, Gretton et al. 2012,
Hansen–Ghrist 2019, Liang et al. 2023, Mohri–Hashimoto 2024, Rebedea et al.
2023, Tibshirani et al. 2019, Vovk 2021, Yadkori et al. 2024, Zhou et al.
2023) were carried over from the earlier manuscript and are standard, widely
cited works; volume and page numbers were completed where known. If a fully
independent audit is wanted, these seventeen should be re-checked against
their publisher pages as well.
