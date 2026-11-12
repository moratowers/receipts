"""Multiple-testing procedures from the audit's independent CHECKER program, copied verbatim.

Source: check_program_audit.py, sha256 b1eb36229a4e4fae954866aa2e07645174e3ee19f1d33a1c38733caa6c8e3944
(the sha256 recorded in the checker's passing run), last changed in commit eed0c78c (2026-10-23T23:47:21Z).
The constant lines are its lines 147 and 149-150; the functions are its lines 586-672, unchanged.
Only this docstring, the import lines and blank lines were added. The checker was written by a different agent from the
builder, from the frozen plan's text; by its author's record it never opened the builder's code.
"""
import math

import numpy as np

LAMBDA = 0.5             # 4.4
B_RESAMPLE = 10000       # 4.4
SEED = 20261017          # 4.4


def bh(p, q: float, m: int | None = None):
    """Benjamini-Hochberg step-up (4.1), hand-coded. p in any order; m >= len(p) adds untested entries at p = 1 (4.5,
    BH is monotone so they never rank ahead of a value below 1). Returns (reject list, adjusted p list), original
    order. Adjusted p(i) = min over j >= i of min(1, m p_(j) / j)."""
    p = [float(x) for x in p]
    n = len(p)
    m = n if m is None else int(m)
    if m < n:
        raise ValueError("m must be at least the number of p-values")
    order = sorted(range(n), key=lambda i: (p[i], i))
    k_max = 0
    for rank, i in enumerate(order, start=1):
        if p[i] <= rank * q / m:
            k_max = rank
    reject = [False] * n
    for rank, i in enumerate(order, start=1):
        if rank <= k_max:
            reject[i] = True
    adj = [1.0] * n
    running = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        running = min(running, min(1.0, m * p[i] / rank))
        adj[i] = running
    return reject, adj


def harmonic(m: int) -> float:
    return math.fsum(1.0 / i for i in range(1, m + 1))


def by(p, q: float, m: int | None = None):
    """Benjamini-Yekutieli (4.2): the BH step-up at q / c(m), adjusted p = min(1, c(m) x BH-adjusted p)."""
    n = len(p)
    m = n if m is None else int(m)
    c = harmonic(m)
    reject, _ = bh(p, q / c, m)
    _, adj_bh = bh(p, q, m)
    return reject, [min(1.0, c * a) for a in adj_bh]


def simes(p) -> float:
    """min over i of n p_(i) / i (4.3 step 1), which equals the family's smallest BH-adjusted p."""
    s = sorted(float(x) for x in p)
    n = len(s)
    return min(n * s[i - 1] / i for i in range(1, n + 1))


def hierarchical(p_by_lane: dict, families: dict, q: float):
    """Yekutieli (2008) two-level procedure (4.3): Simes per family, BH at q over the family p-values, then BH at q
    inside each family rejected at level 1. Returns (family_p, family_reject, lane_reject)."""
    fams = list(families)
    fam_p = {f: simes([p_by_lane[x] for x in families[f]]) for f in fams}
    rej1, _ = bh([fam_p[f] for f in fams], q)
    fam_rej = dict(zip(fams, rej1))
    lane_rej = {}
    for f in fams:
        members = families[f]
        if fam_rej[f]:
            r, _ = bh([p_by_lane[x] for x in members], q)
            lane_rej.update(zip(members, r))
        else:
            lane_rej.update({x: False for x in members})
    return fam_p, fam_rej, lane_rej


def storey(p, lam: float = LAMBDA):
    """Storey (2002) at one lambda (4.4): N_above = #{p > lam}, pi0 = min(1, N_above / (m (1 - lam))), E = m (1 - pi0)."""
    m = len(p)
    n_above = sum(1 for x in p if x > lam)
    pi0 = min(1.0, n_above / (m * (1.0 - lam)))
    return n_above, pi0, m * (1.0 - pi0)


def storey_resample(p, B: int = B_RESAMPLE, seed: int = SEED, lam: float = LAMBDA):
    """4.4 resampling spread, exactly as written: rng = default_rng(seed); idx = rng.integers(0, m, size=(B, m)) in one
    call; pi0*_b = min(1, sum(p[idx[b]] > lam) / (m (1 - lam))); numpy.quantile(.., [0.025, 0.975]) (default linear);
    E spread = [m (1 - hi), m (1 - lo)]. Not a confidence interval."""
    pa = np.asarray(p, dtype=float)
    m = pa.size
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, m, size=(B, m))
    pi0_star = np.minimum(1.0, (pa[idx] > lam).sum(axis=1) / (m * (1.0 - lam)))
    lo, hi = np.quantile(pi0_star, [0.025, 0.975])
    return float(lo), float(hi), float(m * (1.0 - hi)), float(m * (1.0 - lo))


