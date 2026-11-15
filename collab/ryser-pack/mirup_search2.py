# -*- coding: utf-8 -*-
"""Round 3 (MIRUP branch): 0->1 structured search for an explicit counterexample
to the Modified Integer Round-Up Property (MIRUP), i.e. TCSExam
`bin-packing-mirup` refuted slot.

Instance = multiset of item sizes (integer) with capacity L.
patterns = all type-count vectors (c_t) with sum(c_t * size_t) <= L.
LP  = min sum x  s.t. A x >= n, x >= 0 rational     (Gilmore-Gomory config LP)
OPT = min sum x  s.t. A x >= n, x in Z >= 0         (integer bin packing)
MIRUP says OPT <= ceil(LP)+1.  A refutation needs OPT >= ceil(LP)+2.

We search over structured multisets (few distinct sizes, small multiplicities),
which is where configuration-LP integrality gaps live.  All arithmetic for the
final answer is re-certified with EXACT integer primal/dual certificates
(natCover / natDual in the official Basic.lean).
"""
import itertools, math, random, json, sys, time
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds

def patterns_of(sizes, L, counts):
    k=len(sizes); out=[]
    def rec(t, cs, total):
        if t==k:
            if any(c>0 for c in cs): out.append(tuple(cs))
            return
        for c in range(counts[t]+1):
            if total + c*sizes[t] <= L:
                rec(t+1, cs+[c], total+c*sizes[t])
            else: break
    rec(0,[],0)
    return out

def evaluate(sizes, L, counts, want_cert=False):
    pats=patterns_of(sizes,L,counts)
    k=len(sizes); m=len(pats)
    if m==0: return None
    A=np.array([[p[t] for p in pats] for t in range(k)],dtype=float)
    n=np.array(counts,dtype=float)
    c=np.ones(m)
    lp=linprog(c,A_ub=-A,b_ub=-n,bounds=(0,None),method='highs')
    if not lp.success: return None
    LP=float(lp.fun)
    mi=milp(c=c,integrality=np.ones(m),bounds=Bounds(0,np.inf),
            constraints=LinearConstraint(A,lb=n,ub=np.full(k,np.inf)),
            options={'time_limit':8.0,'mip_rel_gap':0.0})
    if not mi.success: return None
    OPT=int(round(mi.fun))
    ceilLP=math.ceil(LP-1e-8)
    gap=OPT-ceilLP
    res=dict(sizes=sizes,L=L,counts=counts,LP=LP,ceilLP=ceilLP,OPT=OPT,gap=gap,
             m=m,pats=pats,x_lp=lp.x.tolist(),x_opt=np.rint(mi.x).astype(int).tolist())
    if want_cert and gap>=2:
        res['cert']=exact_certificate(res)
    return res

def exact_certificate(res):
    """Exact integer primal/dual certificates with common denominator D.
       primal X: rounds LP solution UP to guarantee A X >= n*D.
       dual   W: solves LP dual, rounds DOWN to guarantee A^T W <= D*1.
       Both side conditions are plain Nat inequalities -> kernel `decide`.
    """
    sizes,L,counts=res['sizes'],res['L'],res['counts']
    pats=res['pats']; k=len(sizes); m=len(pats)
    A=np.array([[p[t] for p in pats] for t in range(k)],dtype=float)
    n=np.array(counts,dtype=float)
    D=10**6
    X=np.ceil(np.array(res['x_lp'])*D-1e-9).astype(np.int64)
    AX=(A@X.astype(float)).astype(np.int64)
    # dual: max sum w s.t. A^T w <= 1, w>=0
    d=linprog(-np.ones(k),A_ub=A.T,b_ub=np.ones(m),bounds=(0,None),method='highs')
    W=np.floor(d.x*D+1e-9).astype(np.int64) if d.success else np.zeros(k,dtype=np.int64)
    ATW=(A.T@W.astype(float)).astype(np.int64)
    return dict(D=D,X=X.tolist(),AX=AX.tolist(),primal_sum=int(X.sum()),
                W=W.tolist(),ATW_max=int(ATW.max()),dual_sum=int(W.sum()),
                primal_ok=bool((AX>=counts*D).all()),dual_ok=bool((ATW<=D).all()))

def search(iters,seed=20261115):
    rng=random.Random(seed); hist={}; best=None; t0=time.time(); evals=0
    for it in range(iters):
        L=rng.choice([12,15,18,20,24,30,36,40,48,60])
        k=rng.choice([2,3,3,4])
        # bias sizes into bands that force at most 2/3/4 items per bin
        band=rng.choice(['third','quarter','fifth','mixed'])
        sizes=set()
        while len(sizes)<k:
            if band=='third':   s=rng.randint(L//3+1, max(L//3+1,L//2))
            elif band=='quarter': s=rng.randint(L//4+1, max(L//4+1,L//3))
            elif band=='fifth':  s=rng.randint(L//5+1, max(L//5+1,L//4))
            else: s=rng.randint(max(1,L//6+1), L-1)
            sizes.add(s)
        sizes=sorted(sizes)
        # multiplicities
        counts=[rng.randint(1,7) for _ in range(k)]
        if sum(c*s for c,s in zip(counts,sizes)) > 8*L: continue
        res=evaluate(sizes,L,counts)
        if res is None: continue
        evals+=1
        g=res['gap']; hist[g]=hist.get(g,0)+1
        if g>=2:
            print(f'*** FOUND gap={g} iter={it} L={L} sizes={sizes} counts={counts} '
                  f'LP={res["LP"]:.6f} ceil={res["ceilLP"]} OPT={res["OPT"]}',flush=True)
            res['cert']=exact_certificate(res)
            return res
        if best is None or g>best['gap'] or (g==best['gap'] and res['LP']<best['LP']):
            best=res
        if it%500==0:
            print(f'  it={it} evals={evals} t={time.time()-t0:.1f}s best_gap={best["gap"] if best else None} hist={hist}',flush=True)
    print(f'done iters={iters} evals={evals} hist={hist} best_gap={best["gap"] if best else None}')
    return None

if __name__=='__main__':
    iters=int(sys.argv[1]) if len(sys.argv)>1 else 4000
    found=search(iters)
    if found:
        out={k:v for k,v in found.items() if k!='x_lp'}
        json.dump(out,open('/data/workspace/run_logs/mirup_counterexample.json','w'),indent=1)
        print('saved run_logs/mirup_counterexample.json')
        print('cert:',json.dumps(found['cert'],indent=1)[:1500])
    else:
        json.dump(dict(success=False),open('/data/workspace/run_logs/mirup_search2.json','w'))
