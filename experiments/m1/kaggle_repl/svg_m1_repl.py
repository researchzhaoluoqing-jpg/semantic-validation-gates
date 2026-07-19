# %% [markdown]
# # M1 Replication B (second instrument) — Sheaf Energy vs. Contradiction Counting under a Real NLI
#
# Field instantiation of the mechanism study (§6) and pre-registered ablation (b)
# of *Semantic Validation Gates* (v3.1). The simulation harness (Kaggle dataset
# `svg-harness`) is reused verbatim — per §6, "the harness used here becomes the
# real experiment by replacing simulated confidences with model outputs."
#
# **Instrument** (frozen before any E1 case is scored; Prop. 4.1):
# DeBERTa-large-MNLI, temperature-scaled on MNLI validation-matched (Guo et al.
# 2017), ECE reported pre/post. The instrument never sees ground-truth distance.
#
# **Materials**: GSM8K training-split gold solutions → claim chains (4–8 steps)
# with the dataset's own `<<a op b = c>>` calculator annotations as the numeric
# extraction channel.
#
# **Cells** (paired clean/violated design): V1 (direct negation, k=1),
# V2 (negation at step distance k ∈ {2,3,4,5}), V3 (compositional numeric
# closing-claim violation; pairwise-blind by construction), V4 (hedged
# contamination, S2). Arms: COUNT / WSUM / NLIMAX / SAT / SHEAF.
#
# **Endpoints & decision rule**: pre-registered PE1 (paired-bootstrap ΔAUROC vs
# best baseline, Holm-adjusted), PE2 (top-1 localization gap at k ≥ 3), WSUM
# anti-artifact clause; frozen GREEN/YELLOW/RED verdict via `e1_verdict`.
# E0 measures S1/S2 in the field; E2 field-tests Theorem 4.2's coverage law.

# %%
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "datasets"], check=True)

# %%
import os, re, json, math, itertools, sys
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import glob as _glob
_hits = _glob.glob("/kaggle/input/**/f3_reference.py", recursive=True)
if _hits:
    sys.path.insert(0, os.path.dirname(_hits[0]))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath("__file__")),
                                    "..", "harness"))
print("harness path:", sys.path[0],
      "| /kaggle/input contents:", os.listdir("/kaggle/input")
      if os.path.isdir("/kaggle/input") else "n/a")

from f3_reference import ClaimGraph, Edge, f3_unified
from insertion import View, CasePair
from detectors import (DETECTORS, PGD, affine_energy, score_sheaf,
                       sheaf_localize)
from runners import e1_verdict, run_e2
import stats as svgstats

SEED = 20260719
rng = np.random.default_rng(SEED)
torch.manual_seed(SEED)

QUICK = os.environ.get("QUICK", "0") == "1"  # default flips per push: smoke vs full
NLI_MODEL = "FacebookAI/roberta-large-mnli"  # Replication B: architecture-distinct instrument
N_CAL_MNLI = 400 if QUICK else 2000
N_CHAINS = 140 if QUICK else 600
N_PER_CELL = 20 if QUICK else 300
N_BOOT = 500 if QUICK else 4000
CELLS = [("V1", 1), ("V3", 0), ("V4", 1)]  # Replication B: key cells only
CONTRA_KEEP = 0.05        # soft-evidence floor for contradiction edges
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OUT = "/kaggle/working/results" if os.path.isdir("/kaggle/working") else "./results"
os.makedirs(f"{OUT}/plots", exist_ok=True)
print(f"device={DEVICE} quick={QUICK} chains={N_CHAINS} n/cell={N_PER_CELL}")
if DEVICE == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))

# %% [markdown]
# ## 1. Instrument: calibrated NLI (frozen)

# %%
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from nli_wrapper import TemperatureScaler, ece

tok = AutoTokenizer.from_pretrained(NLI_MODEL)
# fp32: DeBERTa-v1 disentangled attention is fp16-incompatible (Float/Half mix)
nli_model = (AutoModelForSequenceClassification.from_pretrained(
    NLI_MODEL, torch_dtype=torch.float32, use_safetensors=False)
    .to(DEVICE).eval())
