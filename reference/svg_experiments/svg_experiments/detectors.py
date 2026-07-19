"""
svg_experiments/detectors.py -- The five arms of E1 (ERS), unified interface.

COUNT  : #{contradict edges, w>=0.5}          (standard production baseline)
WSUM   : sum of contradict-edge confidences   (the DANGEROUS baseline: also
         accumulates sub-threshold evidence; added so a sheaf win cannot be
         dismissed as a de-thresholding artifact)
NLIMAX : max contradict-edge confidence
SHEAF  : unified energy = sqrt( f3_unified(g)^2 + affine_energy^2 ).
         The affine term is <x, L_F(w) x> with affine restriction maps
         (stalks = log-values), minimized in CLOSED FORM as weighted least
         squares -- the numeric instantiation of paper Sec 3.3.
SAT    : hard layer on thresholded edges; for numeric views, exact closure
         (residual of the hard-edge least squares > tol).
Localization: top weighted-residual element ('where the obstruction lives').
"""
from __future__ import annotations
import numpy as np
from f3_reference import ClaimGraph, Edge, f3_unified, localize, certify
from insertion import View

PGD = dict(iters=400, lr=0.1)


# --------------------------------------------------------------- baselines

def score_count(v: View) -> float:
    return float(sum(1 for e in v.g.edges
                     if e.rel == "contradict" and e.w >= 0.5))


def score_wsum(v: View) -> float:
    return float(sum(e.w for e in v.g.edges if e.rel == "contradict"))


def score_nlimax(v: View) -> float:
    ws = [e.w for e in v.g.edges if e.rel == "contradict"]
    return float(max(ws)) if ws else 0.0


# ------------------------------------------------------- affine sheaf term

def affine_energy(nodes, aedges):
    """Cycle-holonomy statistic: the H^1 obstruction evaluated on fundamental
    cycles. Build a spanning tree, propagate potentials x_v = x_u + delta
    along tree edges; every non-tree edge e closes a fundamental cycle with
    holonomy h_e = |x_u + delta_e - x_v| (= the signed delta-sum around the
    cycle). Score = sqrt(sum_e conf_e * h_e^2), conf_e = w_e * min tree-edge
    weight on the cycle (soft closure). SCIENTIFIC NOTE: the naive
    least-squares residual spreads the gap over all L cycle edges (energy
    ~ gap^2/L, per-edge ~ (gap/L)^2) -- diluted and unlocalizable; the
    holonomy is length-invariant and localizes at the closing edge. This is
    finding F1 of the smoke study and feeds paper Sec 3.3.
    Returns (score, per-aedge residuals aligned to aedges order)."""
    if not aedges:
        return 0.0, []
    n = len(nodes)
    parent = {0: (None, None, None)}      # v -> (u, delta, w) via tree edge
    x = {0: 0.0}
    tree_edges, extra = [], []
    for idx, (u, v, d, w) in enumerate(aedges):
        if v not in x and u in x:
            x[v] = x[u] + d; parent[v] = (u, d, w); tree_edges.append(idx)
        elif u not in x and v in x:
            x[u] = x[v] - d; parent[u] = (v, -d, w); tree_edges.append(idx)
        else:
            extra.append(idx)
    for i in range(n):                    # disconnected safety
        x.setdefault(i, 0.0)

    def min_w_path(a, b):
        seen = {}
        node = a
        while node is not None:
            seen[node] = True
            node = parent.get(node, (None,))[0]
        node, mw = b, 1.0
        while node not in seen and node is not None:
            pu = parent.get(node, (None, None, None))
            mw = min(mw, pu[2] if pu[2] is not None else 1.0)
            node = pu[0]
        return mw

    res = [0.0] * len(aedges)
    for idx in extra:
        u, v, d, w = aedges[idx]
        h = x[u] + d - x[v]
        conf = w * min_w_path(u, v)
        res[idx] = conf * h * h
    return float(np.sqrt(sum(res))), res


# ------------------------------------------------------------------- sheaf

def score_sheaf(v: View):
    """Returns (score, x_star, aff_res) -- x_star/aff_res feed localization."""
    e_pair, x_star = f3_unified(v.g, **PGD)
    e_aff, res = (affine_energy(v.aff_nodes, v.aff_edges)
                  if v.aff_edges else (0.0, []))
    return float(np.sqrt(e_pair ** 2 + e_aff ** 2)), x_star, res


def sheaf_localize(v: View, x_star, aff_res, injected):
    """Top-1 hotspot across BOTH views hits the injected element?"""
    best_g = None
    hs = localize(v.g, x_star, top_k=1)
    g_val = hs[0][1] if hs else -1.0
    if hs:
        best_g = v.g.edges.index(hs[0][0])
    a_val = max(aff_res) if aff_res else -1.0
    a_idx = int(np.argmax(aff_res)) if aff_res else None
    if injected[0] == "g":
        return g_val >= a_val and best_g == injected[1]
    return a_val >= g_val and a_idx == injected[1]


# --------------------------------------------------------------------- SAT

def score_sat(v: View) -> float:
    hard = [e for e in v.g.edges if e.w >= 0.5]
    gt = ClaimGraph(list(v.g.claims),
                    [Edge(e.u, e.v, e.rel, e.w) for e in hard],
                    set(v.g.asserted))
    pair_unsat = 0.0 if certify(gt)["sat"] else 1.0
    aff_unsat = 0.0
    if v.aff_edges:
        hard_a = [(u, vv, d, 1.0) for (u, vv, d, w) in v.aff_edges if w >= 0.5]
        e, _ = affine_energy(v.aff_nodes, hard_a)
        aff_unsat = 1.0 if e > 0.1 else 0.0
    return max(pair_unsat, aff_unsat)


DETECTORS = {"COUNT": score_count, "WSUM": score_wsum,
             "NLIMAX": score_nlimax, "SAT": score_sat}
