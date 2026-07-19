"""
svg_experiments/stats.py -- Statistical machinery for E0-E4 (ERS v1.0 SAP).
Every function names the theorem / methodological authority it implements.
Pure numpy+scipy: fully testable today.
"""
from __future__ import annotations
import numpy as np
from scipy import stats as sps


def auroc(pos, neg) -> float:
    """AUC == Mann-Whitney U/(n1*n0); ties half credit.
    Backing: AUC-U equivalence (Hanley-McNeil 1982)."""
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    ranks = sps.rankdata(np.concatenate([pos, neg]))
    u = ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2
    return float(u / (len(pos) * len(neg)))


def paired_bootstrap_delta_auroc(posA, negA, posB, negB,
                                 n_boot=10_000, seed=0):
    """E1 primary endpoint PE1: Delta-AUROC(A-B) with *paired* resampling over
    base items (each item contributes its violated score to pos and its clean
    score to neg, for BOTH methods -> resampling indices jointly preserves the
    pairing). Chosen over DeLong: valid under arbitrary cross-method
    dependence and reusable verbatim for localization endpoints.
    Returns (delta, ci_lo, ci_hi, p_two_sided [percentile-bootstrap])."""
    n = len(posA)
    assert len(negA) == len(posB) == len(negB) == n, "paired design required"
    posA, negA, posB, negB = (np.asarray(a, float) for a in (posA, negA, posB, negB))
    delta = auroc(posA, negA) - auroc(posB, negB)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, n, n)
        boots[b] = auroc(posA[i], negA[i]) - auroc(posB[i], negB[i])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    p = 2 * min((boots <= 0).mean(), (boots >= 0).mean())
    return float(delta), float(lo), float(hi), float(min(1.0, max(p, 1 / n_boot)))


def clopper_pearson(k, n, conf=0.95):
    """Exact binomial CI (Beta quantiles). ERS G-level reporting standard."""
    a = (1 - conf) / 2
    lo = 0.0 if k == 0 else float(sps.beta.ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(sps.beta.ppf(1 - a, k + 1, n - k))
    return lo, hi


def wilson(k, n, conf=0.95):
    """Wilson interval -- used for sample-size planning (E3: n=400 gives
    halfwidth ~= +/-0.03 at p-hat ~= 0.1)."""
    z = sps.norm.ppf(1 - (1 - conf) / 2)
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(c - h), float(c + h)


def holm(pvals):
    """Holm step-down adjusted p-values. FWER control with NO independence
    assumption -- required because per-k tests in E1 share data."""
    p = np.asarray(pvals, float); m = len(p)
    order = np.argsort(p); adj = np.empty(m); running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def conformal_coverage_law(n_cal, alpha):
    """Split conformal, threshold = m-th order statistic, m=ceil((n+1)(1-a)).
    Under exchangeability + continuous scores, PIT makes calibration scores
    iid U(0,1), so coverage conditional on the calibration set equals the
    m-th uniform order statistic ~ Beta(m, n+1-m).
    Backing: Vovk (2012); Angelopoulos & Bates (2023), coverage-distribution
    proposition. This is the E2 reference law."""
    m = int(np.ceil((n_cal + 1) * (1 - alpha)))
    return m, sps.beta(m, n_cal + 1 - m)


def coverage_field_test(scores_pool, n_cal, alpha, R=1000, n_test=None, seed=0):
    """E2 core protocol (corrected): R random cal/test splits; per-split
    empirical coverage; (i) KS test of the R coverages against
    Beta(m, n+1-m); (ii) one-sided exact binomial on pooled rejections,
    H0: err <= alpha. Replicates share the pool, so KS is approximate; it is
    reported alongside the exact pooled binomial. A single-split CI check
    (the original spec) is NOT a validity test and is deliberately absent."""
    rng = np.random.default_rng(seed)
    s = np.asarray(scores_pool, float); N = len(s)
    n_test = n_test or min(500, N - n_cal)
    m, law = conformal_coverage_law(n_cal, alpha)
    covs = np.empty(R); rej = tot = 0
    for r in range(R):
        idx = rng.permutation(N)
        cal, test = s[idx[:n_cal]], s[idx[n_cal:n_cal + n_test]]
        tau = np.sort(cal)[m - 1]
        covs[r] = (test <= tau).mean()
        rej += int((test > tau).sum()); tot += n_test
    ks = sps.kstest(covs, law.cdf)
    binom = sps.binomtest(rej, tot, alpha, alternative="greater")
    return dict(mean_cov=float(covs.mean()), beta_mean=float(law.mean()),
                ks_p=float(ks.pvalue), pooled_err=rej / tot,
                binom_p=float(binom.pvalue))


def cochran_armitage(cases, totals, scores=None):
    """Trend in proportions across ordered groups. E4 primary endpoint:
    mean-form miss rate increases with length m (H1: slope > 0)."""
    r = np.asarray(cases, float); n = np.asarray(totals, float)
    s = np.asarray(scores if scores is not None else range(len(r)), float)
    N, Rr = n.sum(), r.sum(); pbar = Rr / N
    T = (s * r).sum(); E = pbar * (s * n).sum()
    V = pbar * (1 - pbar) * ((s ** 2 * n).sum() - (s * n).sum() ** 2 / N)
    z = (T - E) / np.sqrt(V)
    return float(z), float(2 * sps.norm.sf(abs(z)))


def loglog_slope(m_vals, deltas, n_boot=2000, seed=0):
    """E4 quantitative falsifier of Prop 3.6 (MMD dilution): OLS slope of
    log|delta f5_mean| on log m; pre-registered value -1 +/- 0.15."""
    x = np.log(np.asarray(m_vals, float)); y = np.log(np.asarray(deltas, float))
    fit = lambda xx, yy: np.linalg.lstsq(
        np.vstack([xx, np.ones_like(xx)]).T, yy, rcond=None)[0][0]
    slope = fit(x, y)
    rng = np.random.default_rng(seed); n = len(x); bs = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, n, n); bs[b] = fit(x[i], y[i])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return float(slope), float(lo), float(hi)


def cmin_from_audit(coverage, recall, target=0.90, conf_needed=0.95):
    """E3 frozen rule: c_min = smallest c s.t. the Clopper-Pearson LOWER bound
    of P(recall>=target | coverage>=c) is >= conf_needed. Feeds the fail-safe
    abstention floor of Prop 4.6 / Sec 4.5."""
    cov = np.asarray(coverage, float); rec = np.asarray(recall, float)
    for c in np.round(np.linspace(0.0, 0.95, 20), 3):
        mask = cov >= c
        if mask.sum() < 20:
            continue
        k = int((rec[mask] >= target).sum()); n = int(mask.sum())
        lo, _ = clopper_pearson(k, n)
        if lo >= conf_needed:
            return float(c), k, n
    return None, 0, 0
