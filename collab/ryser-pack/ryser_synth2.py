# -*- coding: utf-8 -*-
"""Round 3 core, v3: DIRECT finite synthesis of a Ryser counterexample.

Key mathematical simplification found this round (double counting):
  If H is r-partite, |E| edges, and EVERY vertex lies in at most D edges,
  then any vertex cover C hits at most |C|*D edges, so
      tau(H) >= ceil(|E|/D).
  If additionally nu(H)=1 (all edges pairwise intersecting) and
      |E| > (r-1)*D,
  then tau >= ceil(|E|/D) >= r > (r-1)*nu, i.e. RyserBound FAILS.

This turns the problem into a FINITE CSP with no quantifier alternation:
  variables a[e][p] in Fin NV  (vertex label of edge e in part p)
  (1) any two edges agree in some part   -> nu = 1
  (2) distinct transversals
  (3) degree of every (part,vertex) <= D
  (4) |E| > (r-1)*D  (fixed by parameters)
Then tau >= r is a 3-line counting argument, easy to formalize in Lean.

Everything below is built from scratch with z3 (installed from the internal
mirror). No Lean binary is available in this sandbox; the final .lean file is
a specification + full proof skeleton, explicitly marked NOT COMPILED.
"""
import itertools, json, sys, time
from z3 import *

def synth(r, NV, NE, D, time_limit=120, seed=0):
    """returns explicit edge table or None"""
    A = [[Int(f'a_{e}_{p}') for p in range(r)] for e in range(NE)]
    s = Solver()
    s.set('timeout', time_limit*1000)
    for e in range(NE):
        for p in range(r):
            s.add(A[e][p] >= 0, A[e][p] < NV)
    # (1)+(2): pairwise intersecting AND distinct
    for e in range(NE):
        for f in range(e+1, NE):
            s.add(Or([A[e][p] == A[f][p] for p in range(r)]))
            s.add(Or([A[e][p] != A[f][p] for p in range(r)]))
    # (3): bounded degree, so tau >= ceil(NE/D)
    for p in range(r):
        for v in range(NV):
            s.add(Sum([If(A[e][p] == v, 1, 0) for e in range(NE)]) <= D)
    # symmetry breaking: first edge = all zeros (WLOG relabel part-vertices)
    for p in range(r): s.add(A[0][p] == 0)
    t0 = time.time()
    res = s.check()
    if res != sat:
        return None, f'{res} in {time.time()-t0:.1f}s'
    m = s.model()
    edges = [tuple(m.eval(A[e][p]).as_long() for p in range(r)) for e in range(NE)]
    return edges, f' sat in {time.time()-t0:.1f}s'

def verify(edges, r, NV, D):
    NE = len(edges)
    # degrees
    deg = {}
    for e in edges:
        for p in range(r):
            deg[(p,e[p])] = deg.get((p,e[p]),0)+1
    dmax = max(deg.values())
    # nu = 1?
    def meet(e,f): return any(e[p]==f[p] for p in range(r))
    nu1 = all(meet(edges[i],edges[j]) for i in range(NE) for j in range(i+1,NE))
    # exact tau (branch and bound)
    hit = {}
    for i,e in enumerate(edges):
        for p in range(r):
            hit.setdefault((p,e[p]),0); hit[(p,e[p])] |= 1<<i
    ALL=(1<<NE)-1
    best=[r+3,None]
    def rec(chosen,cov,k):
        if k>=best[0]: return
        if cov==ALL: best[0]=k;best[1]=set(chosen);return
        idx=next(i for i in range(NE) if not ((cov>>i)&1))
        e=edges[idx]
        vs=[(p,e[p]) for p in range(r) if (p,e[p]) not in chosen]
        scored=sorted(((bin(hit[pv]&~cov).count('1'),pv) for pv in vs),reverse=True)
        for _,pv in scored:
            rec(chosen|{pv},cov|hit[pv],k+1)
            if k+1>=best[0]: break
    rec(set(),0,0)
    tau=best[0]
    return dict(NE=NE, dmax=dmax, nu1=nu1, tau=tau,
                counting_bound=-(-NE//D), bound=(r-1)*1,
                ryser_fails=(tau > (r-1)*1 and nu1),
                min_cover=[list(x) for x in (best[1] or [])])

def scan():
    print('=== direct synthesis scan (r=6, NV=7 or 8) ===', flush=True)
    trials = [
        (6,7,26,5),(6,7,31,6),(6,7,32,6),(6,7,36,6),
        (6,8,26,5),(6,8,31,6),(6,8,36,6),(6,8,37,6),
        (6,8,41,7),(6,9,31,6),(6,9,36,6),
        (7,8,37,6),(8,9,50,7),
    ]
    for r,NV,NE,D in trials:
        if NE <= (r-1)*D: continue
        t0=time.time()
        try:
            edges,msg = synth(r,NV,NE,D,time_limit=90)
        except Exception as ex:
            print(f' r={r} NV={NV} NE={NE} D={D}: EXC {ex}'); continue
        print(f' r={r} NV={NV} NE={NE} D={D} ceil(NE/D)={-(-NE//D)} (r-1)D={(r-1)*D}: {msg}',flush=True)
        if edges:
            v=verify(edges,r,NV,D)
            print('   VERIFY',v,flush=True)
            if v['ryser_fails']:
                out=dict(r=r,NV=NV,NE=NE,D=D,edges=[list(e) for e in edges],verify=v)
                json.dump(out,open('/data/workspace/run_logs/ryser_counterexample.json','w'),indent=1)
                print('   *** SAVED run_logs/ryser_counterexample.json ***',flush=True)
                return out
    return None

if __name__=='__main__':
    out=scan()
    if out is None:
        json.dump(dict(success=False),open('/data/workspace/run_logs/ryser_synth2_result.json','w'))
