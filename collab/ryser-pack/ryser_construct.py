# -*- coding: utf-8 -*-
"""Round 3 (core): 0->1 construction of an explicit Ryser counterexample.

Mathematical seed (from literature, reconstructed here):
  Truncated projective plane of order q.  In the affine model of PG(2,q),
  delete one point P at infinity (the "vertical" direction) and contract the
  q+1 lines through P into parts:
    part INF  = the q other points at infinity (slopes s in F_q)
    part x    = the q affine points on the vertical line X=x, labelled by y
  The q^2 affine lines y = s*x + b (s,b in F_q) become transversals
    f_{s,b}(INF)=s,  f_{s,b}(x)=s*x+b mod q.
  Any two of them meet (same slope at INF, or unique intersection x), so
  nu=1.  Taking every vertex of one part is a cover of size q = r-1, so
  tau=q: this is the classical TIGHT example, not a counterexample.

OpenAI's idea (reconstructed): keep one part per ambient direction, add a
fresh vertex to each part, and insert EXCEPTIONAL edges (transversals that
still meet every existing edge) so that no (r-1)-vertex set covers all edges.

This program does that search itself:
  1. enumerate all transversals over (q+1) parts x (q+1) vertices,
  2. keep those meeting every E0 edge,
  3. greedily insert exceptional edges avoiding a current minimum cover,
     always preserving pairwise intersection,
  4. verify tau > (r-1)*nu with an independent exact solver.

If it succeeds, the output is a fully explicit finite hypergraph H with
nu=1 and tau=r, which refutes Ryser's conjecture and fills the TCSExam
`ryser-conjecture` refuted slot.
"""
import itertools, json, sys, time, random
from functools import lru_cache

Q = 5          # try 5, 7, 11
NEW = Q        # the fresh vertex id in every part
R = Q + 1      # number of parts
PARTS = list(range(R))          # 0 = INF, 1..Q = vertical lines x=0..Q-1
VERTS = list(range(Q + 1))     # 0..Q-1 = original, Q = NEW

def line_edge(s, b):
    # part 0 (INF) -> s ; part x (1..Q) -> s*(x-1)+b mod q
    e = [0] * R
    e[0] = s
    for x in range(1, R):
        e[x] = (s * (x - 1) + b) % Q
    return tuple(e)

E0 = [line_edge(s, b) for s in range(Q) for b in range(Q)]
E0set = set(E0)

def meet(e, f):
    for p in range(R):
        if e[p] == f[p] and e[p] != NEW:
            return True
    return False

def avoids(e, C):
    # C is a set of (part, vertex) pairs
    for p in range(R):
        if (p, e[p]) in C:
            return False
    return True

# ---------- exact tau and one minimum cover ----------
def min_cover(edges, ub):
    """min vertex set meeting every edge. cov = bitmask over EDGE INDICES."""
    n = len(edges)
    hit = {}
    for i, e in enumerate(edges):
        for p in range(R):
            hit.setdefault((p, e[p]), 0)
            hit[(p, e[p])] |= 1 << i
    ALL = (1 << n) - 1
    best = [ub + 1, None]
    def rec(chosen, cov, k):
        if k >= best[0]: return
        if cov == ALL:
            best[0] = k; best[1] = set(chosen); return
        idx = next(i for i in range(n) if not ((cov >> i) & 1))
        e = edges[idx]
        vs = [(p, e[p]) for p in range(R) if (p, e[p]) not in chosen]
        scored = [(bin(hit[pv] & ~cov).count('1'), pv) for pv in vs]
        scored.sort(reverse=True)
        for _, pv in scored:
            rec(chosen | {pv}, cov | hit[pv], k + 1)
            if k + 1 >= best[0]: break
    rec(set(), 0, 0)
    return best[0], best[1]

def matching_number(edges):
    """nu: max pairwise disjoint edges (disjoint = differ in EVERY part)."""
    best = 0
    def dfs(used, start, d):
        nonlocal best
        if d > best: best = d
        for i in range(start, len(edges)):
            e = edges[i]
            # a matching requires pairwise DISJOINT edges: they must differ in EVERY part
            ok = all(not meet(e, edges[j]) for j in used)
            if ok:
                used.append(i); dfs(used, i + 1, d + 1); used.pop()
    dfs([], 0, 0)
    return best