id2label = {int(k): v.upper() for k, v in nli_model.config.id2label.items()}
IDX = {v: k for k, v in id2label.items()}
CONTRA_IDX, ENTAIL_IDX = IDX["CONTRADICTION"], IDX["ENTAILMENT"]
print("label map:", id2label)

@torch.no_grad()
def nli_logits(pairs, batch=64):
    out = []
    for i in range(0, len(pairs), batch):
        chunk = pairs[i:i+batch]
        enc = tok([p for p, h in chunk], [h for p, h in chunk],
                  return_tensors="pt", padding=True, truncation=True,
                  max_length=256).to(DEVICE)
        out.append(nli_model(**enc).logits.float().cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, 3))

# --- temperature calibration on MNLI validation-matched, then FROZEN ---------
from datasets import load_dataset
mnli = (load_dataset("nyu-mll/glue", "mnli", split="validation_matched")
        .shuffle(seed=SEED).select(range(N_CAL_MNLI)))
# GLUE mnli labels: 0=entailment, 1=neutral, 2=contradiction -> map to model order
glue2model = {0: ENTAIL_IDX, 1: IDX["NEUTRAL"], 2: CONTRA_IDX}
cal_logits = nli_logits(list(zip(mnli["premise"], mnli["hypothesis"])))
cal_labels = np.array([glue2model[l] for l in mnli["label"]])
scaler = TemperatureScaler().fit(cal_logits, cal_labels)
def softmax(z):
    z = z - z.max(-1, keepdims=True); p = np.exp(z)
    return p / p.sum(-1, keepdims=True)
ece_pre = ece(softmax(cal_logits), cal_labels)
ece_post = ece(scaler.prob(cal_logits), cal_labels)
acc_cal = float((cal_logits.argmax(1) == cal_labels).mean())
print(f"T={scaler.T:.3f}  ECE pre={ece_pre:.4f} post={ece_post:.4f}  acc={acc_cal:.3f}")

# --- cached pair scorer -------------------------------------------------------
_cache = {}
def score_pairs(pairs):
    """Calibrated (p_contra, p_entail) per ordered pair, cached."""
    todo = [p for p in pairs if p not in _cache]
    if todo:
        probs = scaler.prob(nli_logits(todo))
        for p, pr in zip(todo, probs):
            _cache[p] = (float(pr[CONTRA_IDX]), float(pr[ENTAIL_IDX]))
    return [_cache[p] for p in pairs]

def contra_sym(u, v):
    (c1, _), (c2, _) = score_pairs([(u, v), (v, u)])
    return max(c1, c2)

def entail_dir(u, v):
    return score_pairs([(u, v)])[0][1]

# %% [markdown]
# ## 2. Materials: GSM8K claim chains + numeric annotations

# %%
gsm = load_dataset("openai/gsm8k", "main", split="train").shuffle(seed=SEED)

EQ_RE = re.compile(r"<<([^<>=]+)=([-\d.,/]+)>>")

def parse_item(rec):
    body = rec["answer"].split("####")[0].strip()
    raw_steps = [s.strip() for s in body.split("\n") if len(s.strip()) > 10]
    steps, eqvals = [], []
    for s in raw_steps:
        vals = []
        for m in EQ_RE.finditer(s):
            try:
                vals.append(float(m.group(2).replace(",", "").rstrip(".")))
            except ValueError:
                pass
        steps.append(EQ_RE.sub("", s).replace("  ", " ").strip())
        eqvals.append(vals[-1] if vals else None)
    return steps, eqvals

chains = []
for rec in gsm:
    steps, eqvals = parse_item(rec)
    if 4 <= len(steps) <= 10 and all(len(s) > 10 for s in steps):
        chains.append(dict(steps=steps, eqvals=eqvals))
    if len(chains) >= N_CHAINS:
        break
print(f"{len(chains)} chains; step-count dist:",
      np.bincount([len(c['steps']) for c in chains])[4:])

