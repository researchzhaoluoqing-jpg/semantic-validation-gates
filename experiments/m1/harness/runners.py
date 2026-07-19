"""
svg_experiments/runners.py -- Orchestration for E0-E4 exactly per ERS v1.0.
Mock mode = full integration test + power simulation; real mode = swap
MockNLI for HFNLI (and synthetic embeddings for sentence-transformers in E4).
"""
from __future__ import annotations
import numpy as np
from insertion import make_case
from detectors import (DETECTORS, score_sheaf, sheaf_localize)
import stats


# ------------------------------------------------------------------ E0

def run_e0_s1(nli, ks=range(0, 6), n_per=300):
    """Directly measure the S1 decay curve; report mean conf per k and the
    threshold-crossing point k* (first k with mean < 0.5)."""
    curve = {}
    for k in ks:
        confs = [nli.contradict_conf("u", "v", dist_hint=k)
                 for _ in range(n_per)]
        curve[k] = (float(np.mean(confs)), float(np.std(confs)))
    kstar = next((k for k, (m, _) in curve.items() if m < 0.5), None)
    return curve, kstar


def run_e0_s2(nli, n=300):
    """Directly measure the S2 hedged false-positive rate (w>=0.5)."""
    hits = sum(1 for _ in range(n)
               if (fp := nli.hedged_fp()) is not None and fp >= 0.5)
    lo, hi = stats.clopper_pearson(hits, n)
    return hits / n, (lo, hi)


# ------------------------------------------------------------------ E1

def run_e1(nli, cells, n_per=1000, seed=7):
    """cells: list of (vtype, k). Paired design: every case yields a clean
    and a violated score for every arm. Returns per-cell metrics and the
    frozen-rule verdict inputs (PE1 vs the BEST baseline, PE2 at k>=3)."""
    rng = np.random.default_rng(seed)
    out = {}
    for vtype, k in cells:
        scores = {a: {"pos": [], "neg": []}
                  for a in ["COUNT", "WSUM", "NLIMAX", "SAT", "SHEAF"]}
        loc_hits = loc_base = 0
        for _ in range(n_per):
            cp = make_case(vtype, k, nli, rng)
            for name, fn in DETECTORS.items():
                scores[name]["neg"].append(fn(cp.clean))
                scores[name]["pos"].append(fn(cp.violated))
            s_c, *_ = score_sheaf(cp.clean)
            s_v, x_star, aff = score_sheaf(cp.violated)
            scores["SHEAF"]["neg"].append(s_c)
            scores["SHEAF"]["pos"].append(s_v)
            if sheaf_localize(cp.violated, x_star, aff, cp.injected):
                loc_hits += 1
            # baseline 'localization': injected element above threshold
            if cp.injected[0] == "g":
                loc_base += cp.violated.g.edges[cp.injected[1]].w >= 0.5
        aur = {a: stats.auroc(scores[a]["pos"], scores[a]["neg"])
               for a in scores}
        best_bl = max((a for a in aur if a != "SHEAF"), key=aur.get)
        d, lo, hi, p = stats.paired_bootstrap_delta_auroc(
            scores["SHEAF"]["pos"], scores["SHEAF"]["neg"],
            scores[best_bl]["pos"], scores[best_bl]["neg"],
            n_boot=2000, seed=seed)
        out[(vtype, k)] = dict(auroc=aur, best_baseline=best_bl,
                               delta=(d, lo, hi, p),
                               loc_sheaf=loc_hits / n_per,
                               loc_base=loc_base / n_per)
    return out


def e1_verdict(results, dA=0.03, dLoc=0.10):
    """Frozen green/yellow/red rules from ERS. Green requires the headline
    win AND a WSUM-specific win on V3 or V4 (anti-artifact clause)."""
    deltas = [r["delta"] for r in results.values()]
    pe1 = any(d >= dA and lo > 0 for d, lo, hi, p in deltas)
    pe2 = any(r["loc_sheaf"] - r["loc_base"] >= dLoc
              for (vt, k), r in results.items() if k >= 3)
    wsum_clause = any(r["auroc"]["SHEAF"] - r["auroc"]["WSUM"] >= dA
                      for (vt, _), r in results.items() if vt in ("V3", "V4"))
    if (pe1 or pe2) and wsum_clause:
        return "GREEN"
    if pe1 or pe2:
        return "YELLOW (beats thresholded baselines only)"
    return "RED (pivot to architecture paper)"


