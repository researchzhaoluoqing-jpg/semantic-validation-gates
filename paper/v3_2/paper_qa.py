"""Pre-submission QA: reconcile every number reported in the manuscript
against the raw experimental artifacts, and run structural checks."""
import json, re, io, os, glob

ROOT = r"C:\Users\AItra\machineL\Papers\Working_Paper_Gates"
PAPER = os.path.join(ROOT, "paper", "v3_2")

R = {}
for name, path in [
    ("confirm", "experiments/results/m1_full_v7/results/m1_report.json"),
    ("scale",   "experiments/results/m1_scale_v8/results/m1_report.json"),
    ("repl",    "experiments/results/m1_repl_B/results/m1_report.json"),
]:
    p = os.path.join(ROOT, path)
    R[name] = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None
    print(f"artifact {name:8s}: {'loaded' if R[name] else 'MISSING'}")

tex = ""
for f in [os.path.join(PAPER, "main.tex")] + sorted(glob.glob(os.path.join(PAPER, "sections", "*.tex"))):
    tex += io.open(f, encoding="utf-8").read()

fails, warns = [], []

def chk(label, claimed, actual, tol=5e-4):
    ok = actual is not None and abs(float(claimed) - float(actual)) <= tol
    print(f"  {'OK ' if ok else 'FAIL'} {label:44s} paper={claimed}  data={actual}")
    if not ok:
        fails.append(label)

print("\n=== A. Confirmatory run (v7) numbers ===")
c = R["confirm"]
e1 = c["e1"]
chk("V3 SHEAF_MAX AUROC", 0.990, round(e1["V3_k0"]["auroc"]["SHEAF_MAX"], 3))
chk("V3 quadrature AUROC", 0.586, round(e1["V3_k0"]["auroc"]["SHEAF"], 3))
chk("V3 delta", 0.489, round(e1["V3_k0"]["delta_auroc_primary"][0], 3))
chk("V3 CI low", 0.470, round(e1["V3_k0"]["delta_auroc_primary"][1], 3))
chk("V3 CI high", 0.503, round(e1["V3_k0"]["delta_auroc_primary"][2], 3))
chk("V3 Holm p", 0.0018, round(e1["V3_k0"]["p_holm"], 4))
chk("V3 FPR@95TPR (max-form)", 0.010, round(e1["V3_k0"]["fpr_at_95tpr"]["SHEAF_MAX"], 3))
chk("V3 baseline FPR@95TPR", 0.943, round(e1["V3_k0"]["fpr_at_95tpr"]["COUNT"], 3))
chk("V3 localization sheaf", 0.24, round(e1["V3_k0"]["loc_sheaf"], 2), tol=5e-3)
chk("V3 localization baseline", 0.00, round(e1["V3_k0"]["loc_base"], 2), tol=5e-3)
chk("V4 delta", 0.019, round(e1["V4_k1"]["delta_auroc_primary"][0], 3))
chk("n_eval per cell", 105, e1["V1_k1"]["n_eval"], tol=0)
chk("temperature T", 1.452, round(c["config"]["temperature"], 3))
chk("ECE post", 0.011, round(c["config"]["ece_post"], 3))
chk("ECE pre", 0.040, round(c["config"]["ece_pre"], 3))
chk("MNLI accuracy", 0.911, round(c["config"]["mnli_cal_acc"], 3))
chk("n chains", 450, c["config"]["n_chains"], tol=0)
chk("NLI pairs scored", 22706, c["config"]["nli_pairs_scored"], tol=0)
chk("E2 pooled exceedance", 0.0952, round(c["e2"]["pooled_err"], 4))
chk("E2 tie fraction", 0.397, round(c["e2"]["pool_tie_fraction"], 3))
chk("E2 pool n", 735, c["e2"]["pool_n"], tol=0)
for k, v in [("1", 0.749), ("2", 0.740), ("3", 0.742), ("4", 0.764), ("5", 0.756)]:
    chk(f"S1 direct k={k}", v, round(c["e0"]["s1_direct"][k][0], 3))
