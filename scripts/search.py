"""Search for small MIRUP-violating instances: OPT >= ceil(LP) + 2."""
import random, time, json, sys
import numpy as np
from fractions import Fraction
import bpp

def subset_sums(sizes):
    n=len(sizes); s=np.zeros(1<<n,dtype=np.int64)
    for m in range(1,1<<n):
        lb = m & -m; i = lb.bit_length()-1
        s[m]=s[m^lb]+sizes[i]
    return s

def pats_fast(sizes,L):
    n=len(sizes); s=subset_sums(sizes)
    masks=np.nonzero((s<=L)&(s>0))[0]
    cnt=np.zeros(len(masks),dtype=np.int64)
    for k in range(n):
        cnt+=((masks>>k)&1)
    return masks.tolist()

def evaluate(sizes,L):
    n=len(sizes)
    pats=pats_fast(sizes,L)
    A=np.zeros((n,len(pats)))
    for j,m in enumerate(pats):
        for i in range(n):
            if m>>i&1: A[i,j]=1.0
    from scipy.optimize import linprog,milp,LinearConstraint,Bounds
    from scipy.sparse import csr_matrix
    res=linprog(np.ones(len(pats)),A_ub=-A,b_ub=-np.ones(n),bounds=[(0,None)]*len(pats),method="highs")
    if res.status!=0: return None
    lp=res.fun
    m=milp(np.ones(len(pats)),constraints=LinearConstraint(csr_matrix(A),lb=np.ones(n),ub=np.inf),
           integrality=np.ones(len(pats)),bounds=Bounds(0,np.inf),
           options={"time_limit":20,"mip_rel_gap":0})
    if m.status!=0: return None
    return lp, round(m.fun)

def gen_families():
    rnd=random.Random(20261115)
    base=[4,6,6,9,16,29,32,37,40,62]
    # Family A: scaled instC + perturbations / extra small items
    for scale in (1,2,3,4,6,8):
        for trial in range(400):
            L=81*scale
            sz=[x*scale for x in base]
            # perturb each size by -scale..+scale
            sz=[max(1,x+rnd.randint(-scale,scale)) for x in sz]
            if max(sz)>L: continue
            # add 0..4 extra items
            k=rnd.randint(0,4)
            for _ in range(k):
                sz.append(rnd.randint(max(1,L//6+1),L))
            yield sz,L
    # Family B: random instances, sizes in (L/6, L]
    for n in (10,11,12,13,14):
        for trial in range(1500):
            L=rnd.choice([60,81,100,120,150,240])
            sz=[rnd.randint(L//6+1,L) for _ in range(n)]
            yield sz,L
    # Family C: few distinct sizes with multiplicities (ratio structures)
    for n in (10,12,14,16):
        for trial in range(1200):
            L=rnd.choice([60,120,240,360])
            d=rnd.randint(2,4)
            vals=[rnd.randint(L//6+1,L) for _ in range(d)]
            sz=[rnd.choice(vals) for _ in range(n)]
            yield sz,L
    # Family D: sizes from L/p + eps grid (Kartak-style constructions)
    for n in (10,12,14):
        for trial in range(1200):
            L=rnd.choice([90,120,180,360])
            q=rnd.randint(2,6)
            sz=[rnd.randint(1,3)*L//q + rnd.choice([-2,-1,0,1,2]) for _ in range(n)]
            sz=[max(1,min(L,x)) for x in sz]
            yield sz,L

def main():
    t0=time.time(); budget=float(sys.argv[1]) if len(sys.argv)>1 else 900
    hits=[]; n_ev=0
    for sizes,L in gen_families():
        if time.time()-t0>budget: break
        try:
            r=evaluate(sizes,L)
        except Exception as e:
            continue
        if r is None: continue
        lp,opt=r; n_ev+=1
        if opt >= int(np.ceil(lp-1e-7))+2:
            hits.append({"sizes":sizes,"L":L,"lp":lp,"opt":opt})
            print("HIT",hits[-1],flush=True)
            json.dump(hits,open("hits.json","w"),indent=1)
    print(f"evaluated {n_ev} instances in {time.time()-t0:.0f}s; hits={len(hits)}",flush=True)

main()