NEG_TEMPLATES = ["However, it is not the case that {c}",
                 "Actually, the following is false: {c}",
                 "This shows that it is wrong to say {c}",
                 "On reflection, the claim that {c} cannot be right",
                 "Contrary to the above, it is untrue that {c}",
                 "We must conclude that the statement '{c}' does not hold"]
HEDGE_TEMPLATE = ("Suppose, hypothetically, that it were not true that {c} — "
                  "but as computed above, that cannot be the case.")

def neg_text(claim):
    c = claim[0].lower() + claim[1:].rstrip(".")
    return NEG_TEMPLATES[int(rng.integers(len(NEG_TEMPLATES)))].format(c=c) + "."

# %% [markdown]
# ## 3. Field graph builder (per-chain NLI cache) and case generators

# %%
def build_graph(texts, asserted_flags):
    g = ClaimGraph(claims=list(texts),
                   asserted={i for i, a in enumerate(asserted_flags) if a})
    n = len(texts)
    ent_pairs = [(texts[i], texts[i+1]) for i in range(n - 1)]
    for i, (_, pe) in enumerate(score_pairs(ent_pairs)):
        g.add_edge(i, i + 1, "entail", w=max(pe, 0.02))
    for i, j in itertools.combinations(range(n), 2):
        pc = contra_sym(texts[i], texts[j])
        if pc >= CONTRA_KEEP:
            g.add_edge(i, j, "contradict", w=pc)
    return g

def ensure_injected_edge(g, u, v):
    for idx, e in enumerate(g.edges):
        if e.rel == "contradict" and {e.u, e.v} == {u, v}:
            return idx
    g.add_edge(u, v, "contradict", w=max(contra_sym(g.claims[u], g.claims[v]), 0.02))
    return len(g.edges) - 1

def make_field_v12(k, hedge=False):
    # target step index is n-k (violation appended at the end), so n >= k+2
    pool = [c for c in chains if len(c["steps"]) >= k + 2]
    ch = pool[int(rng.integers(len(pool)))]
    steps = list(ch["steps"])
    n = len(steps)
    target = n - k                       # violation appended at end, distance k
    clean_txt, clean_ass = list(steps), [True] * n
    vio_txt = steps + [neg_text(steps[target])]
    vio_ass = [True] * (n + 1)
    if hedge:
        hidx = int(rng.integers(0, n))
        hs = HEDGE_TEMPLATE.format(c=steps[hidx][0].lower() + steps[hidx][1:].rstrip("."))
        clean_txt, clean_ass = clean_txt + [hs], clean_ass + [False]
        vio_txt, vio_ass = vio_txt + [hs], vio_ass + [False]
    g_clean = build_graph(clean_txt, clean_ass)
    g_vio = build_graph(vio_txt, vio_ass)
    inj = ensure_injected_edge(g_vio, n, target)
    return CasePair(View(g_clean), View(g_vio),
                    "V4" if hedge else ("V1" if k == 1 else "V2"), k, ("g", inj))

CLOSING_TEMPLATES = [
    "Overall, the final result of {f:g} is about {c:g} times the initial value of {i:g} in this problem.",
    "In summary, going from the starting quantity of {i:g} to the final {f:g} amounts to a factor of roughly {c:g}.",
    "Putting it together, the answer {f:g} represents approximately {c:g} times the original {i:g}.",
]

def make_field_v3():
    pool = [c for c in chains
            if sum(v is not None and v > 0 for v in c["eqvals"]) >= 3]
    ch = pool[int(rng.integers(len(pool)))]
    vals = [v for v in ch["eqvals"] if v is not None and v > 0]
    v0, vlast = vals[0], vals[-1]
    true_c = vlast / v0

    tmpl = CLOSING_TEMPLATES[int(rng.integers(len(CLOSING_TEMPLATES)))]

    def build(consistent):
        c = (true_c * (1 + rng.normal(0, 0.02)) if consistent
             else true_c * float(rng.choice([1, -1]) * rng.uniform(0.45, 0.9) + 1.0))
        closing = tmpl.format(f=vlast, c=round(c, 2), i=v0)
        texts = list(ch["steps"]) + [closing]
        g = build_graph(texts, [True] * len(texts))
        nodes = list(range(len(vals)))
        aedges = [(i, i + 1, math.log(vals[i+1] / vals[i]), 0.95)
                  for i in range(len(vals) - 1)]
        aedges.append((0, len(vals) - 1, math.log(max(round(c, 2), 1e-6)), 0.95))
        return View(g, nodes, aedges)

    clean, vio = build(True), build(False)
    return CasePair(clean, vio, "V3", 0, ("aff", len(vio.aff_edges) - 1))

