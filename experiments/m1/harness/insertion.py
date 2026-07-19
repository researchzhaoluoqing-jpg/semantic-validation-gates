"""
svg_experiments/insertion.py -- Violation generators V1-V4 (ERS E1).

Scientific backing per type:
  V1/V2: transitive contradiction at step distance k; direct-edge confidence
         follows the S1 law (measured in E0). Tests threshold collapse vs
         graceful degradation.
  V3:    COMPOSITIONAL inconsistency -- numeric chain x_{i+1}=alpha_i x_i with
         a closing claim x_last = c * x_0, c != prod(alpha). Every PAIR of
         equations is jointly satisfiable, so pairwise NLI emits NO
         contradiction edge: COUNT/WSUM/NLImax are blind BY CONSTRUCTION.
         The sheaf detects it because affine restriction maps (stalks =
         log-values, edge residual x_u + delta_e - x_v) make the cycle
         energy strictly positive -- this is exactly <x, L_F(w) x> with
         affine restriction data (paper Sec 3.3), solved in closed form as
         weighted least squares. Clean V3 twins carry extraction noise
         (delta ~ N(0, sigma_extract)) so the negative class is realistic.
  V4:    hedged contamination -- clean class with a forced hypothetical
         clause that NLI flags as contradicting an asserted claim (S2).
         Only assertion-aware methods (sheaf: free node reconciled by the
         global minimization) discount it; WSUM/COUNT tally it as signal.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from f3_reference import ClaimGraph, Edge

NEG_TEMPLATES = ["Therefore, it is not the case that {c}.",
                 "However, {c} must be false.",
                 "This shows {c} does not hold."]


@dataclass
class View:
    g: ClaimGraph                      # pairwise NLI graph (all baselines)
    aff_nodes: list | None = None      # numeric view (V3): node names
    aff_edges: list | None = None      # (u, v, delta, w)


@dataclass
class CasePair:
    clean: View
    violated: View
    vtype: str
    k: int
    injected: tuple | None             # ('g', edge_idx) or ('aff', edge_idx)


# ------------------------------------------------------------------ helpers

def _chain(n, nli, rng):
    g = ClaimGraph(claims=[f"step_{i}" for i in range(n)],
                   asserted=set(range(n)))
    for i in range(n - 1):
        g.add_edge(i, i + 1, "entail",
                   w=nli.entail_conf(g.claims[i], g.claims[i + 1], 1))
    return g


def _clone(g):
    return ClaimGraph(list(g.claims),
                      [Edge(e.u, e.v, e.rel, e.w) for e in g.edges],
                      set(g.asserted))


def _noise(g, nli, rng, force_hedge=False):
    """S2 contamination, injected into BOTH classes (fair-noise principle)."""
    fp = nli.hedged_fp(force=force_hedge)
    if fp is not None:
        h = g.n
        g.claims.append("hedged_hypothetical")     # asserted stays False
        g.add_edge(h, int(rng.integers(0, min(6, g.n))), "contradict", w=fp)
    if rng.random() < 0.30:                        # spurious sub-threshold
        u, v = rng.choice(min(6, g.n), size=2, replace=False)
        g.add_edge(int(u), int(v), "contradict",
                   w=float(rng.uniform(0.10, 0.45)))


# --------------------------------------------------------------- generators

def make_v12(n_chain, k, nli, rng, force_hedge=False):
    """V1 (k=1) / V2 (k>=2). Ground-truth injected edge index recorded for
    the localization endpoint PE2."""
    base = _chain(n_chain, nli, rng)
    clean = _clone(base); _noise(clean, nli, rng, force_hedge)
    vio = _clone(base);   _noise(vio, nli, rng, force_hedge)
    i = int(rng.integers(0, max(1, n_chain - k)))
    v = vio.n
    vio.claims.append(NEG_TEMPLATES[int(rng.integers(0, 3))]
                      .format(c=vio.claims[i]))
    vio.asserted.add(v)
    vio.add_edge(v, i, "contradict",
                 w=nli.contradict_conf(vio.claims[v], vio.claims[i],
                                       dist_hint=k))
    inj = len(vio.edges) - 1
    if k >= 2 and rng.random() < 0.6:              # weak paraphrase pickup
        vio.add_edge(v, min(i + 1, n_chain - 1), "contradict",
                     w=float(np.clip(0.6 * vio.edges[inj].w, 0.02, 0.99)))
    return CasePair(View(clean), View(vio),
                    "V1" if k == 1 else "V2", k, ("g", inj))


def make_v3(n_chain, nli, rng, sigma_extract=0.02):
    """Compositional numeric inconsistency; pairwise detectors blind.
    BUGFIX (smoke finding F3): the closing claim asserts a DIRECT relation
    between x_0 and x_{n-1}, i.e. an edge that CLOSES the chain into a
    fundamental cycle -- not a dangling new node (which creates no cycle and
    hence no H^1 obstruction to detect)."""
    def build(consistent: bool):
        g = ClaimGraph(claims=[f"x{i}" for i in range(n_chain)]
                       + ["closing"], asserted=set(range(n_chain + 1)))
        _noise(g, nli, rng)                        # same noise field
        nodes = list(range(n_chain))
        aedges, total = [], 0.0
        for i in range(n_chain - 1):
            d = float(rng.uniform(0.3, 1.2))       # log alpha_i
            total += d
            aedges.append((i, i + 1, d, nli.entail_conf("", "", 1)))
        gap = (rng.normal(0, sigma_extract) if consistent
               else float(rng.choice([-1, 1]) * rng.uniform(0.4, 0.9)))
        aedges.append((0, n_chain - 1, total + gap,
                       nli.entail_conf("", "", 1)))
        return View(g, nodes, aedges)

    clean, vio = build(True), build(False)
    return CasePair(clean, vio, "V3", 0, ("aff", len(vio.aff_edges) - 1))


# dataclass lacks a field-replace helper for vtype
def _retype(cp: CasePair, t: str) -> CasePair:
    return CasePair(cp.clean, cp.violated, t, cp.k, cp.injected)


def make_case(vtype, k, nli, rng, n_chain=6):
    if vtype in ("V1", "V2"):
        return make_v12(n_chain, k, nli, rng)
    if vtype == "V3":
        return make_v3(n_chain, nli, rng)
    if vtype == "V4":
        return _retype(make_v12(n_chain, 1, nli, rng, force_hedge=True), "V4")
    raise ValueError(vtype)
