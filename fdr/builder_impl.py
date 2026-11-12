"""Multiple-testing procedures from the audit's BUILDER program, copied verbatim.

Source: build_gold_program_audit.py, sha256 ad8d6fec6fe7ccedc24a81d06ee19d73a4de0166510629c8a052d5dc52de781a
(the sha256 recorded in the audit result's sidecar), last changed in commit ab712e65 (2026-10-24T00:11:29Z).
The constant lines are its lines 74-76 and 472; the functions are its lines 1040-1111, unchanged.
Only this docstring, the import lines and blank lines were added. The rest of that program reads private research data
and is not published.
"""
import math

import numpy as np

LAMBDA = 0.5                    # 4.4
BOOT_B = 10000                  # 4.4
SEED = 20261017                 # 4.4

FAMILIES = ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10")


def bh(p: list[float], q: float) -> tuple[list[bool], list[float]]:
    """Benjamini-Hochberg step-up at q over len(p) values; (rejections, adjusted p), original order."""
    n = len(p)
    order = sorted(range(n), key=lambda i: (p[i], i))
    k = 0
    for j, i in enumerate(order, 1):
        if p[i] <= j * q / n:
            k = j
    rej = [False] * n
    for i in order[:k]:
        rej[i] = True
    adj, run = [0.0] * n, 1.0
    for j in range(n, 0, -1):
        i = order[j - 1]
        run = min(run, n * p[i] / j)
        adj[i] = min(1.0, run)
    return rej, adj


def harmonic(m: int) -> float:
    return math.fsum(1.0 / i for i in range(1, m + 1))


def by(p: list[float], q: float) -> tuple[list[bool], list[float]]:
    """Benjamini-Yekutieli: BH at q / c(m); adjusted p = min(1, c(m) x BH-adjusted p)."""
    c = harmonic(len(p))
    rej, _ = bh(p, q / c)
    _, adj = bh(p, q)
    return rej, [min(1.0, c * a) for a in adj]


def simes(p: list[float]) -> float:
    s = sorted(p)
    n = len(s)
    return min(1.0, min(n * s[i] / (i + 1) for i in range(n)))


def hierarchical(p: list[float], fam: list[str], q: float, families=FAMILIES):
    """Yekutieli (2008), two levels: (family Simes p, family rejected, lane rejected), per family and per lane."""
    members = {f: [i for i, x in enumerate(fam) if x == f] for f in families}
    fam_p = [simes([p[i] for i in members[f]]) for f in families]
    f_rej, _ = bh(fam_p, q)
    lane_rej = [False] * len(p)
    for f, ok in zip(families, f_rej):
        if ok:
            r, _ = bh([p[i] for i in members[f]], q)
            for i, x in zip(members[f], r):
                lane_rej[i] = x
    return dict(zip(families, fam_p)), dict(zip(families, f_rej)), lane_rej


def storey(p: list[float], lam: float = LAMBDA, b: int = BOOT_B, seed: int = SEED) -> dict:
    """pi0-hat = min(1, #{p > lam} / ((1 - lam) m)), E = m (1 - pi0-hat), and the resampling spread (4.4)."""
    m = len(p)
    arr = np.asarray(p, dtype=float)
    n_above = int(np.sum(arr > lam))
    pi0 = min(1.0, n_above / ((1.0 - lam) * m))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, m, size=(b, m))
    pi0_star = np.minimum(1.0, np.sum(arr[idx] > lam, axis=1) / ((1.0 - lam) * m))
    lo, hi = (float(x) for x in np.quantile(pi0_star, [0.025, 0.975]))
    return {"m_p": m, "N_above": n_above, "pi0_hat": pi0, "E": m * (1.0 - pi0),
            "pi0_spread": [lo, hi], "E_spread": [m * (1.0 - hi), m * (1.0 - lo)],
            "spread_label": "resampling spread of the estimator, not a confidence interval",
            "note": "E = 0 does not mean the program holds no true edge; pi0-hat and E are fixed by N_above"}


def padded(p: list[float], m_total: int) -> list[float]:
    """The 53 p-values plus m_total - 53 extra trials at p = 1, least favourable to the 53 (4.5)."""
    return list(p) + [1.0] * (m_total - len(p))