def make_field_case(vtype, k):
    if vtype in ("V1", "V2"):
        return make_field_v12(k)
    if vtype == "V3":
        return make_field_v3()
    return make_field_v12(1, hedge=True)

# %% [markdown]
# ## 4. E0 — field measurement of (S1) and (S2)

# %%
S1_N = 30 if QUICK else 120
s1_direct, s1_cross = {}, {}
for k in range(1, 6):
    d_confs, x_confs = [], []
    for _ in range(S1_N):
        pool = [c for c in chains if len(c["steps"]) >= 6]
        ch = pool[int(rng.integers(len(pool)))]
        i = int(rng.integers(0, len(ch["steps"]) - k))
        neg = neg_text(ch["steps"][i])
        d_confs.append(contra_sym(neg, ch["steps"][i]))
        x_confs.append(contra_sym(neg, ch["steps"][i + k]))
    s1_direct[k] = (float(np.mean(d_confs)), float(np.std(d_confs)))
    s1_cross[k] = (float(np.mean(x_confs)), float(np.std(x_confs)))
kstar_cross = next((k for k in range(1, 6) if s1_cross[k][0] < 0.5), None)
print("S1 direct (neg vs target):", {k: round(v[0], 3) for k, v in s1_direct.items()})
print("S1 cross  (neg vs +k)    :", {k: round(v[0], 3) for k, v in s1_cross.items()})

s2_hits, s2_n = 0, (60 if QUICK else 300)
for _ in range(s2_n):
    ch = chains[int(rng.integers(len(chains)))]
    i = int(rng.integers(0, len(ch["steps"])))
    hs = HEDGE_TEMPLATE.format(c=ch["steps"][i][0].lower()
                               + ch["steps"][i][1:].rstrip("."))
    if contra_sym(hs, ch["steps"][i]) >= 0.5:
        s2_hits += 1
s2_rate = s2_hits / s2_n
s2_ci = svgstats.clopper_pearson(s2_hits, s2_n)
print(f"S2 hedged FP rate = {s2_rate:.3f}  CP95={tuple(round(x,3) for x in s2_ci)}")

# %% [markdown]
# ## 5. E1 — paired comparison on real chains
# Primary sheaf arm SHEAF_MAX applies the manuscript's P3 principle (localized
# violations aggregate by max, never sum — Prop. 3.4/3.5; harness amendment O1)
# across the two f3 channels (pairwise relaxed energy; numeric holonomy), each
# normalized by its 90th-percentile clean score on a per-cell calibration split
# that is excluded from evaluation. The as-specified quadrature energy (SHEAF)
# is retained as the sensitivity arm. Registered as protocol deviation D2
# before the confirmatory run; frozen verdict rules applied to the primary arm.

# %%
def fpr_at_tpr(pos, neg, tpr=0.95):
    thr = np.quantile(np.asarray(pos, float), 1 - tpr)
    return float((np.asarray(neg, float) >= thr).mean())

def sheaf_channels(view):
    e_pair, x_star = f3_unified(view.g, **PGD)
    e_aff, res = (affine_energy(view.aff_nodes, view.aff_edges)
                  if view.aff_edges else (0.0, []))
    return e_pair, e_aff, x_star, res