chk("S2 rate", 0.0, c["e0"]["s2_rate"])
chk("S2 CP upper", 0.012, round(c["e0"]["s2_ci"][1], 3))
chk("S2 n", 300, c["e0"]["s2_n"], tol=0)

print("\n  Table row check (paper table vs artifact, all arms):")
table_rows = {
    "V1_k1": dict(SHEAF_MAX=0.719, SHEAF=0.719, COUNT=0.696, WSUM=0.719, NLIMAX=0.531, SAT=0.514),
    "V2_k2": dict(SHEAF_MAX=0.741, SHEAF=0.741, COUNT=0.710, WSUM=0.741, NLIMAX=0.520, SAT=0.505),
    "V2_k3": dict(SHEAF_MAX=0.756, SHEAF=0.756, COUNT=0.734, WSUM=0.756, NLIMAX=0.513, SAT=0.505),
    "V2_k4": dict(SHEAF_MAX=0.717, SHEAF=0.717, COUNT=0.685, WSUM=0.717, NLIMAX=0.503, SAT=0.500),
    "V2_k5": dict(SHEAF_MAX=0.739, SHEAF=0.739, COUNT=0.701, WSUM=0.739, NLIMAX=0.502, SAT=0.500),
    "V3_k0": dict(SHEAF_MAX=0.990, SHEAF=0.586, COUNT=0.498, WSUM=0.501, NLIMAX=0.500, SAT=0.500),
    "V4_k1": dict(SHEAF_MAX=0.751, SHEAF=0.751, COUNT=0.696, WSUM=0.732, NLIMAX=0.518, SAT=0.510),
}
for cell, arms in table_rows.items():
    for arm, val in arms.items():
        chk(f"table {cell}/{arm}", val, round(e1[cell]["auroc"][arm], 3))

print("\n=== B. Scale-up run (v8) numbers ===")
s = R["scale"]
chk("scale n chains", 1000, s["config"]["n_chains"], tol=0)
chk("scale n_eval", 210, s["e1"]["V1_k1"]["n_eval"], tol=0)
chk("scale pairs", 46936, s["config"]["nli_pairs_scored"], tol=0)
chk("scale V3 AUROC", 0.995, round(s["e1"]["V3_k0"]["auroc"]["SHEAF_MAX"], 3))
chk("scale V3 delta", 0.488, round(s["e1"]["V3_k0"]["delta_auroc_primary"][0], 3))
chk("scale V3 CI low", 0.474, round(s["e1"]["V3_k0"]["delta_auroc_primary"][1], 3))
chk("scale V3 CI high", 0.498, round(s["e1"]["V3_k0"]["delta_auroc_primary"][2], 3))
chk("scale V3 FPR", 0.005, round(s["e1"]["V3_k0"]["fpr_at_95tpr"]["SHEAF_MAX"], 3))
chk("scale V3 loc", 0.30, round(s["e1"]["V3_k0"]["loc_sheaf"], 2), tol=5e-3)
chk("scale quadrature", 0.576, round(s["e1"]["V3_k0"]["auroc"]["SHEAF"], 3))
chk("scale E2 pooled", 0.0996, round(s["e2"]["pooled_err"], 4))
chk("scale E2 pool n", 1470, s["e2"]["pool_n"], tol=0)
chk("scale V4 delta", 0.015, round(s["e1"]["V4_k1"]["delta_auroc_primary"][0], 3))
chk("scale S2 rate (paper 0.7%)", 0.007, round(s["e0"]["s2_rate"], 3))