# ------------------------------------------------------------------ E2

def run_e2(valid_scores, n_cal=200, alpha=0.10, R=500, seed=0):
    return stats.coverage_field_test(valid_scores, n_cal, alpha, R=R,
                                     seed=seed)


# ------------------------------------------------------------------ E3

def match_claims(gold, extracted, nli, thr=0.9):
    """Bidirectional-entailment matching protocol; returns claim recall.
    (Real mode: nli entailment both directions >= thr; borderline 100 items
    to human adjudication per ERS.)"""
    hit = sum(1 for g in gold if any(
        nli.entail_conf(g, e) >= thr and nli.entail_conf(e, g) >= thr
        for e in extracted))
    return hit / max(1, len(gold))


# ------------------------------------------------------------------ E4

def run_e4(ms=(5, 10, 20, 40, 80), n_per=300, delta=1.2, alpha=0.05,
           dim=64, seed=0):
    """Mock-embedding instantiation of Props 3.6/3.7. Reference set ~ N(mu,
    0.1 I); clean unit ~ same; violated text flips ONE unit to distance
    ~delta. Arms: mean-form (||mean(units) - mean(ref)||) vs max-form
    (directed Hausdorff). Thresholds: split conformal at alpha on clean.
    Real mode: swap in sentence-transformer embeddings of IFEval outputs."""
    rng = np.random.default_rng(seed)
    mu = rng.normal(0, 1, dim); mu /= np.linalg.norm(mu)
    ref = mu + 0.1 * rng.normal(0, 1, (50, dim))

    def sample_units(m, violate):
        U = mu + 0.1 * rng.normal(0, 1, (m, dim))
        if violate:
            d = rng.normal(0, 1, dim); d /= np.linalg.norm(d)
            U[rng.integers(0, m)] = mu + delta * d
        return U

    def f_mean(U):
        return float(np.linalg.norm(U.mean(0) - ref.mean(0)))

    def f_max(U):
        return float(max(np.linalg.norm(ref - u, axis=1).min() for u in U))

    miss = {"mean": [], "max": []}; shift_mean = []
    for m in ms:
        clean_scores = {"mean": [], "max": []}
        for _ in range(n_per):
            U = sample_units(m, False)
            clean_scores["mean"].append(f_mean(U))
            clean_scores["max"].append(f_max(U))
        thr = {a: np.quantile(clean_scores[a],
                              1 - alpha, method="higher")
               for a in clean_scores}
        misses = {"mean": 0, "max": 0}; sh = []
        for _ in range(n_per):
            U = sample_units(m, False)          # matched-pair construction:
            Uv = U.copy()                       # same base, flip ONE unit
            dvec = rng.normal(0, 1, dim); dvec /= np.linalg.norm(dvec)
            Uv[rng.integers(0, m)] = mu + delta * dvec
            if f_mean(Uv) <= thr["mean"]:
                misses["mean"] += 1
            if f_max(Uv) <= thr["max"]:
                misses["max"] += 1
            # F2 (smoke finding): shift MUST be measured on matched pairs;
            # independent clean/violated sampling injects O(m^-1/2) noise
            # that contaminates the dilution exponent (-0.53 observed vs
            # -1 true). Matched pairs isolate the pure 1/m signal.
            sh.append(abs(f_mean(Uv) - f_mean(U)))
        for a in misses:
            miss[a].append(misses[a] / n_per)
        shift_mean.append(np.mean(sh))
    z, p = stats.cochran_armitage([int(r * n_per) for r in miss["mean"]],
                                  [n_per] * len(ms), scores=list(ms))
    slope, lo, hi = stats.loglog_slope(ms, shift_mean)
    return dict(ms=list(ms), miss=miss, trend_z=z, trend_p=p,
                slope=(slope, lo, hi))
