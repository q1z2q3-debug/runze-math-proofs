# -*- coding: utf-8 -*-
"""Round 3: build a 0->1 bin-packing integrality-gap finder.
Goal: find an explicit MIRUP counterexample (OPT >= ceil(LP)+2), which by the
official Task/Basic.lean refuted slot DISPROVES the MIRUP conjecture.

Pipeline (self-built, no external solver except scipy linprog/milp installed
from the internal mirror):
  patterns = all item subsets with sum(size) <= L
  LP  = min sum x  s.t. A x >= 1, x >= 0        (fractional cover)
  OPT = min sum x  s.t. A x >= 1, x in Z>=0     (integer cover = bin packing)
  gap = OPT - ceil(LP); MIRUP refuted iff gap >= 2.
Sanity check: official instC must give LP=3, OPT=4.
"""
import itertools, math, random, json, sys, time
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds

def patterns_of(sizes, L):
    n = len(sizes)
    out = []
    idx = list(range(n))
    # enumerate subsets by increasing cardinality, prune on sorted sizes
    for k in range(1, n+1):
        for comb in itertools.combinations(idx, k):
            if sum(sizes[i] for i in comb) <= L:
                out.append(comb)
    return out

def solve(sizes, L, verbose=False):
    pats = patterns_of(sizes, L)
    n, m = len(sizes), len(pats)
    if m == 0: return None
    A = np.zeros((n, m), dtype=float)
    for j,p in enumerate(pats):
        for i in p: A[i,j] = 1.0
    c = np.ones(m)
    cons = LinearConstraint(A, lb=np.ones(n), ub=np.full(n, np.inf))
    lp = linprog(c, A_ub=-A, b_ub=-np.ones(n), bounds=(0,None), method='highs')
    if not lp.success: return None
    LP = float(lp.fun)
    # integer cover
    mi = milp(c=c, integrality=np.ones(m), bounds=Bounds(0, np.inf),
              constraints=cons, options={'time_limit': 20.0})
    if not mi.success: return None
    OPT = int(round(mi.fun))
    ceilLP = math.ceil(LP - 1e-9)
    gap = OPT - ceilLP
    x_lp = lp.x
    x_opt = np.rint(mi.x).astype(int)
    if verbose:
        print(f'  n={n} patterns={m} LP={LP:.6f} ceil={ceilLP} OPT={OPT} gap={gap}')
        print('  nonzero LP patterns:', [(pats[j], round(x_lp[j],4)) for j in range(m) if x_lp[j]>1e-7][:20])
        print('  integer patterns   :', [(pats[j], x_opt[j]) for j in range(m) if x_opt[j]>0][:20])
    return dict(sizes=sizes, L=L, LP=LP, ceilLP=ceilLP, OPT=OPT, gap=gap,
                patterns=pats, x_lp=[float(v) for v in x_lp], x_opt=x_opt.tolist(),
                n=n, m=m)

def certify_rational(sizes, L, sol, D=1000000):
    """From LP solution produce natural-number primal/dual certificates with common denominator D.
       primal: X_j = round(x_j * D), covers each item >= D times, sum X <= ceil(LP*D)+n
       dual: solve LP dual to get w_i, W_i = round(w_i*D), each pattern sum W <= D (+ slack)
       Returns exact integer certificates suitable for lpVal_le_of_natCover / le_lpVal_of_natDual.
    """
    n, m = sol['n'], sol['m']
    pats = sol['patterns']
    x = np.array(sol['x_lp'])
    # primal: scale & round up to guarantee coverage
    X = np.ceil(x * D - 1e-9).astype(np.int64)
    cov = np.zeros(n, dtype=np.int64)
    for j,p in enumerate(pats):
        for i in p: cov[i] += X[j]
    # dual
    A = np.zeros((n,m))
    for j,p in enumerate(pats):
        for i in p: A[i,j]=1
    d = linprog(-np.ones(n), A_ub=A.T, b_ub=np.ones(m), bounds=(0,None), method='highs')
    W = np.floor(d.x * D + 1e-9).astype(np.int64) if d.success else np.zeros(n,dtype=np.int64)
    patW = np.zeros(m, dtype=np.int64)
    for j,p in enumerate(pats):
        patW[j] = sum(W[i] for i in p)
    return dict(D=D, X=X.tolist(), cover_counts=cov.tolist(),
                primal_sum=int(X.sum()), W=W.tolist(), pattern_W_max=int(patW.max()),
                dual_sum=int(W.sum()))

def sanity():
    print('=== SANITY: official instC (Kartak 2015), expect LP=3 OPT=4 gap=1 ===')
    sizes=[4,6,6,9,16,29,32,37,40,62]; L=81
    s=solve(sizes,L,verbose=True)
    print('  PASS?', abs(s['LP']-3)<1e-6 and s['OPT']==4 and s['gap']==1)
    return s

def random_search(iters, seed=20261115):
    rng = random.Random(seed)
    best=None; hist={}
    t0=time.time()
    for it in range(iters):
        L = rng.choice([30,36,40,48,60,72,80,90,100,120])
        # sizes > L/6 (max 5 items/bin), biased toward L/3..L/2
        lo = L//6 + 1
        hi = L - 1
        n = rng.randint(8, 18)
        sizes=[]
        for _ in range(n):
            if rng.random()<0.75:
                sizes.append(rng.randint(max(lo,L//4), max(max(lo,L//4),L//2)))
            else:
                sizes.append(rng.randint(lo, hi))
        sizes=sorted(sizes)
        if sum(sizes) > 6*L:  # keep OPT small
            continue
        sol=solve(sizes,L)
        if sol is None: continue
        g=sol['gap']
        hist[g]=hist.get(g,0)+1
        if g>=2:
            print(f'*** FOUND gap={g} at iter={it}: L={L} sizes={sizes} LP={sol["LP"]:.6f} ceil={sol["ceilLP"]} OPT={sol["OPT"]}')
            solve(sizes,L,verbose=True)
            return sol
        if best is None or g>best['gap']: best=sol
        if it%200==0:
            print(f'  iter={it} elapsed={time.time()-t0:.1f}s best_gap={best["gap"] if best else None} hist={hist}',flush=True)
    print('no gap>=2 found; histogram',hist,'best',best['gap'] if best else None)
    return None

if __name__=='__main__':
    s=sanity()
    iters=int(sys.argv[1]) if len(sys.argv)>1 else 3000
    found=random_search(iters)
    if found:
        cert=certify_rational(found['sizes'],found['L'],found)
        print('\n=== CERTIFICATES ===')
        print('D=',cert['D'])
        print('primal X sum=',cert['primal_sum'],'min cover count=',min(cert['cover_counts']))
        print('dual W sum=',cert['dual_sum'],'max pattern W=',cert['pattern_W_max'])
        json.dump(dict(solution={k:v for k,v in found.items() if k not in ('patterns','x_lp','x_opt')},
                       patterns=found['patterns'],x_lp=found['x_lp'],x_opt=found['x_opt'],
                       certificate=cert),
                  open('/data/workspace/run_logs/mirup_counterexample.json','w'),indent=1)
        print('saved run_logs/mirup_counterexample.json')
