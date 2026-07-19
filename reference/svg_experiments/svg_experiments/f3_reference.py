"""
f3 Logic Gate — Reference Implementation (v3, §3.3)
====================================================
Weighted cellular sheaf Laplacian on a claim graph, unified relaxed logic
energy over the constraint polytope, and a SAT certifier (relax-and-certify).

Dependencies: numpy only (a tiny DPLL solver is included; no external SAT lib).

Model
-----
- Vertices  : atomic claims, stalk F(v) = R (truth value in [0,1]).
- Edges     : detected logical relations with calibrated NLI confidence w_e:
                * 'entail'     u => v   : soft residual  r_e(x) = max(0, x_u - x_v)
                                          hard clause    (¬u ∨ v)
                * 'equiv'      u <=> v  : soft residual  r_e(x) = x_u - x_v
                                          hard clauses   (¬u ∨ v), (¬v ∨ u)
                * 'contradict' ¬(u ∧ v) : soft residual  r_e(x) = x_u + x_v - 1 (clipped at 0)
                                          hard clause    (¬u ∨ ¬v)
- Asserted claims are clamped to truth 1 (the text asserts them).
- Weighted energy:  E(x) = sum_e w_e * r_e(x)^2  = <r(x), W r(x)>
  For 'equiv' edges this is exactly the coboundary quadratic form
  <x, L_F(w) x> with L_F(w) = δᵀWδ; entail/contradict edges use the affine /
  one-sided extension described in the paper (Amendment B.1).

Scores
------
- f3_asserted : sqrt(E(x_asserted))            — Prop A.2 applies (Lipschitz in w)
- f3_unified  : sqrt(min_{x in X} E(x))        — free (non-asserted) variables are
                relaxed over [0,1]; asserted variables clamped.  (Def. B.1)
- certify()   : DPLL on the hard clauses; if UNSAT, greedy deletion-minimal
                unsatisfiable core returned as exact severity.  (§B.2)
"""

from __future__ import annotations
import itertools
import numpy as np
from dataclasses import dataclass, field


# ----------------------------------------------------------------------------
# Claim graph
# ----------------------------------------------------------------------------

@dataclass
class Edge:
    u: int
    v: int
    rel: str        # 'entail' | 'equiv' | 'contradict'
    w: float = 1.0  # calibrated NLI confidence in [0, 1]


@dataclass
class ClaimGraph:
    claims: list[str]
    edges: list[Edge] = field(default_factory=list)
    asserted: set[int] = field(default_factory=set)  # indices clamped to truth 1

    def add_edge(self, u: int, v: int, rel: str, w: float = 1.0) -> None:
        assert rel in ("entail", "equiv", "contradict")
        assert 0.0 <= w <= 1.0
        self.edges.append(Edge(u, v, rel, w))

    @property
    def n(self) -> int:
        return len(self.claims)


# ----------------------------------------------------------------------------
# Soft layer: weighted sheaf energy
# ----------------------------------------------------------------------------

def edge_residuals(g: ClaimGraph, x: np.ndarray) -> np.ndarray:
    """Per-edge residuals r_e(x) (before weighting)."""
    r = np.zeros(len(g.edges))
    for i, e in enumerate(g.edges):
        if e.rel == "equiv":
            r[i] = x[e.u] - x[e.v]
        elif e.rel == "entail":            # violated iff x_u > x_v
            r[i] = max(0.0, x[e.u] - x[e.v])
        elif e.rel == "contradict":        # violated iff x_u + x_v > 1
            r[i] = max(0.0, x[e.u] + x[e.v] - 1.0)
    return r


def sheaf_energy(g: ClaimGraph, x: np.ndarray) -> float:
    """E(x) = sum_e w_e r_e(x)^2  (== <x, L_F(w) x> on the equiv sub-sheaf)."""
    r = edge_residuals(g, x)
    w = np.array([e.w for e in g.edges])
    return float(np.dot(w * r, r))


def f3_asserted(g: ClaimGraph) -> float:
    """Score of the raw asserted assignment (all asserted claims at truth 1,
    non-asserted claims initialized at their energy-minimizing free values —
    here simply included in the minimization of f3_unified; for the pure
    asserted score we set free variables to 0.5 (maximal ignorance)."""
    x = np.full(g.n, 0.5)
    for i in g.asserted:
        x[i] = 1.0
    return float(np.sqrt(sheaf_energy(g, x)))


