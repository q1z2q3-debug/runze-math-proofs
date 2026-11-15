import random, time, json
import numpy as np
import bpp
from search import pats_fast, gen_families
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix

def evaluate(sizes,L):
    n=len(sizes); pats=pats_fast(sizes,L)
    A=np.zeros((n,len(pats)))
    for j,m in enumerate(pats):
        for i in range(n):
            if m>>i&1: A[i,j]=1.0
    from scipy.optimize import linprog
    r=linprog(np.ones(len(pats)),A_ub=-A,b_ub=-np.ones(n),bounds=[(0,None)]*len(pats),method="highs")
    if r.status!=0: return None
    m=milp(np.ones(len(pats)),constraints=LinearConstraint(csr_matrix(A),lb=np.ones(n),ub=np.inf),
           integrality=np.ones(len(pats)),bounds=Bounds(0,np.inf),
           options={"time_limit":10,"mip_rel_gap":0})
    if m.status!=0: return None
    return r.fun, round(m.fun)

dist={}; rec=[]; cnt=0; t0=time.time()
for sizes,L in gen_families():
    if cnt>=2500 or time.time()-t0>600: break
    try: out=evaluate(sizes,L)
    except Exception: continue
    if out is None: continue
    lp,opt=out; cnt+=1
    gap=opt-int(np.ceil(lp-1e-7))
    dist[gap]=dist.get(gap,0)+1
    if gap>=1: rec.append({"sizes":sizes,"L":L,"lp":round(lp,6),"opt":opt,"gap":gap})
print("n=",cnt,"dist OPT-ceil(LP):",dist)
json.dump({"count":cnt,"dist":dist,"examples_gap1":rec[:12]},open("gap_stats.json","w"),indent=1)
