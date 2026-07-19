# %% [markdown]
# # Semantic Validation Gates — Empirical Validation v1
#
# Companion experiment for *"Semantic Validation Gates: A Formal Axiomatic Framework
# for Semantic Verification"* (Zhao, 2026, SSRN preprint v1).
#
# Instantiates the five gates (Format, Fact, Logic, Alignment, Intent) as computable
# operators on empirical measures of sentence embeddings, then tests:
#
# - **E1** — the gates are computable end-to-end on GSM8K + TruthfulQA outputs
# - **E2** — Conjecture 5.3: EVT (Fréchet) calibrated thresholds bound false rejection ≤ α
# - **E3** — Theorem 5.1 / Π: lexicographic first-failure classification; per-gate AUROC
# - **E4** — Conjectures 5.2 / 5.4: empirical Lipschitz constants and Π stability under perturbation
#
# Runs on Kaggle GPU (T4), internet ON. No HF token required (all public models/datasets).
# Set env `QUICK=1` for a small smoke-test run.

# %%
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "POT", "sentence-transformers", "datasets"], check=True)

# %%
import os, re, json, math, random, itertools, warnings
import numpy as np
import pandas as pd
import torch
import ot  # POT
from scipy import stats
from scipy.spatial.distance import cdist
from sklearn.metrics import roc_auc_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

QUICK = os.environ.get("QUICK", "1") == "1"  # default flips per push: smoke vs full run
N_PER_DATASET = 20 if QUICK else 150
GEN_MODEL = "Qwen/Qwen2.5-0.5B-Instruct" if QUICK else "Qwen/Qwen2.5-1.5B-Instruct"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
NLI_MODEL = "cross-encoder/nli-deberta-v3-xsmall"
TOX_MODEL = "unitary/toxic-bert"
MAX_SENTS = 12          # cap sentences per output for pairwise NLI
KDE_JITTER = 0.05       # KDE smoothing scale for the fact reference measure
ALPHAS = [0.01, 0.05, 0.10]
ALPHA_MAIN = 0.05
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

OUT = "/kaggle/working/results" if os.path.isdir("/kaggle/working") else "./results"
os.makedirs(f"{OUT}/plots", exist_ok=True)
print(f"device={DEVICE} quick={QUICK} N={N_PER_DATASET} model={GEN_MODEL}")

# %% [markdown]
# ## 1. Data — GSM8K (test) and TruthfulQA (generation)

# %%
from datasets import load_dataset

gsm = load_dataset("openai/gsm8k", "main", split="test").shuffle(seed=SEED).select(range(N_PER_DATASET))
tqa = load_dataset("truthful_qa", "generation", split="validation").shuffle(seed=SEED).select(range(N_PER_DATASET))

def gsm_gold_number(ans: str):
    m = re.search(r"####\s*([-+]?[\d,]*\.?\d+)", ans)
    return m.group(1).replace(",", "") if m else None

items = []
for r in gsm:
    items.append(dict(
        dataset="gsm8k", question=r["question"],
        reference=r["answer"].split("####")[0].strip(),          # gold reasoning (fact reference)
        gold=gsm_gold_number(r["answer"]),
        correct_refs=None, incorrect_refs=None,
    ))
for r in tqa:
    items.append(dict(
        dataset="truthful_qa", question=r["question"],
        reference=" ".join(r["correct_answers"]),
        gold=None,
        correct_refs=r["correct_answers"], incorrect_refs=r["incorrect_answers"],
    ))
print(len(items), "items")

# %% [markdown]
# ## 2. Generation

# %%
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained(GEN_MODEL)
lm = AutoModelForCausalLM.from_pretrained(GEN_MODEL, torch_dtype=torch.float16,
                                          device_map=DEVICE)

GSM_SYS = ("Solve the math problem step by step. "
           "End your response with the final numeric answer on its own last line "
           "in exactly this format: #### <number>")
TQA_SYS = "Answer the question truthfully and concisely, in at most four sentences."

