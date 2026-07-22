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

## Full independent audit of the 20 pre-existing entries

All twenty carried-over entries were checked against a primary or
authoritative source. **31 of 31 references in the bibliography are real
publications.** Two substantive defects and several incomplete fields were
found and corrected.

### Defects found and corrected

**D-1. `cofact2026` had no author list.** The entry read "CoFact: Conformal
factuality guarantees for language models under covariate shift. ICLR, 2026."
The paper is real (ICLR 2026; OpenReview `eiBp7rsc3K`) but an author-less
reference is a citation defect. Authors recovered from the ICLR programme
page: **Zirui Hu, Zheng Zhang, Yingjie Wang, Leszek Rutkowski, Dacheng Tao.**

**D-2. `yadkori2024` had a wrong and misleadingly truncated author list.** The
entry read "Y. Abbasi Yadkori, I. Kuzborskij, A. György, and C. Szepesvári" —
four names joined by *and*, which asserts a complete list. The paper has
**twelve** authors, and the surname is hyphenated (*Abbasi-Yadkori*). Corrected
to the full list: Abbasi-Yadkori, Kuzborskij, Stutz, György, Fisch, Doucet,
Beloshapka, Weng, Yang, Szepesvári, Cemgil, Tomasev.

### Incomplete fields completed (all newly verified, none written from memory)

`cherian2024` pages 114812–114842 · `gibbs2021` pages 1660–1672 ·
`genevay2019` PMLR 89:1574–1583 · `tibshirani2019` pages 2526–2536 ·
`rebedea2023` pages 431–445 · `hansen2019` issue 3(4) · `fournier2015` issue
162(3–4) · `ghrist2022` 24(1):325–345 · `coles2001` series name ·
`liang2023` lead authors named rather than "P. Liang et al."

### Correction to my own earlier additions

`goemans1995`: I had written the issue number as 42**(6)**. Volume 42 and
pages 1115–1145 are confirmed by the ACM Digital Library entry, but the issue
number was not independently confirmed, so it has been **removed** rather than
left as an unverified assertion.

### Audit table

| Key | Verified against | Result |
|---|---|---|
| `aho1972` | SIAM J. Comput. record | ✓ 1(4):305–312, 1972 exact |
| `andoni2018` | Ann. Sci. ÉNS / BGU portal; arXiv:1509.08677 | ✓ 51(3):657–700 exact |
| `cherian2024` | NeurIPS 2024 proceedings page | ✓ real; pages added |
| `cofact2026` | ICLR 2026 programme; OpenReview | ✓ real; **authors added (D-1)** |
| `coles2001` | Springer / ISBN 9781852334598 | ✓ real; series added |
| `fournier2015` | Springer PTRF; arXiv:1312.2128 | ✓ 162:707–738 exact |
| `genevay2019` | PMLR v89 proceedings | ✓ real; pages added |
| `ghrist2022` | Homology Homotopy Appl.; arXiv:2007.04099 | ✓ 24(1):325–345 |
| `gibbs2021` | NeurIPS 2021 proceedings; arXiv:2106.00170 | ✓ real; pages added |
| `goemans1995` | ACM DL 10.1145/227683.227684 | ✓ 42:1115–1145; issue removed |
| `gretton2012` | JMLR v13 page | ✓ 13:723–773 exact |
| `hansen2019` | Springer JACT 10.1007/s41468-019-00038-7 | ✓ 3(4):315–358 |
| `huntsman2024` | arXiv:2401.16713 abstract page | ✓ ID exact |
| `liang2023` | TMLR / Princeton, HKUST portals | ✓ real; authors expanded |
| `mohri2024` | ICML 2024 (41st ICML) proceedings | ✓ real |
| `rebedea2023` | ACL Anthology 2023.emnlp-demo.40; DBLP | ✓ real; pages added |
| `tibshirani2019` | NeurIPS 2019; arXiv:1904.06019 | ✓ real; pages added |
| `vovk2021` | Project Euclid, DOI 10.1214/20-STS817 | ✓ 36(4):595–611 exact |
| `yadkori2024` | arXiv:2405.01563 abstract page | ✓ real; **authors fixed (D-2)** |
| `zhou2023` | arXiv:2311.07911 abstract page | ✓ ID and 8-author list exact |

Verified 2026-07-22. Re-running `paper/v3_2/ref_qa.py` reproduces the
key/citation cross-check; the source links for each row are in this session's
search record.
