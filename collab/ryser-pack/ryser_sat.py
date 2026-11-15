# -*- coding: utf-8 -*-
"""ONE TASK (ryser / refuted): EXACT finite decision via SAT.

Encoding (one-hot):
  X[e,p,v] : edge e uses vertex v in part p.
  W[e,f,p] : edges e,f agree in part p  (W <-> OR_v (X[e,p,v] & X[f,p,v]))
  (1) exactly one vertex per (e,p)
  (2) intersecting: OR_p W[e,f,p]                 -> nu = 1
  (3) distinct    : OR_p (NOT W[e,f,p])           -> |Finset edges| = NE
  (4) degree      : at most D edges per (p,v)     -> tau >= ceil(NE/D)
  (5) NE > (R-1)*D                                -> ceil(NE/D) >= R

SAT  => explicit counterexample (decoded + independently verified)
UNSAT=> theorem: no such hypergraph with these parameters exists.
"""
import sys, json, time, itertools, os
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153


def decide(R, NV, NE, D, timeout=60, verbose=True):
    pool = IDPool()
    def X(e,p,v): return pool.id(('X',e,p,v))
    def Y(e,f,p,v): return pool.id(('Y',e,f,p,v))
    def W(e,f,p): return pool.id(('W',e,f,p))
    cnf = CNF()
    # (1) exactly one per (e,p)
    for e in range(NE):
        for p in range(R):
            lits = [X(e,p,v) for v in range(NV)]
            cnf.extend(CardEnc.equals(lits=lits, bound=1, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
    # degree constraints (4)
    for p in range(R):
        for v in range(NV):
            lits = [X(e,p,v) for e in range(NE)]
            cnf.extend(CardEnc.atmost(lits=lits, bound=D, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
    # W definitions + (2)(3)
    for e in range(NE):
        for f in range(e+1, NE):
            inter, distinct = [], []
            for p in range(R):
                w = W(e,f,p)
                ys = []
                for v in range(NV):
                    y = Y(e,f,p,v)
                    ys.append(y)
                    # y <-> X_e & X_f
                    cnf.append([-y, X(e,p,v)])
                    cnf.append([-y, X(f,p,v)])
                    cnf.append([y, -X(e,p,v), -X(f,p,v)])
                    cnf.append([-y, w])
                # w -> OR y
                cnf.append([-w] + ys)
                inter.append(w)
                distinct.append(-w)
            cnf.append(inter)       # (2) intersecting
            cnf.append(distinct)    # (3) distinct
    # symmetry breaking: e0 = all zeros, and edge 1 has part0 value <= 1
    for p in range(R):
        cnf.append([X(0,p,0)])
        for v in range(1,NV): cnf.append([-X(0,p,v)])
    if verbose:
        print(f'  cnf: vars={pool.top} clauses={len(cnf.clauses)}', flush=True)
    solver = Cadical153(bootstrap_with=cnf.clauses)
    t0=time.time()
    # Cadical no native timeout; use interrupt via conf budget approximations
    res = solver.solve_limited(expect_interrupt=False) if hasattr(solver,'solve_limited') else solver.solve()
    elapsed = time.time()-t0
    if res is None:
        return 'UNKNOWN', None, dict(elapsed=elapsed, vars=pool.top, clauses=len(cnf.clauses))
    if not res:
        solver.delete()
        return 'UNSAT', None, dict(elapsed=elapsed, vars=pool.top, clauses=len(cnf.clauses))
    model = set(l for l in solver.get_model() if l>0)
    solver.delete()
    E=[]
    for e in range(NE):
        row=[]
        for p in range(R):
            v=next(v for v in range(NV) if X(e,p,v) in model)
            row.append(v)
        E.append(row)
    return 'SAT', E, dict(elapsed=elapsed, vars=pool.top, clauses=len(cnf.clauses))


def exact_verify(E, R, NV, D):
    NE=len(E)
    deg={}
    for e in E:
        for p in range(R): deg[(p,e[p])]=deg.get((p,e[p]),0)+1
    dmax=max(deg.values())
    distinct=len(set(map(tuple,E)))==NE
    def meet(a,b): return any(a[p]==b[p] for p in range(R))
    inter=all(meet(E[i],E[j]) for i in range(NE) for j in range(i+1,NE))
    nu=0
    def dfs(used,start,d):
        nonlocal nu
        if d>nu: nu=d
        for i in range(start,NE):
            if all(not meet(E[i],E[j]) for j in used):
                used.append(i); dfs(used,i+1,d+1); used.pop()
    dfs([],0,0)
    # tau by branch&bound (ub = R+2 enough)
    hit={}
    for i,e in enumerate(E):
        for p in range(R):
            hit.setdefault((p,e[p]),0); hit[(p,e[p])]|=1<<i
    ALL=(1<<NE)-1
    best=[R+3,None]
    def rec(chosen,cov,k):
        if k>=best[0]: return
        if cov==ALL: best[0]=k;best[1]=set(chosen);return
        idx=next(i for i in range(NE) if not ((cov>>i)&1))
        e=E[idx]
        vs=[(p,e[p]) for p in range(R) if (p,e[p]) not in chosen]
        scored=sorted(((bin(hit[pv]&~cov).count('1'),pv) for pv in vs),reverse=True)
        for _,pv in scored:
            rec(chosen|{pv},cov|hit[pv],k+1)
            if k+1>=best[0]: break
    rec(set(),0,0)
    tau=best[0]
    return dict(NE=NE,R=R,NV=NV,D=D,dmax=dmax,distinct=distinct,intersecting=inter,
                nu=nu,tau=tau,counting_lower=-(-NE//D),
                ryser_rhs=(R-1)*nu,
                ryser_fails=(tau>(R-1)*nu and nu==1 and distinct and inter),
                min_cover=[list(x) for x in (best[1] or [])])

if __name__=='__main__':
    R=int(sys.argv[1]); NV=int(sys.argv[2]); NE=int(sys.argv[3]); D=int(sys.argv[4])
    out=f'/data/workspace/run_logs/ryser_sat_R{R}_NV{NV}_NE{NE}_D{D}.json'
    print(f'=== SAT decide R={R} NV={NV} NE={NE} D={D} ceil(NE/D)={-(-NE//D)} (R-1)D={(R-1)*D} ===',flush=True)
    res,E,info=decide(R,NV,NE,D)
    print(f'  result={res} elapsed={info["elapsed"]:.1f}s',flush=True)
    rec=dict(params=dict(R=R,NV=NV,NE=NE,D=D),result=res,info=info)
    if E:
        v=exact_verify(E,R,NV,D)
        rec['verify']=v; rec['edges']=E
        print('  VERIFY',{k:x for k,x in v.items() if k!='min_cover'},flush=True)
        if v['ryser_fails']:
            print('  *** COUNTEREXAMPLE FOUND ***',flush=True)
            for i,e in enumerate(E): print(f'   e{i:02d}={e}',flush=True)
            json.dump(rec,open('/data/workspace/run_logs/ryser_SOLVED.json','w'),indent=1)
        else:
            print('  (SAT model verified but does NOT refute Ryser)',flush=True)
    json.dump(rec,open(out,'w'),indent=1)
    print('  saved',out,flush=True)