print("\n=== C. Replication run (RoBERTa) numbers ===")
r = R["repl"]
chk("repl T", 1.337, round(r["config"]["temperature"], 3))
chk("repl ECE", 0.012, round(r["config"]["ece_post"], 3))
chk("repl n chains", 600, r["config"]["n_chains"], tol=0)
chk("repl V3 AUROC", 0.999, round(r["e1"]["V3_k0"]["auroc"]["SHEAF_MAX"], 3))
chk("repl V3 delta", 0.489, round(r["e1"]["V3_k0"]["delta_auroc_primary"][0], 3))
chk("repl V3 CI low", 0.479, round(r["e1"]["V3_k0"]["delta_auroc_primary"][1], 3))
chk("repl V3 CI high", 0.498, round(r["e1"]["V3_k0"]["delta_auroc_primary"][2], 3))
chk("repl V3 Holm p", 0.0008, round(r["e1"]["V3_k0"]["p_holm"], 4))
chk("repl V3 FPR", 0.005, round(r["e1"]["V3_k0"]["fpr_at_95tpr"]["SHEAF_MAX"], 3))
chk("repl V3 loc", 0.33, round(r["e1"]["V3_k0"]["loc_sheaf"], 2), tol=5e-3)
chk("repl quadrature", 0.593, round(r["e1"]["V3_k0"]["auroc"]["SHEAF"], 3))
chk("repl V1 max-form", 0.752, round(r["e1"]["V1_k1"]["auroc"]["SHEAF_MAX"], 3))
chk("repl V1 WSUM", 0.752, round(r["e1"]["V1_k1"]["auroc"]["WSUM"], 3))
chk("repl V4 delta", 0.035, round(r["e1"]["V4_k1"]["delta_auroc_primary"][0], 3))
chk("repl E2 pooled", 0.0995, round(r["e2"]["pooled_err"], 4))
chk("repl S2 rate", 0.023, round(r["e0"]["s2_rate"], 3))
chk("repl S2 CP low", 0.009, round(r["e0"]["s2_ci"][0], 3))
chk("repl S2 CP high", 0.047, round(r["e0"]["s2_ci"][1], 3))

print("\n=== D. Structural checks ===")
labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
refs = set(re.findall(r"\\ref\{([^}]+)\}", tex))
missing = sorted(refs - labels)
print(f"  {'OK ' if not missing else 'FAIL'} all \\ref targets defined ({len(refs)} refs, {len(labels)} labels)")
if missing:
    print(f"       missing: {missing}"); fails.append("dangling \\ref")

unused = sorted(l for l in labels if l not in refs and not l.startswith("sec:") and not l.startswith("tab:"))
if unused:
    print(f"  note  labels defined but never \\ref'd: {unused}")

for pat, desc in [(r"\bv3\.\d\b", "internal version marker"),
                  (r"Work in Progress", "draft status label"),
                  (r"\bTODO\b|\bFIXME\b|\bXXX\b", "TODO marker"),
                  (r"\?\?", "literal ?? (broken ref)")]:
    hits = re.findall(pat, tex)
    ok = not hits
    print(f"  {'OK ' if ok else 'FAIL'} no {desc}")
    if not ok:
        fails.append(desc); print(f"       {hits[:5]}")

dup = re.findall(r"\b(\w+)\s+\1\b", tex)
dup = [d for d in dup if d.lower() not in {"that", "had", "the"} and len(d) > 3]
if dup:
    print(f"  note  possible doubled words: {sorted(set(dup))[:10]}")

print("\n=== E. SSRN submission requirements ===")
for pat, desc in [(r"\\title\{", "title present"),
                  (r"Independent Researcher", "author affiliation on PDF"),
                  (r"\\begin\{abstract\}", "abstract present"),
                  (r"Declaration of generative AI use", "AI disclosure on PDF"),
                  (r"\\begin\{thebibliography\}", "reference list present")]:
    ok = bool(re.search(pat, tex))
    print(f"  {'OK ' if ok else 'FAIL'} {desc}")
    if not ok:
        fails.append(desc)

print("\n" + "=" * 60)
print(f"RESULT: {len(fails)} failure(s)" + (f": {fails}" if fails else " — paper matches artifacts"))
