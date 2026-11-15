# -*- coding: utf-8 -*-
"""Round 3 core, v2: z3 CEGAR synthesizer for an explicit Ryser counterexample.

Instead of keeping the classical truncated-plane edges fixed (which was too
rigid: only 25 transversals meet all of them), we let EVERY edge choose its
vertex label in EVERY part from V = F_q U {NEW}, subject to:
  (1) any two edges share a vertex in some part  -> nu = 1
  (2) (CEGAR) for each discovered small vertex cover C, some edge avoids C
      -> eventually tau >= r
This is exactly "change the line labels within the parts and insert
exceptional edges" reconstructed from scratch as a finite CSP.

On success the output is an explicit r-partite r-uniform hypergraph with
tau = r > (r-1)*nu = r-1, i.e. a Ryser counterexample.
"""
import itertools, json, sys, time
from z3 import *

Q = 5
R = Q + 1                    # parts
NV = Q + 1                   # vertices per part (0..Q-1 originals, Q = NEW)
NE = Q * Q                   # number of edges (the q^2 lines, relabelled)

A = [[Int(f'a_{e}_{p}') for p in range(R)] for e in range(NE)]

def vrange(v): return And(v >= 0, v <= Q)

def build_solver(fix_inf=False):
    s = Solver()
    for e in range(NE):
        for p in range(R):
            s.add(vrange(A[e][p]))
    # (1) pairwise intersecting  -> nu = 1
    for e in range(NE):
        for f in range(e+1, NE):
            s.add(Or([A[e][p] == A[f][p] for p in range(R)]))
            # also forbid duplicate transversals (keeps |edges| = NE)
            s.add(Or([A[e][p] != A[f][p] for p in range(R)]))
    if fix_inf:
        for b in range(Q):
            for s0 in range(Q):
                e = s0*Q + b
                s.add(A[e][0] == s0)
    return s

def model_edges(m):
    return [tuple(m.eval(A[e][p]).as_long() for p in range(R)) for e in range(NE)]

def min_cover(edges, ub):
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

def all_min_covers(edges, tau, limit=400):
    """enumerate covers of size tau (bounded) to block several at once."""
    n = len(edges)
    hit = {}
    for i, e in enumerate(edges):
        for p in range(R):
            hit.setdefault((p, e[p]), 0)
            hit[(p, e[p])] |= 1 << i
    ALL = (1<<n)-1
    out = []
    def rec(chosen, cov, k):
        if len(out) >= limit: return
        if cov == ALL:
            if k == tau: out.append(set(chosen))
            return
        if k >= tau: return
        idx = next(i for i in range(n) if not ((cov>>i)&1))
        e = edges[idx]
        for p in range(R):
            pv = (p, e[p])
            if pv in chosen: continue
            rec(chosen | {pv}, cov | hit[pv], k+1)
    rec(set(), 0, 0)
    return out

def nu_exact(edges):
    def meet(e, f):
        return any(e[p] == f[p] for p in range(R))
    best = 0
    def dfs(used, start, d):
        nonlocal best
        if d > best: best = d
        for i in range(start, len(edges)):
            if all(not meet(edges[i], edges[j]) for j in used):
                used.append(i); dfs(used, i+1, d+1); used.pop()
    dfs([], 0, 0)
    return best

def cegar(max_iters=400, fix_inf=False, verbose=True):
    s = build_solver(fix_inf)
    t0 = time.time(); seen = set()
    for it in range(max_iters):
        if s.check() != sat:
            print(f'  UNSAT at iter {it} ({time.time()-t0:.1f}s)'); return None
        m = s.model()
        edges = model_edges(m)
        tau, C = min_cover(edges, R + 2)
        if tau >= R:
            print(f'  *** SUCCESS at iter {it} ({time.time()-t0:.1f}s): tau={tau} >= r={R}')
            return edges
        # block all minimum covers of this model (not just one)
        covers = all_min_covers(edges, tau, limit=60)
        if verbose and it % 20 == 0:
            print(f'  iter={it} tau={tau} #min-covers={len(covers)} elapsed={time.time()-t0:.1f}s', flush=True)
        added = 0
        for C in covers:
            key = tuple(sorted(C))
            if key in seen: continue
            seen.add(key)
            # exists an edge avoiding C: for each (p,v) in C, that edge's part-p value != v
            clauses = []
            for e in range(NE):
                clauses.append(And([A[e][p] != v for (p, v) in C]))
            s.add(Or(clauses))
            added += 1
        if added == 0 and covers:
            C0 = covers[0]
            s.add(Or([And([A[e][p] != v for (p,v) in C0]) for e in range(NE)]))
    print(f'  no success in {max_iters} iters ({time.time()-t0:.1f}s), blocked {len(seen)} covers')
    return None

if __name__ == '__main__':
    Q = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    R = Q + 1; NV = Q + 1; NE = Q*Q
    A = [[Int(f'a_{e}_{p}') for p in range(R)] for e in range(NE)]
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    print(f'=== z3 CEGAR: q={Q} r={R} parts={R} |V|={NV} edges={NE} ===', flush=True)
    edges = cegar(max_iters=iters)
    if edges:
        tau, C = min_cover(edges, R+3)
        nu = nu_exact(edges)
        ok = tau > (R-1)*nu
        print(f'  VERIFY: tau={tau} nu={nu} (r-1)*nu={(R-1)*nu} RYSER FAILS? {ok}')
        print('  edge table (part0..part%d):' % (R-1))
        for i,e in enumerate(edges): print('   ', i, e)
        json.dump(dict(q=Q, r=R, tau=tau, nu=nu, ok=ok,
                       edges=[list(e) for e in edges],
                       min_cover=[list(x) for x in (C or [])]),
                  open('/data/workspace/run_logs/ryser_counterexample.json','w'), indent=1)
        print('  saved run_logs/ryser_counterexample.json')
    else:
        json.dump(dict(q=Q, r=R, success=False),
                  open(f'/data/workspace/run_logs/ryser_q{Q}_cegar.json','w'), indent=1)
