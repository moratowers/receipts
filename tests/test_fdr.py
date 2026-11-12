"""The audit's two hand-coded implementations of its multiple-testing procedures, checked three ways:
against the worked example in Benjamini and Hochberg (1995), against each other, and against statsmodels."""
import random

import numpy as np
import pytest
from statsmodels.stats.multitest import multipletests

from fdr import builder_impl as B
from fdr import checker_impl as C

# Benjamini and Hochberg (1995), section 4.1: the 15 p-values of the worked example.
BH1995 = [0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298, 0.0344, 0.0459, 0.3240, 0.4262, 0.5719,
          0.6528, 0.7590, 1.000]
BH1995_ADJ = [0.0015, 0.003, 0.0095, 0.035625, 0.0603, 0.063857, 0.063857, 0.0645, 0.0765, 0.486, 0.581182,
              0.714875, 0.753231, 0.813214, 1.0]
BY_ON_BH1995_ADJ = [0.004977, 0.009955, 0.031523, 0.118212, 0.200089, 0.211893, 0.211893, 0.214026, 0.253845] + [1.0] * 6


@pytest.mark.parametrize("impl", [B, C], ids=["builder", "checker"])
def test_bh_worked_example(impl):
    rej05, adj = impl.bh(BH1995, 0.05)
    rej10, _ = impl.bh(BH1995, 0.10)
    assert rej05 == [True] * 4 + [False] * 11
    assert rej10 == [True] * 9 + [False] * 6
    assert [round(x, 6) for x in adj] == BH1995_ADJ


@pytest.mark.parametrize("impl", [B, C], ids=["builder", "checker"])
def test_by_worked_example(impl):
    assert round(impl.harmonic(15), 6) == 3.318229
    rej05, adj = impl.by(BH1995, 0.05)
    rej10, _ = impl.by(BH1995, 0.10)
    assert sum(rej05) == 3 and sum(rej10) == 3
    assert [round(x, 6) for x in adj] == BY_ON_BH1995_ADJ


def test_hierarchical_worked_example_both():
    fam = ["A"] * 5 + ["B"] * 10
    fp_b, fr_b, lr_b = B.hierarchical(BH1995, fam, 0.10, families=("A", "B"))
    lanes = [f"l{i}" for i in range(15)]
    fp_c, fr_c, lr_c = C.hierarchical(dict(zip(lanes, BH1995)), {"A": lanes[:5], "B": lanes[5:]}, 0.10)
    assert fr_b == fr_c == {"A": True, "B": False}
    assert lr_b == [lr_c[x] for x in lanes] == [True] * 5 + [False] * 10
    assert round(fp_b["A"], 6) == round(fp_c["A"], 6) == 0.0005
    assert round(fp_b["B"], 6) == round(fp_c["B"], 6) == 0.114667


def test_storey_worked_example_both():
    s = B.storey(BH1995, lam=0.5, b=2000, seed=20261017)
    n_above, pi0, e = C.storey(BH1995, 0.5)
    assert s["N_above"] == n_above == 4
    assert s["pi0_hat"] == pi0 and round(pi0, 6) == 0.533333
    assert s["E"] == pytest.approx(e, abs=1e-12)
    lo, hi, e_lo, e_hi = C.storey_resample(BH1995, B=2000, seed=20261017, lam=0.5)
    assert s["pi0_spread"] == [lo, hi]
    assert s["E_spread"] == [e_lo, e_hi]


def _random_vectors(n_vectors=2000, seed=1):
    rng = random.Random(seed)
    for _ in range(n_vectors):
        m = rng.randint(1, 80)
        share_signal = rng.random()
        p = []
        for _ in range(m):
            if rng.random() < share_signal:
                p.append(rng.random() ** 6)                 # pulled toward 0, like real effects
            else:
                p.append(rng.random())
        if rng.random() < 0.2 and m > 1:                     # ties
            p[rng.randrange(m)] = p[0]
        if rng.random() < 0.1:                               # exact ones, as untested entries are padded
            p[rng.randrange(m)] = 1.0
        yield p


@pytest.mark.parametrize("q", [0.05, 0.10])
def test_bh_and_by_agree_with_each_other_and_statsmodels(q):
    for p in _random_vectors():
        rb, ab = B.bh(p, q)
        rc, ac = C.bh(p, q)
        rs, as_, _, _ = multipletests(p, alpha=q, method="fdr_bh")
        assert rb == rc == list(rs)
        assert np.allclose(ab, ac, rtol=0, atol=1e-12)
        assert np.allclose(ab, as_, rtol=0, atol=1e-12)

        rb, ab = B.by(p, q)
        rc, ac = C.by(p, q)
        rs, as_, _, _ = multipletests(p, alpha=q, method="fdr_by")
        assert rb == rc == list(rs)
        assert np.allclose(ab, ac, rtol=0, atol=1e-12)
        assert np.allclose(ab, as_, rtol=0, atol=1e-12)


def test_checker_padding_equals_padding_the_vector():
    """The checker takes m larger than the number of p-values (untested entries at p = 1); the builder pads."""
    for p in _random_vectors(500, seed=2):
        m = len(p) + 7
        rc, ac = C.bh(p, 0.10, m=m)
        rb, ab = B.bh(B.padded(p, m), 0.10)
        assert rc == rb[:len(p)]
        assert np.allclose(ac, ab[:len(p)], rtol=0, atol=1e-12)


def test_hierarchical_agrees_on_random_families():
    rng = random.Random(3)
    fams = ("F1", "F2", "F3", "F4", "F5")
    for p in _random_vectors(500, seed=4):
        fam = [rng.choice(fams) for _ in p]
        used = tuple(f for f in fams if f in fam)
        fp_b, fr_b, lr_b = B.hierarchical(p, fam, 0.10, families=used)
        lanes = [f"l{i}" for i in range(len(p))]
        groups = {f: [x for x, g in zip(lanes, fam) if g == f] for f in used}
        fp_c, fr_c, lr_c = C.hierarchical(dict(zip(lanes, p)), groups, 0.10)
        assert fr_b == fr_c
        assert lr_b == [lr_c[x] for x in lanes]
        for f in used:
            assert fp_b[f] == pytest.approx(fp_c[f], abs=1e-12)


def test_bh_rejects_at_the_exact_threshold():
    """A p-value equal to its step-up bound j q / m is rejected (<=, not <)."""
    for impl in (B, C):
        assert impl.bh([0.025, 0.05], 0.05)[0] == [True, True]
    assert list(multipletests([0.025, 0.05], alpha=0.05, method="fdr_bh")[0]) == [True, True]


def test_storey_does_not_count_p_equal_to_lambda():
    """Storey counts p strictly above lambda."""
    p = [0.5, 0.5, 0.1, 0.9]
    assert B.storey(p, b=10)["N_above"] == 1
    assert C.storey(p)[0] == 1
