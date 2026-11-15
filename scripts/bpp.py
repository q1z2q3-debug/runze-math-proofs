"""Exact bin-packing toolkit: configuration LP value and integer optimum.

Conventions follow the TCSExam MIRUP task: instance = positive integer sizes
l_i <= L; a pattern is a subset of item copies with total size <= L; the
configuration LP minimizes total fractional pattern weight subject to
covering every item at least once; OPT = minimum number of bins.
"""
from fractions import Fraction
from itertools import combinations
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix


def enumerate_patterns(sizes, L, max_items=None):
    n = len(sizes)
    pats = []
    by = {i: [] for i in range(n)}
    if max_items is None or max_items >= 1:
        for m in range(1 << n):
            s = 0
            k = 0
            for i in range(n):
                if m >> i & 1:
                    s += sizes[i]; k += 1
            if s <= L and k >= 1 and (max_items is None or k <= max_items):
                pats.append((m, s, k))
    idx = np.array([p[0] for p in pats], dtype=np.int64)
    return pats


def build_matrices(sizes, L, max_items=None):
    n = len(sizes)
    pats = enumerate_patterns(sizes, L, max_items)
    A = np.zeros((n, len(pats)), dtype=np.float64)
    for j, (m, s, k) in enumerate(pats):
        for i in range(n):
            if m >> i & 1:
                A[i, j] = 1.0
    return pats, A


def lp_value(sizes, L, max_items=None, pats_A=None):
    n = len(sizes)
    pats, A = pats_A if pats_A is not None else build_matrices(sizes, L, max_items)
    c = np.ones(len(pats))
    res = linprog(c, A_ub=-A, b_ub=-np.ones(n),
                  bounds=[(0, None)] * len(pats), method="highs")
    assert res.status == 0, res.message
    return res.fun, res.x, pats


def opt_value(sizes, L, max_items=None, pats_A=None, time_limit=60.0):
    n = len(sizes)
    pats, A = pats_A if pats_A is not None else build_matrices(sizes, L, max_items)
    milp_c = np.ones(len(pats))
    integrality = np.ones(len(pats))
    constraints = LinearConstraint(csr_matrix(A), lb=np.ones(n), ub=np.inf)
    res = milp(milp_c, constraints=constraints, integrality=integrality,
               bounds=Bounds(0, np.inf), options={"time_limit": time_limit, "mip_rel_gap": 0})
    if res.status != 0:
        return None, res
    return round(res.fun), res


def exact_lp_fraction(sizes, L, cover_weights=None):
    """Exact rational LP via simplex on the *dual*:
       max sum w_i  s.t.  sum_{i in p} w_i <= 1 for every pattern p, w_i >= 0.
    Implemented with Fraction simplex (dense). Returns Fraction value."""
    pats, A = build_matrices(sizes, L)
    n = len(sizes)
    # dual: maximize sum w  subject to A^T w <= 1, w >= 0
    # standard form: maximize c^T x with A x <= b  -> use tableau simplex
    m = len(pats); nv = n
    Ad = [[Fraction(int(A[i, j])) for i in range(nv)] for j in range(m)]
    bd = [Fraction(1)] * m
    cd = [Fraction(1)] * nv
    return _simplex_max(Ad, bd, cd)


def _simplex_max(A, b, c):
    """Maximize c^T x s.t. A x <= b, x >= 0 (A,b,c over Fraction). Two-phase simplex."""
    m = len(A); n = len(c)
    N = n + m
    # tableau rows: m+1, cols: N+1 (last = rhs)
    T = [[Fraction(0)] * (N + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            T[i][j] = A[i][j]
        T[i][n + i] = Fraction(1)
        T[i][N] = b[i]
    for j in range(n):
        T[m][j] = -c[j]
    # basis
    basis = [n + i for i in range(m)]
    # phase 1 if any b < 0
    if any(x < 0 for x in b):
        # multiply negative rows by -1 and use artificial vars; here b>=1>0 so skip
        raise ValueError("phase-1 needed")
    while True:
        # choose entering col with most negative reduced cost in objective row
        piv = None; best = Fraction(0)
        for j in range(N):
            if T[m][j] < best:
                best = T[m][j]; piv = j
        if piv is None:
            break
        # ratio test
        row = None; rbest = None
        for i in range(m):
            if T[i][piv] > 0:
                r = T[i][N] / T[i][piv]
                if rbest is None or r < rbest:
                    rbest = r; row = i
        if row is None:
            raise ValueError("unbounded")
        # pivot
        pv = T[row][piv]
        for j in range(N + 1):
            T[row][j] /= pv
        for i in range(m + 1):
            if i != row and T[i][piv] != 0:
                f = T[i][piv]
                for j in range(N + 1):
                    T[i][j] -= f * T[row][j]
        basis[row] = piv
    x = [Fraction(0)] * N
    for i, bi in enumerate(basis):
        x[bi] = T[i][N]
    val = sum(c[j] * x[j] for j in range(n))
    return val, x[:n]


def cert_natcover(sizes, L, x_float, pats=None):
    """Turn a fractional cover into an integer certificate X/D (D=denominator)
    and verify it exactly."""
    n = len(sizes)
    pats = pats or enumerate_patterns(sizes, L)
    fr = [Fraction(v).limit_denominator(10 ** 6) for v in x_float]
    D = 1
    for f in fr:
        D = D * f.denominator // np.gcd(D, f.denominator)
    X = [int(f * D) for f in fr]
    ok = True
    for i in range(n):
        cov = sum(X[j] for j, (m, s, k) in enumerate(pats) if m >> i & 1)
        if cov < D:
            ok = False
    return ok, X, D, sum(X)


def volume(sizes, L):
    return Fraction(sum(sizes), L)


if __name__ == "__main__":
    instC = ([4, 6, 6, 9, 16, 29, 32, 37, 40, 62], 81)
    l, L = instC
    pats, A = build_matrices(l, L)
    print("patterns:", len(pats), "volume:", volume(l, L))
    lp, x, _ = lp_value(l, L, pats_A=(pats, A))
    print("LP (float):", lp)
    opt, res = opt_value(l, L, pats_A=(pats, A))
    print("OPT (MILP):", opt)
    print("ceil(LP)+1 =", int(np.ceil(lp-1e-9))+1)
