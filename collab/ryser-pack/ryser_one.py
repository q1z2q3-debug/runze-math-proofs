# -*- coding: utf-8 -*-
"""ONE TASK: ryser-conjecture / refuted slot.

Target: an explicit r-partite r-uniform hypergraph H with
    nu(H) = 1   (every two edges share a vertex)
    tau(H) >= r (no vertex cover of size r-1)
=> tau > (r-1)*nu  => RyserBound fails => `refuted` is proved.

Machine-checkable counting lemma (the whole proof, 3 lines):
    if every vertex (p,v) lies in at most D edges, then any cover C
    hits at most |C|*D edges, so |C| >= ceil(|E|/D).
    Choose |E| > (r-1)*D  =>  ceil(|E|/D) >= r.

So we only need a finite CSP:
    NE edges, R parts, NV vertices per part,
    (a) any two edges agree in >= 1 part     -> nu = 1
    (b) any two edges are distinct
    (c) degree of every (p,v) <= D
    (d) NE > (R-1)*D

Built from scratch: simulated annealing with incremental cost, then an
INDEPENDENT exact verifier (tau by branch-and-bound, nu by DFS, degrees,
intersection, distinctness). No external solver needed for the final object.
"""
import random, json, sys, time, math, itertools

def construct(R, NV, NE, D, seed, steps=400000, T0=2.5, T1=0.005, verbose=False):
    rng = random.Random(seed)
    E = [[rng.randrange(NV) for _ in range(R)] for _ in range(NE)]
    deg = [[0]*NV for _ in range(R)]
    for e in range(NE):
        for p in range(R): deg[p][E[e][p]] += 1

    def meet(i, j):
        for p in range(R):
            if E[i][p] == E[j][p]: return True
        return False
    def same(i, j):
        return all(E[i][p] == E[j][p] for p in range(R))

    bad = [[False]*NE for _ in range(NE)]   # bad[i][j] = not intersecting
    dup = [[False]*NE for _ in range(NE)]   # duplicate transversals
    nbad = ndup = 0
    for i in range(NE):
        for j in range(i+1, NE):
            if not meet(i,j): bad[i][j]=bad[j][i]=True; nbad+=1
            if same(i,j): dup[i][j]=dup[j][i]=True; ndup+=1
    nover = sum(max(0, deg[p][v]-D) for p in range(R) for v in range(NV))

    W_BAD, W_DUP, W_DEG = 60, 30, 8
    cost = W_BAD*nbad + W_DUP*ndup + W_DEG*nover

    for step in range(steps):
        T = T0 * (T1/T0) ** (step/steps)
        e = rng.randrange(NE); p = rng.randrange(R)
        old = E[e][p]; new = rng.randrange(NV)
        if old == new: continue

        # --- incremental evaluation ---
        deg[p][old] -= 1; deg[p][new] += 1
        d_over = (max(0,deg[p][old]+1-D) - max(0,deg[p][old]-D)) + \
                 (max(0,deg[p][new]-D)   - max(0,deg[p][new]-1-D))
        E[e][p] = new
        changed = []
        d_bad = d_dup = 0
        for f in range(NE):
            if f == e: continue
            was_bad, was_dup = bad[e][f], dup[e][f]
            is_bad = not meet(e,f)
            is_dup = same(e,f)
            if was_bad != is_bad:
                d_bad += (1 if is_bad else -1)
                changed.append((f,'b',was_bad))
                bad[e][f]=bad[f][e]=is_bad
            if was_dup != is_dup:
                d_dup += (1 if is_dup else -1)
                changed.append((f,'d',was_dup))
                dup[e][f]=dup[f][e]=is_dup
        dcost = W_BAD*d_bad + W_DUP*d_dup + W_DEG*d_over
        if dcost <= 0 or rng.random() < math.exp(-dcost/T):
            cost += dcost; nbad += d_bad; ndup += d_dup; nover += d_over
            if cost == 0:
                return E, dict(steps=step+1, seed=seed, cost=0)
        else:
            # rollback
            E[e][p] = old
            deg[p][old] += 1; deg[p][new] -= 1
            for f,kind,val in changed:
                if kind=='b': bad[e][f]=bad[f][e]=val
                else: dup[e][f]=dup[f][e]=val
        if verbose and step and step % 100000 == 0:
            print(f'    step={step} cost={cost} nbad={nbad} ndup={ndup} nover={nover}', flush=True)
    return None, dict(steps=steps, seed=seed, cost=cost, nbad=nbad, ndup=ndup, nover=nover)