def build_prompt(it):
    sys_msg = GSM_SYS if it["dataset"] == "gsm8k" else TQA_SYS
    msgs = [{"role": "system", "content": sys_msg},
            {"role": "user", "content": it["question"]}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

BATCH = 8
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

outputs = []
for i in range(0, len(items), BATCH):
    batch = items[i:i+BATCH]
    prompts = [build_prompt(it) for it in batch]
    enc = tok(prompts, return_tensors="pt", padding=True).to(DEVICE)
    with torch.no_grad():
        gen = lm.generate(**enc, max_new_tokens=400, do_sample=False,
                          pad_token_id=tok.pad_token_id)
    for j, it in enumerate(batch):
        text = tok.decode(gen[j][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        outputs.append(text.strip())
    if i % 40 == 0:
        print(f"generated {i+len(batch)}/{len(items)}")
for it, o in zip(items, outputs):
    it["output"] = o

del lm
torch.cuda.empty_cache()

# %% [markdown]
# ## 3. Correctness labels
# GSM8K: exact numeric match. TruthfulQA: nearest-reference embedding proxy
# (closer to a correct reference than to any incorrect one).

# %%
from sentence_transformers import SentenceTransformer, CrossEncoder

emb_model = SentenceTransformer(EMB_MODEL, device=DEVICE)

def embed(texts):
    if len(texts) == 0:
        return np.zeros((0, 384), dtype=np.float32)
    return np.asarray(emb_model.encode(texts, normalize_embeddings=True,
                                       show_progress_bar=False), dtype=np.float32)

def split_sents(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    parts = [p.strip() for p in parts if len(p.strip()) >= 3]
    return parts[:MAX_SENTS] if parts else [text.strip()[:200] or "empty"]

def extract_pred_number(text):
    m = re.search(r"####\s*([-+]?[\d,]*\.?\d+)", text)
    if m:
        return m.group(1).replace(",", "")
    nums = re.findall(r"[-+]?[\d,]*\.?\d+", text)
    return nums[-1].replace(",", "") if nums else None

def num_eq(a, b):
    try:
        return a is not None and b is not None and abs(float(a) - float(b)) < 1e-4
    except ValueError:
        return False

for it in items:
    if it["dataset"] == "gsm8k":
        it["correct"] = num_eq(extract_pred_number(it["output"]), it["gold"])
    else:
        e_out = embed([it["output"]])[0]
        e_cor = embed(it["correct_refs"]); e_inc = embed(it["incorrect_refs"])
        sim_c = float(np.max(e_cor @ e_out)) if len(e_cor) else -1.0
        sim_i = float(np.max(e_inc @ e_out)) if len(e_inc) else -1.0
        it["correct"] = sim_c > sim_i
print("accuracy:", np.mean([it["correct"] for it in items]))

# %% [markdown]
# ## 4. The five gates
# Output representation: empirical measure µ = uniform point cloud of sentence
# embeddings on the unit sphere. W2 computed exactly with POT.

# %%
def w2(X, Y, wx=None, wy=None):
    """2-Wasserstein distance between empirical measures (rows = support points)."""
    if len(X) == 0 or len(Y) == 0:
        return 0.0
    wx = np.ones(len(X)) / len(X) if wx is None else wx
    wy = np.ones(len(Y)) / len(Y) if wy is None else wy
    M = cdist(X, Y, metric="sqeuclidean")
    return float(np.sqrt(max(ot.emd2(wx, wy, M), 0.0)))

def mmd_rbf(X, Y, gamma=1.0):
    """RKHS kernel-mean-embedding distance ‖ψ(µ)−ψ(ν)‖ (biased MMD estimate)."""
    Kxx = np.exp(-gamma * cdist(X, X, "sqeuclidean")).mean()
    Kyy = np.exp(-gamma * cdist(Y, Y, "sqeuclidean")).mean()
    Kxy = np.exp(-gamma * cdist(X, Y, "sqeuclidean")).mean()
    return float(np.sqrt(max(Kxx + Kyy - 2 * Kxy, 0.0)))

# --- f1 Format: distance to minimal format repair -----------------------------
GSM_FMT = re.compile(r"####\s*[-+]?[\d,]*\.?\d+\s*$")

def format_check_and_repair(it):
    """Returns (is_valid, repaired_text)."""
    text = it["output"]
    if it["dataset"] == "gsm8k":
        if GSM_FMT.search(text):
            return True, text
        n = extract_pred_number(text)
        return False, text + f"\n#### {n if n is not None else 0}"
    sents = split_sents(text)
    ok = 0 < len(text.strip()) and len(sents) <= 6
    return ok, " ".join(sents[:6]) if sents else "No answer."

# --- f3 Logic: Hodge residual of the pairwise-NLI entailment flow -------------
nli = CrossEncoder(NLI_MODEL, device=DEVICE)  # logits: [contradiction, entailment, neutral]

def nli_probs(pairs):
    if not pairs:
        return np.zeros((0, 3))
    logits = nli.predict(pairs, show_progress_bar=False,
                         convert_to_numpy=True, batch_size=64)
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)

def logic_components(sents):
    """Cache pairwise NLI once per sample: {(i,j): (p_contra, p_entail_ij, p_entail_ji)}."""
    n = len(sents)
    if n < 2:
        return {}
    pairs, idx = [], []
    for i, j in itertools.combinations(range(n), 2):
        pairs += [(sents[i], sents[j]), (sents[j], sents[i])]
        idx.append((i, j))
    P = nli_probs(pairs)
    out = {}
    for k, (i, j) in enumerate(idx):
        pij, pji = P[2*k], P[2*k+1]
        out[(i, j)] = (float(max(pij[0], pji[0])), float(pij[1]), float(pji[1]))
    return out

def f3_from_components(comp, keep=None):
    """Hodge residual norm of the entailment-asymmetry flow + max contradiction.
    `keep`: optional set of retained sentence indices (for perturbations)."""
    edges = [(i, j) for (i, j) in comp
             if keep is None or (i in keep and j in keep)]
    if len(edges) < 3:
        max_c = max((comp[e][0] for e in edges), default=0.0)
        return 0.5 * max_c, dict(resid=0.0, max_contra=max_c)
    nodes = sorted({k for e in edges for k in e})
    pos = {v: k for k, v in enumerate(nodes)}
    B = np.zeros((len(edges), len(nodes)))
    Y = np.zeros(len(edges))
    for r, (i, j) in enumerate(edges):
        B[r, pos[i]], B[r, pos[j]] = 1.0, -1.0
        Y[r] = comp[(i, j)][1] - comp[(i, j)][2]      # entailment asymmetry flow
    s, *_ = np.linalg.lstsq(B, Y, rcond=None)
    resid = float(np.linalg.norm(Y - B @ s) / math.sqrt(len(edges)))
    max_c = max(comp[e][0] for e in edges)
    return 0.5 * resid + 0.5 * max_c, dict(resid=resid, max_contra=max_c)

# --- f4 Alignment: W2 to the detoxified projection ----------------------------
from transformers import pipeline as hf_pipeline
tox_clf = hf_pipeline("text-classification", model=TOX_MODEL, device=0 if DEVICE == "cuda" else -1)

def toxicity_scores(sents):
    res = tox_clf(sents, truncation=True, batch_size=32)
    return [r["score"] if r["label"].lower() == "toxic" else 1 - r["score"] for r in res]

# --- assemble all gates from cached components --------------------------------
def gate_values(E, fmt_ok, E_repair, E_fact, tox, comp, E_intent, keep=None):
    """All five raw deviations from cached per-sample components.
    E: sentence embeddings (n,d); keep: retained indices for perturbations."""
    idx = list(range(len(E))) if keep is None else sorted(keep)
    X = E[idx]
    f1 = 0.0 if fmt_ok and keep is None else w2(X, E_repair)
    f2 = w2(X, E_fact)
    f3, f3_parts = f3_from_components(comp, keep=set(idx) if keep is not None else None)
    safe = [i for i in idx if tox[i] < 0.5]
    f4 = 0.0 if len(safe) == len(idx) else w2(X, E[safe] if safe else E_intent)
    f5 = mmd_rbf(X, E_intent)
    return dict(f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, **f3_parts)

# %% [markdown]
# ## 5. E1 — compute all raw deviations

# %%
records = []
for k, it in enumerate(items):
    sents = split_sents(it["output"])
    E = embed(sents)
    fmt_ok, repaired = format_check_and_repair(it)
    E_repair = embed(split_sents(repaired))
    # KDE-smoothed fact reference: gold reasoning / correct answers + Gaussian jitter
    ref_sents = split_sents(it["reference"])
    E_ref = embed(ref_sents)
    jit = np.concatenate([E_ref + np.random.normal(0, KDE_JITTER, E_ref.shape)
                          for _ in range(3)])
    E_fact = np.concatenate([E_ref, jit])
    tox = toxicity_scores(sents)
    comp = logic_components(sents)
    E_intent = embed([it["question"]] + split_sents(it["reference"]))
    g = gate_values(E, fmt_ok, E_repair, E_fact, tox, comp, E_intent)
    it["_cache"] = dict(E=E, fmt_ok=fmt_ok, E_repair=E_repair, E_fact=E_fact,
                        tox=tox, comp=comp, E_intent=E_intent)
    records.append(dict(idx=k, dataset=it["dataset"], correct=bool(it["correct"]),
                        fmt_ok=bool(fmt_ok), tox_max=float(max(tox)),
                        n_sents=len(sents), **g))
    if k % 25 == 0:
        print(f"gates {k}/{len(items)}")

df = pd.DataFrame(records)
df.to_csv(f"{OUT}/records.csv", index=False)
print(df.groupby(["dataset", "correct"])[["f1", "f2", "f3", "f4", "f5"]].mean().round(4))

# %% [markdown]
# ## 6. E2 — EVT threshold calibration (Conjecture 5.3)
# Fit a Fréchet distribution to each gate's deviations over *valid* calibration
# outputs; τᵢ(α) = F⁻¹(1−α). Check held-out valid false-rejection rate ≤ α.

# %%
GATES = ["f1", "f2", "f3", "f4", "f5"]
valid_mask = df["correct"] & df["fmt_ok"] & (df["tox_max"] < 0.5)
valid_idx = df.index[valid_mask].to_numpy()
rng = np.random.default_rng(SEED)
rng.shuffle(valid_idx)
n_cal = int(0.6 * len(valid_idx))
cal_idx, held_idx = valid_idx[:n_cal], valid_idx[n_cal:]
print(f"valid={len(valid_idx)} cal={len(cal_idx)} held={len(held_idx)}")

def fit_tau(x, alpha):
    """Fréchet (invweibull) tail quantile; empirical-quantile fallback."""
    x = np.asarray(x, dtype=float)
    if x.max() - x.min() < 1e-9:
        return float(x.max() + 1e-6), "degenerate"
    try:
        c, loc, scale = stats.invweibull.fit(x[x > x.min()], floc=float(x.min()) - 1e-9)
        tau = float(stats.invweibull.ppf(1 - alpha, c, loc, scale))
        if np.isfinite(tau) and tau > 0:
            return tau, "frechet"
    except Exception:
        pass
    return float(np.quantile(x, 1 - alpha)), "empirical"

evt = {}
for alpha in ALPHAS:
    taus, methods = {}, {}
    for g in GATES:
        taus[g], methods[g] = fit_tau(df.loc[cal_idx, g].values, alpha)
    held = df.loc[held_idx, GATES]
    per_gate_rej = {g: float((held[g] / taus[g] > 1).mean()) for g in GATES}
    any_rej = float(((held / pd.Series(taus)) > 1).any(axis=1).mean())
    evt[str(alpha)] = dict(taus=taus, methods=methods, per_gate_false_rejection=per_gate_rej,
                           overall_false_rejection=any_rej, union_bound=5 * alpha)
    print(f"alpha={alpha}: overall FR={any_rej:.3f} (union bound {5*alpha}) per-gate={per_gate_rej}")

with open(f"{OUT}/evt_validation.json", "w") as f:
    json.dump(evt, f, indent=2)
TAU = evt[str(ALPHA_MAIN)]["taus"]
with open(f"{OUT}/thresholds.json", "w") as f:
    json.dump(TAU, f, indent=2)

# %% [markdown]
# ## 7. E3 — lexicographic classification Π and per-gate discrimination

# %%
for g in GATES:
    df[f"rho_{g[1]}"] = df[g] / TAU[g]

def pi_of(row):
    for i in range(1, 6):
        if row[f"rho_{i}"] > 1:
            return i
    return 0

df["Pi"] = df.apply(pi_of, axis=1)

pi_table = df.groupby(["correct", "Pi"]).size().unstack(fill_value=0)
print("Π distribution (rows=correct):\n", pi_table)

auroc = {}
y = (~df["correct"]).astype(int)
for i, g in enumerate(GATES, 1):
    try:
        auroc[g] = float(roc_auc_score(y, df[f"rho_{i}"]))
    except ValueError:
        auroc[g] = float("nan")
auroc["rho_max"] = float(roc_auc_score(y, df[[f"rho_{i}" for i in range(1, 6)]].max(axis=1)))
auroc_by_ds = {ds: {g: (float(roc_auc_score((~d["correct"]).astype(int), d[f"rho_{i}"]))
                        if d["correct"].nunique() > 1 else float("nan"))
                    for i, g in enumerate(GATES, 1)}
               for ds, d in df.groupby("dataset")}
print("AUROC:", auroc)
with open(f"{OUT}/auroc.json", "w") as f:
    json.dump(dict(overall=auroc, by_dataset=auroc_by_ds), f, indent=2)

# %% [markdown]
# ## 8. E4 — perturbation robustness (Conjectures 5.2 / 5.4)

# %%
def perturb_variants(cache):
    """Yield (name, E_perturbed_or_None, keep_indices_or_None)."""
    E = cache["E"]; n = len(E)
    for sig in (0.01, 0.03, 0.10):
        yield f"jitter_{sig}", E + np.random.normal(0, sig, E.shape), None
    if n >= 3:
        d = int(rng.integers(n))
        yield "drop_one", None, [i for i in range(n) if i != d]
        u = int(rng.integers(n))
        # duplicating a sentence = reweighting its mass
        yield "dup_one", np.concatenate([E, E[u:u+1]]), None

pert_rows = []
sub = df.index[:min(60, len(df))]
for k in sub:
    it = items[k]; c = it["_cache"]
    base = {f"rho_{i}": df.loc[k, f"rho_{i}"] for i in range(1, 6)}
    base_pi = df.loc[k, "Pi"]
    for name, Ep, keep in perturb_variants(c):
        if Ep is not None and keep is None:
            g = gate_values(Ep, c["fmt_ok"], c["E_repair"], c["E_fact"],
                            c["tox"] + [0.0] * (len(Ep) - len(c["tox"])),
                            c["comp"], c["E_intent"])
            dist = w2(c["E"], Ep)
        else:
            g = gate_values(c["E"], c["fmt_ok"], c["E_repair"], c["E_fact"],
                            c["tox"], c["comp"], c["E_intent"], keep=keep)
            dist = w2(c["E"], c["E"][sorted(keep)])
        rhos = {f"rho_{i}": g[f"f{i}"] / TAU[f"f{i}"] for i in range(1, 6)}
        new_pi = next((i for i in range(1, 6) if rhos[f"rho_{i}"] > 1), 0)
        pert_rows.append(dict(idx=k, pert=name, w2_dist=dist,
                              pi_flip=int(new_pi != base_pi),
                              **{f"d_rho_{i}": abs(rhos[f"rho_{i}"] - base[f"rho_{i}"])
                                 for i in range(1, 6)}))

pdf_ = pd.DataFrame(pert_rows)
pdf_.to_csv(f"{OUT}/lipschitz.csv", index=False)

lip = {}
m = pdf_["w2_dist"] > 1e-9
for i in range(1, 6):
    x, yv = pdf_.loc[m, "w2_dist"], pdf_.loc[m, f"d_rho_{i}"]
    lip[f"rho_{i}"] = float((x * yv).sum() / (x * x).sum()) if len(x) else 0.0
pdf_["dist_bin"] = pd.qcut(pdf_["w2_dist"].rank(method="first"), 4,
                           labels=["q1_small", "q2", "q3", "q4_large"])
flip_by_bin = pdf_.groupby("dist_bin", observed=True)["pi_flip"].mean().to_dict()
flip_small = float(pdf_.loc[pdf_["w2_dist"] <= pdf_["w2_dist"].quantile(0.25), "pi_flip"].mean())
print("empirical Lipschitz slopes:", lip)
print("Π flip rate by distance bin:", flip_by_bin)

# %% [markdown]
# ## 9. Plots and summary

# %%
INK, ACC = "#444444", "#3B6FB6"

fig, axes = plt.subplots(1, 5, figsize=(18, 3.2))
for ax, (i, g) in zip(axes, enumerate(GATES, 1)):
    for lab, sty in [(True, dict(color=ACC, alpha=0.65)), (False, dict(color=INK, alpha=0.55))]:
        vals = df.loc[df["correct"] == lab, f"rho_{i}"]
        ax.hist(vals, bins=24, density=True, label="correct" if lab else "incorrect", **sty)
    ax.axvline(1.0, color="#B0413E", lw=1.2, ls="--")
    ax.set_title(f"ρ{i} ({g})"); ax.spines[["top", "right"]].set_visible(False)
axes[0].legend(frameon=False)
fig.suptitle("Normalized deviations by correctness (dashed = validity threshold)")
fig.tight_layout(); fig.savefig(f"{OUT}/plots/rho_distributions.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.5))
ct = pd.crosstab(df["Pi"], df["correct"], normalize="columns")
x = np.arange(len(ct.index)); w = 0.38
if True in ct.columns:
    ax.bar(x - w/2, ct.get(True, 0), w, color=ACC, label="correct")
if False in ct.columns:
    ax.bar(x + w/2, ct.get(False, 0), w, color=INK, label="incorrect")
ax.set_xticks(x, [f"Π={i}" for i in ct.index]); ax.set_ylabel("share")
ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("First-failing gate Π (0 = fully valid)")
fig.tight_layout(); fig.savefig(f"{OUT}/plots/pi_by_correctness.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(pdf_["w2_dist"], pdf_[[f"d_rho_{i}" for i in range(1, 6)]].max(axis=1),
           s=12, alpha=0.5, color=ACC)
ax.set_xlabel("W2(µ, µ′)"); ax.set_ylabel("max_i |Δρᵢ|")
ax.set_title("Perturbation response (Conjectures 5.2/5.4)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(f"{OUT}/plots/lipschitz_scatter.png", dpi=150); plt.close(fig)

summary = dict(
    config=dict(quick=QUICK, n_per_dataset=N_PER_DATASET, gen_model=GEN_MODEL,
                emb_model=EMB_MODEL, nli_model=NLI_MODEL, alphas=ALPHAS, seed=SEED),
    e1=dict(n_outputs=len(df), accuracy=float(df["correct"].mean()),
            accuracy_by_dataset=df.groupby("dataset")["correct"].mean().to_dict(),
            mean_deviations_by_correct={str(k): v for k, v in
                df.groupby("correct")[GATES].mean().round(5).T.to_dict().items()}),
    e2_evt=evt,
    e3=dict(auroc_overall=auroc, auroc_by_dataset=auroc_by_ds,
            pi_distribution={str(k): {str(c): int(n) for c, n in v.items()}
                             for k, v in pi_table.to_dict().items()},
            detection_rate_incorrect=float((df.loc[~df["correct"], "Pi"] > 0).mean())
                if (~df["correct"]).any() else float("nan"),
            pass_rate_correct=float((df.loc[df["correct"], "Pi"] == 0).mean())),
    e4=dict(empirical_lipschitz=lip, pi_flip_by_distance_bin=
            {str(k): float(v) for k, v in flip_by_bin.items()},
            pi_flip_rate_smallest_quartile=flip_small),
)
with open(f"{OUT}/summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(json.dumps(summary, indent=2, default=str)[:3000])
print("\nDONE — results in", OUT)
