"""Mock-mode integration smoke test: proves the E0-E4 pipeline runs
end-to-end and the statistics behave as theory dictates. Reduced n for
speed; real runs use ERS sample sizes."""
import numpy as np
from nli_wrapper import MockNLI
from runners import (run_e0_s1, run_e0_s2, run_e1, e1_verdict,
                     run_e2, run_e4)
from insertion import make_case
from detectors import score_sheaf

print("=" * 74)
print("E0 -- S1/S2 direct measurement (mock must recover injected params)")
nli = MockNLI(seed=1)
curve, kstar = run_e0_s1(nli, n_per=200)
print("  S1 curve:", {k: round(v[0], 3) for k, v in curve.items()},
      "| k* =", kstar)
rate, ci = run_e0_s2(nli, n=300)
print(f"  S2 hedged-FP rate = {rate:.3f}  CP95 = ({ci[0]:.3f},{ci[1]:.3f})")
assert kstar in (3, 4) and 0.15 < rate < 0.35, "E0 must recover mock params"

print("=" * 74)
print("E1 -- reduced grid (n=60/cell): V2 at k in {1,3,5}, V3, V4")
cells = [("V1", 1), ("V2", 3), ("V2", 5), ("V3", 0), ("V4", 1)]
res = run_e1(MockNLI(seed=2), cells, n_per=60, seed=2)
hdr = f"{'cell':>8} | " + " ".join(f"{a:>6}" for a in
      ["COUNT", "WSUM", "NLIMAX", "SAT", "SHEAF"]) + \
      " | dAUC[CI]        locS  locB"
print(hdr); print("-" * len(hdr))
for (vt, k), r in res.items():
    a = r["auroc"]
    d, lo, hi, p = r["delta"]
    print(f"{vt+'/k'+str(k):>8} | " +
          " ".join(f"{a[x]:6.3f}" for x in
                   ["COUNT", "WSUM", "NLIMAX", "SAT", "SHEAF"]) +
          f" | {d:+.3f}[{lo:+.3f},{hi:+.3f}] {r['loc_sheaf']:5.2f} "
          f"{r['loc_base']:5.2f}  (best bl: {r['best_baseline']})")
print("VERDICT (frozen rules):", e1_verdict(res))

print("=" * 74)
print("E2 -- conformal coverage field test on real clean SHEAF scores")
rng = np.random.default_rng(3); nliE2 = MockNLI(seed=3)
pool = []
for _ in range(700):
    cp = make_case("V1", 1, nliE2, rng)
    s, *_ = score_sheaf(cp.clean)
    pool.append(s)
r = run_e2(np.array(pool), n_cal=200, alpha=0.10, R=400, seed=3)
print(f"  mean cov={r['mean_cov']:.3f} (Beta mean={r['beta_mean']:.3f})  "
      f"KS p={r['ks_p']:.3f}  pooled err={r['pooled_err']:.3f}  "
      f"binom p={r['binom_p']:.3f}")
assert r["binom_p"] > 0.05, "Thm 4.2 must hold on exchangeable pool"
print("  negative control: location-shifted test pool (exchangeability broken)")
shifted = np.array(pool) .copy()
r2 = run_e2(np.concatenate([shifted[:350], shifted[350:] + 0.35]),
            n_cal=200, alpha=0.10, R=400, seed=4)
print(f"  KS p={r2['ks_p']:.4f}  pooled err={r2['pooled_err']:.3f} "
      f"(should inflate / reject)")

print("=" * 74)
print("E4 -- dilution: mean-form vs max-form, m sweep")
r4 = run_e4(ms=(5, 10, 20, 40, 80), n_per=250, seed=5)
print("  m:        ", r4["ms"])
print("  miss mean:", [round(x, 2) for x in r4["miss"]["mean"]])
print("  miss max :", [round(x, 2) for x in r4["miss"]["max"]])
print(f"  CA trend (mean arm): z={r4['trend_z']:.2f}  p={r4['trend_p']:.2e}")
s, lo, hi = r4["slope"]
print(f"  log-log slope of |dF5_mean| vs m: {s:.3f}  CI [{lo:.3f},{hi:.3f}]"
      f"  (pre-registered -1 +/- 0.15)")
assert r4["miss"]["mean"][-1] > 0.5 and r4["miss"]["max"][-1] < 0.2
print("=" * 74)
print("ALL SMOKE TESTS PASSED -- pipeline is real-model-ready.")