ARMS = ["COUNT", "WSUM", "NLIMAX", "SAT", "SHEAF", "SHEAF_MAX"]
BASELINES = ["COUNT", "WSUM", "NLIMAX", "SAT"]
results, results_sens, raw_scores = {}, {}, {}
for vtype, k in CELLS:
    cases = []
    for case_i in range(N_PER_CELL):
        cp = make_field_case(vtype, k)
        rec = {name: (fn(cp.clean), fn(cp.violated))
               for name, fn in DETECTORS.items()}
        pc, pa, _, _ = sheaf_channels(cp.clean)
        vc, va, x_star, aff = sheaf_channels(cp.violated)
        rec["_ch"] = (pc, pa, vc, va)
        rec["SHEAF"] = (math.sqrt(pc*pc + pa*pa), math.sqrt(vc*vc + va*va))
        rec["_loc"] = bool(sheaf_localize(cp.violated, x_star, aff, cp.injected))
        rec["_locb"] = bool(cp.injected[0] == "g"
                            and cp.violated.g.edges[cp.injected[1]].w >= 0.5)
        cases.append(rec)
    n_cal_split = max(5, int(0.3 * len(cases)))
    cal, ev = cases[:n_cal_split], cases[n_cal_split:]
    tau_p = max(float(np.quantile([c["_ch"][0] for c in cal], 0.9)), 1e-6)
    tau_a = max(float(np.quantile([c["_ch"][1] for c in cal], 0.9)), 1e-6)
    for c in cases:
        pc, pa, vc, va = c["_ch"]
        c["SHEAF_MAX"] = (max(pc / tau_p, pa / tau_a),
                          max(vc / tau_p, va / tau_a))
    scores = {a: {"pos": [c[a][1] for c in ev], "neg": [c[a][0] for c in ev]}
              for a in ARMS}
    aur = {a: svgstats.auroc(scores[a]["pos"], scores[a]["neg"]) for a in ARMS}
    best_bl = max(BASELINES, key=lambda a: aur[a])
    loc_s = float(np.mean([c["_loc"] for c in ev]))
    loc_b = float(np.mean([c["_locb"] for c in ev]))

    def delta_vs(arm):
        return svgstats.paired_bootstrap_delta_auroc(
            scores[arm]["pos"], scores[arm]["neg"],
            scores[best_bl]["pos"], scores[best_bl]["neg"],
            n_boot=N_BOOT, seed=SEED)

    d, lo, hi, p = delta_vs("SHEAF_MAX")
    # frozen verdict rules read the primary arm through the "SHEAF" slot
    aur_primary = dict(aur); aur_primary["SHEAF"] = aur["SHEAF_MAX"]
    results[(vtype, k)] = dict(
        auroc=aur_primary, auroc_all=aur, best_baseline=best_bl,
        delta=(d, lo, hi, p), taus=dict(pair=tau_p, aff=tau_a),
        fpr95={a: fpr_at_tpr(scores[a]["pos"], scores[a]["neg"]) for a in ARMS},
        loc_sheaf=loc_s, loc_base=loc_b, n_eval=len(ev))
    results_sens[(vtype, k)] = dict(delta_quadrature=delta_vs("SHEAF"))
    raw_scores[f"{vtype}_k{k}"] = scores
    print(f"{vtype} k={k}: AUROC={ {a: round(v,3) for a,v in aur.items()} } "
          f"Δ(MAX vs {best_bl})={d:.3f} [{lo:.3f},{hi:.3f}] p={p:.4f} "
          f"loc S/B={loc_s:.2f}/{loc_b:.2f}")

pvals = [results[c]["delta"][3] for c in CELLS]
holm_adj = svgstats.holm(pvals)
for c, ph in zip(CELLS, holm_adj):
    results[c]["p_holm"] = float(ph)
verdict = e1_verdict(results)
print("\n=== FROZEN-RULE VERDICT:", verdict, "===")

# %% [markdown]
# ## 6. E2 — conformal coverage field test (Theorem 4.2)

# %%
clean_pool = np.array([s for cell in raw_scores.values() for s in cell["SHEAF"]["neg"]])
n_cal_e2 = 30 if QUICK else 200
e2 = run_e2(clean_pool, n_cal=n_cal_e2, alpha=0.10,
            R=200 if QUICK else 1000, seed=SEED)