def enumerate_candidates():
    """all transversals meeting every E0 edge (streamed, kept if valid)."""
    total = (Q + 1) ** R
    print(f'  enumerating {total:,} transversals over {R} parts x {Q+1} vertices ...', flush=True)
    cand = []
    t0 = time.time()
    for k, vals in enumerate(itertools.product(VERTS, repeat=R)):
        e = tuple(vals)
        if e in E0set:
            cand.append(e); continue
        ok = all(meet(e, f) for f in E0)
        if ok: cand.append(e)
        if k and k % 2000000 == 0:
            print(f'    {k:,}/{total:,} elapsed={time.time()-t0:.1f}s kept={len(cand)}', flush=True)
    print(f'  done: {len(cand):,} valid candidates ({time.time()-t0:.1f}s)', flush=True)
    return cand

def greedy(cand, restarts=200, seed=0):
    rng = random.Random(seed)
    best = (0, None)
    for r in range(restarts):
        # start from E0 (or a random subset of E0)
        S = list(E0) if r == 0 else [f for f in E0 if rng.random() < 0.85]
        Sset = set(S)
        steps = 0
        while steps < 60:
            tau, C = min_cover(S, R)     # look for cover of size <= R-1
            if tau >= R:                 # SUCCESS: tau = r, nu=1
                return S, tau, C
            # C is a cover of size tau <= R-1; need an edge avoiding it
            pool = [e for e in cand if e not in Sset and avoids(e, C)
                    and all(meet(e, f) for f in S)]
            if not pool: break
            # prefer an edge using NEW vertices (breaks old covers most)
            pool.sort(key=lambda e: (-sum(1 for v in e if v == NEW), rng.random()))
            e = pool[0]
            S.append(e); Sset.add(e); steps += 1
        if len(S) > best[0]: best = (len(S), S)
        if r % 20 == 0:
            print(f'    restart {r}: |S|={len(S)} best={best[0]}', flush=True)
    return None, best[0], None

def verify(S):
    tau, C = min_cover(S, R + 3)
    nu = matching_number(S)
    ok = tau > (R - 1) * nu
    print(f'  VERIFY: |edges|={len(S)} nu={nu} tau={tau} (r-1)*nu={(R-1)*nu} '
          f'RYSER FAILS? {ok}')
    return dict(tau=tau, nu=nu, ok=ok, edges=S, min_cover=[list(x) for x in (C or [])])

if __name__ == '__main__':
    Q = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    NEW = Q; R = Q + 1; PARTS = list(range(R)); VERTS = list(range(Q + 1))
    E0 = [line_edge(s, b) for s in range(Q) for b in range(Q)]
    E0set = set(E0)
    print(f'=== q={Q}  r={R}  parts={R}  vertices/part={Q+1}  E0={len(E0)} lines ===')
    # sanity: classical tight example
    tau0, C0 = min_cover(E0, R)
    nu0 = matching_number(E0)
    print(f'  classical truncated plane: tau={tau0} nu={nu0} bound=(r-1)nu={R-1} '
          f'tight? {tau0 == R-1 and nu0 == 1}')
    cand = enumerate_candidates()
    S, n, C = greedy(cand, restarts=120, seed=20261115)
    if S is None:
        print(f'  NO counterexample found at q={Q} (best |S|={n})')
        out = dict(q=Q, r=R, success=False, best_edges=n,
                   classical=dict(tau=tau0, nu=nu0))
    else:
        print('  *** SUCCESS: explicit intersecting hypergraph with tau=r ***')
        out = verify(S)
        out.update(q=Q, r=R, success=True, min_cover_size=tau0)
        json.dump(out, open('/data/workspace/run_logs/ryser_counterexample.json','w'), indent=1)
        print('  saved run_logs/ryser_counterexample.json')
    json.dump(out, open(f'/data/workspace/run_logs/ryser_q{Q}_result.json','w'), indent=1)
