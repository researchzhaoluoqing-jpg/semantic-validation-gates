"""
svg_experiments/nli_wrapper.py -- The frozen measurement instrument (Prop 4.1).
TemperatureScaler implements Guo et al. (2017); ECE per the 15-bin protocol.
MockNLI encodes the E0-measurable mechanisms S1 (distance decay) and S2
(hedged false positives) so the ENTIRE pipeline is integration-testable
without GPUs; HFNLI is the drop-in real backend (ERS G2/G3).
Leakage guard: real backends MUST ignore dist_hint.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import minimize_scalar


class TemperatureScaler:
    """Post-hoc calibration: single scalar T minimizing validation NLL.
    Backing: Guo et al. 2017, 'On Calibration of Modern Neural Networks'.
    Frozen after fit (ERS G3): the same T serves every experiment."""

    def __init__(self):
        self.T = 1.0

    def fit(self, logits, labels):
        logits = np.asarray(logits, float); labels = np.asarray(labels, int)

        def nll(T):
            z = logits / T; z = z - z.max(1, keepdims=True)
            p = np.exp(z); p /= p.sum(1, keepdims=True)
            return -np.log(p[np.arange(len(labels)), labels] + 1e-12).mean()

        self.T = float(minimize_scalar(nll, bounds=(0.05, 10.0),
                                       method="bounded").x)
        return self

    def prob(self, logits):
        z = np.asarray(logits, float) / self.T
        z = z - z.max(-1, keepdims=True)
        p = np.exp(z)
        return p / p.sum(-1, keepdims=True)


def ece(probs, labels, bins=15):
    """Expected Calibration Error, 15 equal-width confidence bins.
    Reported for every internal classifier per Sec 4.6."""
    probs = np.asarray(probs, float); labels = np.asarray(labels, int)
    conf = probs.max(1); pred = probs.argmax(1); acc = (pred == labels)
    edges = np.linspace(0, 1, bins + 1); e = 0.0
    for i in range(bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.any():
            e += m.mean() * abs(acc[m].mean() - conf[m].mean())
    return float(e)


class MockNLI:
    """Mechanism-level simulator. Parameters (a,b,sigma; fp_rate,fp_lo,fp_hi)
    are MEASURED in E0 on the real NLI, then frozen here, making mock runs a
    faithful power simulation and the pipeline's integration test.
    S1: contradict_conf(k) = clip(a - b*k + N(0,sigma));
    S2: hedged claim flagged with prob fp_rate at conf ~ U(fp_lo, fp_hi)."""

    def __init__(self, a=0.95, b=0.13, sigma=0.06,
                 fp_rate=0.25, fp_lo=0.55, fp_hi=0.85, seed=0):
        self.a, self.b, self.sigma = a, b, sigma
        self.fp_rate, self.fp_lo, self.fp_hi = fp_rate, fp_lo, fp_hi
        self.rng = np.random.default_rng(seed)

    def contradict_conf(self, u, v, dist_hint=1):
        return float(np.clip(self.a - self.b * dist_hint
                             + self.rng.normal(0, self.sigma), 0.02, 0.99))

    def entail_conf(self, u, v, dist_hint=1):
        return float(np.clip(self.rng.beta(20, 2), 0.0, 1.0))

    def hedged_fp(self, force=False):
        if force or self.rng.random() < self.fp_rate:
            return float(self.rng.uniform(self.fp_lo, self.fp_hi))
        return None


class HFNLI:
    """Real backend (requires transformers + GPU; checkpoint pinned per ERS
    G2, calibrated per G3). dist_hint is accepted for interface parity and
    DELIBERATELY IGNORED (leakage guard)."""

    CONTRA_IDX = 0   # set per checkpoint label map at load time; verify!

    def __init__(self, model_name="microsoft/deberta-v3-large-mnli",
                 device="cuda"):
        try:
            from transformers import (AutoTokenizer,
                                      AutoModelForSequenceClassification)
            import torch  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("transformers/torch unavailable; use MockNLI "
                               "for pipeline tests") from e
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = (AutoModelForSequenceClassification
                      .from_pretrained(model_name).to(device).eval())
        self.device = device
        self.scaler = TemperatureScaler()   # fit on MNLI-val logits, freeze

    def _logits(self, u, v):
        import torch
        with torch.no_grad():
            b = self.tok(u, v, return_tensors="pt",
                         truncation=True).to(self.device)
            return self.model(**b).logits.cpu().numpy()[0]

    def contradict_conf(self, u, v, dist_hint=None):
        p = self.scaler.prob(self._logits(u, v)[None])[0]
        return float(p[self.CONTRA_IDX])

    def entail_conf(self, u, v, dist_hint=None):
        p = self.scaler.prob(self._logits(u, v)[None])[0]
        return float(p[-1])  # verify label map at load time

    def hedged_fp(self, force=False):  # real backend: arises naturally
        return None