print("E2 coverage field test:", {k: round(v, 4) for k, v in e2.items()})

# %% [markdown]
# ## 7. Plots and consolidated report

# %%
INK, ACC, ACC2 = "#444444", "#3B6FB6", "#B0413E"
ks = [1, 2, 3, 4, 5]

fig, axes = plt.subplots(1, 3, figsize=(16, 4))
axes[0].errorbar(ks, [s1_direct[k][0] for k in ks], yerr=[s1_direct[k][1] for k in ks],
                 color=ACC, marker="o", label="direct pair (¬c_i, c_i)")
axes[0].errorbar(ks, [s1_cross[k][0] for k in ks], yerr=[s1_cross[k][1] for k in ks],
                 color=INK, marker="s", label="cross pair (¬c_i, c_{i+k})")
axes[0].axhline(0.5, color=ACC2, ls="--", lw=1)
axes[0].set_xlabel("distance k"); axes[0].set_ylabel("calibrated P(contradiction)")
axes[0].set_title("E0: field S1"); axes[0].legend(frameon=False)

v2cells = [c for c in CELLS if c[0] in ("V1", "V2")]
for arm, color, mk in [("COUNT", INK, "s"), ("SHEAF", ACC, "o"), ("SAT", "#888888", "^")]:
    axes[1].plot([c[1] for c in v2cells],
                 [results[c]["auroc"][arm] for c in v2cells],
                 color=color, marker=mk, label=arm)
axes[1].axhline(0.5, color=ACC2, ls="--", lw=1)
axes[1].set_xlabel("violation distance k"); axes[1].set_ylabel("AUROC")
axes[1].set_title("E1: detection vs distance"); axes[1].legend(frameon=False)

axes[2].plot([c[1] for c in v2cells], [results[c]["loc_sheaf"] for c in v2cells],
             color=ACC, marker="o", label="SHEAF top-1 loc")
axes[2].plot([c[1] for c in v2cells], [results[c]["loc_base"] for c in v2cells],
             color=INK, marker="s", label="baseline loc")
axes[2].set_xlabel("violation distance k"); axes[2].set_ylabel("localization rate")
axes[2].set_title("E1: localization vs distance"); axes[2].legend(frameon=False)
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(f"{OUT}/plots/m1_field_curves.png", dpi=150); plt.close(fig)

report = dict(
    config=dict(quick=QUICK, nli=NLI_MODEL, temperature=scaler.T,
                ece_pre=ece_pre, ece_post=ece_post, mnli_cal_acc=acc_cal,
                n_chains=len(chains), n_per_cell=N_PER_CELL, n_boot=N_BOOT,
                contra_keep=CONTRA_KEEP, seed=SEED, nli_pairs_scored=len(_cache)),
    e0=dict(s1_direct=s1_direct, s1_cross=s1_cross, kstar_cross=kstar_cross,
            s2_rate=s2_rate, s2_ci=list(s2_ci), s2_n=s2_n),
    e1={f"{v}_k{k}": dict(
            auroc=results[(v, k)]["auroc_all"], best_baseline=results[(v, k)]["best_baseline"],
            delta_auroc_primary=results[(v, k)]["delta"], p_holm=results[(v, k)]["p_holm"],
            delta_auroc_quadrature=results_sens[(v, k)]["delta_quadrature"],
            channel_taus=results[(v, k)]["taus"], n_eval=results[(v, k)]["n_eval"],
            fpr_at_95tpr=results[(v, k)]["fpr95"],
            loc_sheaf=results[(v, k)]["loc_sheaf"], loc_base=results[(v, k)]["loc_base"])
        for v, k in CELLS},
    verdict=verdict,
    e2=dict(**e2, pool_n=int(len(clean_pool)),
            pool_tie_fraction=float(1 - len(np.unique(clean_pool)) / len(clean_pool))),
)
with open(f"{OUT}/m1_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
with open(f"{OUT}/raw_scores.json", "w") as f:
    json.dump(raw_scores, f, default=str)
print(json.dumps(report, indent=2, default=str)[:2500])
print("\nDONE —", OUT)