def f3_unified(g: ClaimGraph, iters: int = 4000, lr: float = 0.05,
               seed: int = 0) -> tuple[float, np.ndarray]:
    """min_{x in [0,1]^V, x clamped on asserted} sqrt(E(x))
    via projected gradient descent (the objective is a convex piecewise
    quadratic, so PGD converges to the global minimum)."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.3, 0.7, g.n)
    for i in g.asserted:
        x[i] = 1.0
    w = np.array([e.w for e in g.edges])
    for _ in range(iters):
        grad = np.zeros(g.n)
        for k, e in enumerate(g.edges):
            if e.rel == "equiv":
                d = x[e.u] - x[e.v]
                grad[e.u] += 2 * w[k] * d
                grad[e.v] -= 2 * w[k] * d
            elif e.rel == "entail":
                d = x[e.u] - x[e.v]
                if d > 0:
                    grad[e.u] += 2 * w[k] * d
                    grad[e.v] -= 2 * w[k] * d
            elif e.rel == "contradict":
                d = x[e.u] + x[e.v] - 1.0
                if d > 0:
                    grad[e.u] += 2 * w[k] * d
                    grad[e.v] += 2 * w[k] * d
        x -= lr * grad
        np.clip(x, 0.0, 1.0, out=x)
        for i in g.asserted:               # clamp asserted claims
            x[i] = 1.0
    return float(np.sqrt(sheaf_energy(g, x))), x


def localize(g: ClaimGraph, x: np.ndarray, top_k: int = 3) -> list[tuple[Edge, float]]:
    """Edges carrying the largest weighted residual energy — the computable
    analogue of 'where the obstruction lives'."""
    r = edge_residuals(g, x)
    contrib = [(e, float(e.w * r[i] ** 2)) for i, e in enumerate(g.edges)]
    contrib.sort(key=lambda t: -t[1])
    return contrib[:top_k]


# ----------------------------------------------------------------------------
# Hard layer: clauses + tiny DPLL + greedy MUS  (certifier, §B.2)
# ----------------------------------------------------------------------------

def to_clauses(g: ClaimGraph) -> list[tuple[frozenset, str]]:
    """Literals are ints: +i / -(i) encoded as (i, True/False). Each clause is
    (frozenset of (var, polarity)), tagged with provenance for MUS reporting."""
    cls = []
    for e in g.edges:
        if e.rel == "entail":
            cls.append((frozenset({(e.u, False), (e.v, True)}),
                        f"entail({e.u}->{e.v})"))
        elif e.rel == "equiv":
            cls.append((frozenset({(e.u, False), (e.v, True)}),
                        f"equiv({e.u}->{e.v})"))
            cls.append((frozenset({(e.v, False), (e.u, True)}),
                        f"equiv({e.v}->{e.u})"))
        elif e.rel == "contradict":
            cls.append((frozenset({(e.u, False), (e.v, False)}),
                        f"contradict({e.u},{e.v})"))
    for i in sorted(g.asserted):
        cls.append((frozenset({(i, True)}), f"asserted({i})"))
    return cls


def dpll(clauses: list[frozenset], assignment: dict | None = None) -> bool:
    """Plain DPLL with unit propagation. Returns satisfiability."""
    assignment = dict(assignment or {})
    clauses = [set(c) for c in clauses]
    while True:
        simplified, unit = [], None
        for c in clauses:
            vals = {(var, pol) for (var, pol) in c}
            if any(assignment.get(var) == pol for var, pol in vals):
                continue                                # clause satisfied
            rem = {(var, pol) for var, pol in vals if var not in assignment}
            if not rem:
                return False                            # clause falsified
            if len(rem) == 1 and unit is None:
                unit = next(iter(rem))
            simplified.append(rem)
        clauses = [frozenset(c) for c in simplified]
        if not clauses:
            return True
        if unit is None:
            break
        assignment[unit[0]] = unit[1]
    var = next(iter(next(iter(clauses))))[0]            # branch
    for pol in (True, False):
        if dpll(clauses, {**assignment, var: pol}):
            return True
    return False


def certify(g: ClaimGraph) -> dict:
    """Returns {'sat': bool, 'mus': [...] or None}. MUS by greedy deletion:
    deletion-minimal unsatisfiable subset (exact severity, §B.2)."""
    tagged = to_clauses(g)
    clauses = [c for c, _ in tagged]
    if dpll(clauses):
        return {"sat": True, "mus": None}
    core = list(range(len(tagged)))
    for i in list(core):
        trial = [tagged[j][0] for j in core if j != i]
        if not dpll(trial):
            core.remove(i)
    return {"sat": False, "mus": [tagged[i][1] for i in core]}


# ----------------------------------------------------------------------------
# Gate wrapper: relax-and-certify
# ----------------------------------------------------------------------------

def f3_gate(g: ClaimGraph, tau: float) -> dict:
    score, x_star = f3_unified(g)
    out = {"f3_unified": score, "rho3": score / tau,
           "hotspots": [(f"{g.claims[e.u]!r} vs {g.claims[e.v]!r} [{e.rel}]",
                         round(c, 4)) for e, c in localize(g, x_star)] ,
           "certified": None, "mus": None}
    # Relax-and-certify (§B.2): certify the relaxed optimum. On claim graphs
    # (small |V|) we always run the certifier; if UNSAT, the deletion-minimal
    # core is the exact severity, and it closes any relaxation gap when the
    # continuous score alone would have passed.
    cert = certify(g)
    out["certified"] = cert["sat"]
    out["mus"] = cert["mus"]
    if not cert["sat"]:
        out["rho3"] = max(out["rho3"], 1.0 + 1e-9)
    out["pass"] = out["rho3"] <= 1.0
    return out


# ----------------------------------------------------------------------------
# Demo / self-test
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    TAU = 0.30   # in deployment: conformal quantile (Thm 4.1 of the paper)

    print("=" * 72)
    print("Case 1: consistent chain  (A => B => C, all asserted)")
    g1 = ClaimGraph(claims=["A", "B", "C"], asserted={0, 1, 2})
    g1.add_edge(0, 1, "entail", w=0.95)
    g1.add_edge(1, 2, "entail", w=0.90)
    print(f3_gate(g1, TAU))

    print("=" * 72)
    print("Case 2: inserted contradiction  (A => B, but text also asserts D "
          "with contradict(B, D))")
    g2 = ClaimGraph(claims=["A", "B", "D"], asserted={0, 1, 2})
    g2.add_edge(0, 1, "entail", w=0.95)
    g2.add_edge(1, 2, "contradict", w=0.90)
    res2 = f3_gate(g2, TAU)
    print(res2)
    assert not res2["pass"] and res2["hotspots"][0][1] > 0

    print("=" * 72)
    print("Case 3: hidden Boolean inconsistency with near-zero relaxed energy")
    # cycle: A entails B, B entails C, C contradicts A; A asserted only.
    # Free relaxation can hide it partially -> certifier must catch it.
    g3 = ClaimGraph(claims=["A", "B", "C"], asserted={0})
    g3.add_edge(0, 1, "entail", w=0.9)
    g3.add_edge(1, 2, "entail", w=0.9)
    g3.add_edge(2, 0, "contradict", w=0.9)
    res3 = f3_gate(g3, TAU)
    print(res3)
    assert res3["certified"] is False and res3["mus"], "certifier must fire"
    assert not res3["pass"]

    print("=" * 72)
    print("Case 4: Prop A.2 sanity — Lipschitz in edge weights")
    base = f3_asserted(g2) ** 2
    for eps in (0.05, 0.10, 0.20):
        g2p = ClaimGraph(g2.claims, [Edge(e.u, e.v, e.rel, max(0, e.w - eps))
                                     for e in g2.edges], set(g2.asserted))
        pert = f3_asserted(g2p) ** 2
        bound = 4 * 1.0 * (eps * len(g2.edges))   # 4R^2 ||w - w'||_1, R=1... x in [0,1]
        print(f"  ||w-w'||_1={eps*len(g2.edges):.2f}  |ΔE|={abs(base-pert):.4f}"
              f"  bound={bound:.2f}  ok={abs(base-pert) <= bound}")
        assert abs(base - pert) <= bound

    print("=" * 72)
    print("All self-tests passed.")