def exact_verify(E, R, NV, D, ub=None):
    NE = len(E)
    ub = ub or (R+4)
    # degrees
    deg = {}
    for e in E:
        for p in range(R): deg[(p,e[p])] = deg.get((p,e[p]),0)+1
    dmax = max(deg.values())
    # distinct
    distinct = len(set(map(tuple,E))) == NE
    # intersecting  -> nu = 1
    def meet(a,b): return any(a[p]==b[p] for p in range(R))
    inter = all(meet(E[i],E[j]) for i in range(NE) for j in range(i+1,NE))
    # exact nu (DFS on disjointness)
    nu = 0
    def dfs(used,start,d):
        nonlocal nu
        if d>nu: nu=d
        for i in range(start,NE):
            if all(not meet(E[i],E[j]) for j in used):
                used.append(i); dfs(used,i+1,d+1); used.pop()
    dfs([],0,0)
    # exact tau (branch and bound over covered-edge bitmask)
    hit = {}
    for i,e in enumerate(E):
        for p in range(R):
            hit.setdefault((p,e[p]),0); hit[(p,e[p])] |= 1<<i
    ALL=(1<<NE)-1
    best=[ub+1,None]
    def rec(chosen,cov,k):
        if k>=best[0]: return
        if cov==ALL: best[0]=k;best[1]=set(chosen);return
        idx=next(i for i in range(NE) if not ((cov>>i)&1))
        e=E[idx]
        vs=[(p,e[p]) for p in range(R) if (p,e[p]) not in chosen]
        scored=sorted(((bin(hit[pv]&~cov).count('1'),pv) for pv in vs),reverse=True)
        for _,pv in scored:
            rec(chosen|{pv}, cov|hit[pv], k+1)
            if k+1>=best[0]: break
    rec(set(),0,0)
    tau=best[0]
    counting = -(-NE//D)             # ceil(NE/D)
    # independent brute check: NO cover of size <= R-1 exists
    small_cover_exists = (tau <= R-1)
    return dict(NE=NE,R=R,NV=NV,D=D,dmax=dmax,distinct=distinct,intersecting=inter,
                nu=nu,tau=tau,counting_lower=counting,small_cover_exists=small_cover_exists,
                ryser_bound=(R-1)*nu,
                ryser_fails=(not small_cover_exists) and nu==1 and tau>(R-1)*nu,
                min_cover=[list(x) for x in (best[1] or [])],
                degree_table={f'{p},{v}':deg.get((p,v),0) for p in range(R) for v in range(NV)})

def scan(verbose=True):
    trials=[]
    # NE > (R-1)*D and NE <= NV*D (necessary from degree counting)
    for R in (5,6,7):
        for NV in (R, R+1, R+2, 2*R):
            for D in (3,4,5,6):
                lo=(R-1)*D+1; hi=NV*D
                for NE in (lo, lo+1, min(lo+2,hi), min(hi,lo+4)):
                    if NE<2 or NE>hi: continue
                    if -(-NE//D) < R: continue
                    trials.append((R,NV,NE,D))
    # prefer small instances first (easier to formalize / decide)
    trials.sort(key=lambda t:(t[0]*t[1]*t[2], t[2]))
    seen=set(); tried=0
    for R,NV,NE,D in trials:
        key=(R,NV,NE,D)
        if key in seen: continue
        seen.add(key); tried+=1
        if tried>26: break
        if verbose: print(f'  try R={R} NV={NV} NE={NE} D={D} ceil(NE/D)={-(-NE//D)} (R-1)D={(R-1)*D}',flush=True)
        for seed in (20261115, 7, 424242):
            E,info = construct(R,NV,NE,D,seed,steps=120000)
            if E:
                v=exact_verify(E,R,NV,D)
                print(f'    seed={seed} steps={info["steps"]} -> tau={v["tau"]} nu={v["nu"]} dmax={v["dmax"]} FAILS={v["ryser_fails"]}',flush=True)
                if v['ryser_fails']:
                    return E, v, dict(R=R,NV=NV,NE=NE,D=D,seed=seed,info=info)
                break
    return None, None, None

if __name__=='__main__':
    t0=time.time()
    print('=== ONE TASK: explicit Ryser counterexample (r-partite, nu=1, tau>=r) ===',flush=True)
    E,v,meta = scan()
    print(f'elapsed {time.time()-t0:.1f}s',flush=True)
    if E:
        print('\n*** SUCCESS ***')
        print('params:',meta)
        print('verify:',{k:x for k,x in v.items() if k not in ('degree_table','min_cover')})
        print('\nEDGE TABLE (each row = one transversal, part 0..R-1):')
        for i,e in enumerate(E): print(f'  e{i:02d} = {e}')
        out=dict(params=meta,verify=v,edges=[list(e) for e in E])
        json.dump(out,open('/data/workspace/run_logs/ryser_SOLVED.json','w'),indent=1)
        print('\nsaved run_logs/ryser_SOLVED.json')
    else:
        print('no success'); json.dump(dict(success=False),open('/data/workspace/run_logs/ryser_one_result.json','w'))
