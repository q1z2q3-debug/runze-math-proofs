"""Purpose-built SAT decision for the r=4 frontier of the degree-bounded Ryser route.

Object: E codewords (edges) of length r over alphabet of size q, pairwise agreeing in >=1
coordinate (=> intersecting => nu=1), each symbol used <= D times per coordinate
(=> max degree <= D), and E > (r-1)D (=> tau >= ceil(E/D) >= r > (r-1)nu).

Symmetry breaking (this is what the received pack lacked):
  * coordinate 0 has a fixed block structure with block sizes `blocks`: edges are
    pre-assigned to blocks w.l.o.g. (all structures are covered by permuting edges).
  * edges inside a block are interchangeable, so we additionally require that for every
    other coordinate, the values are "first-occurrence ordered" (no requirement, just
    ordering the edge list), which we realise by sorting edges by coordinate 0.
USAGE: python ryser_r4_sat.py <r> <q> <E> <D> <b1,b2,...> [timeout]
"""
import sys, time, json
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153


def decide(r, q, E, D, blocks):
    assert sum(blocks) == E, (blocks, E)
    pool = IDPool()
    X = lambda e, p, v: pool.id(("X", e, p, v))
    Y = lambda e, f, p, v: pool.id(("Y", e, f, p, v))
    W = lambda e, f, p: pool.id(("W", e, f, p))
    cnf = CNF()

    # edge -> block (coordinate 0 fixed)
    blk = []
    for b, sz in enumerate(blocks):
        blk += [b] * sz

    for e in range(E):
        for p in range(r):
            lits = [X(e, p, v) for v in range(q)]
            cnf.extend(CardEnc.equals(lits=lits, bound=1, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
        cnf.append([X(e, 0, blk[e])])
        for v in range(q):
            if v != blk[e]:
                cnf.append([-X(e, 0, v)])

    for p in range(r):
        for v in range(q):
            cnf.extend(CardEnc.atmost(lits=[X(e, p, v) for e in range(E)], bound=D,
                                      vpool=pool, encoding=EncType.seqcounter).clauses)

    for e in range(E):
        for f in range(e + 1, E):
            ws = []
            for p in range(r):
                w = W(e, f, p)
                ws.append(w)
                ys = []
                for v in range(q):
                    y = Y(e, f, p, v)
                    ys.append(y)
                    cnf.append([-y, X(e, p, v)])
                    cnf.append([-y, X(f, p, v)])
                    cnf.append([-X(e, p, v), -X(f, p, v), y])
                    cnf.append([-y, w])
                cnf.append([-w] + ys)
            cnf.append(ws)                 # agree somewhere
            cnf.append([-w for w in ws])   # not agree everywhere (distinct edges)

    solver = Cadical153(bootstrap_with=cnf.clauses)
    t0 = time.time()
    res = solver.solve()
    el = time.time() - t0
    if not res:
        solver.delete()
        return {"result": "UNSAT", "blocks": blocks, "elapsed": round(el, 2),
                "vars": pool.top, "clauses": len(cnf.clauses)}
    model = set(l for l in solver.get_model() if l > 0)
    solver.delete()
    words = [[next(v for v in range(q) if X(e, p, v) in model) for p in range(r)]
             for e in range(E)]
    return {"result": "SAT", "blocks": blocks, "elapsed": round(el, 2),
            "words": words, "vars": pool.top, "clauses": len(cnf.clauses)}


def verify(words, r, D):
    n = len(words)
    degs = [{} for _ in range(r)]
    for w in words:
        for p in range(r):
            degs[p][w[p]] = degs[p].get(w[p], 0) + 1
    inter = all(any(words[i][p] == words[j][p] for p in range(r))
                for i in range(n) for j in range(i + 1, n))
    distinct = len({tuple(w) for w in words}) == n
    dmax = max(max(d.values()) for d in degs)
    return {"intersecting": inter, "distinct": distinct, "dmax": dmax,
            "tau_lower": -(-n // D), "nu": 1, "ryser_rhs": r - 1,
            "refutes": inter and distinct and dmax <= D and -(-n // D) >= r}


if __name__ == "__main__":
    r, q, E, D = map(int, sys.argv[1:5])
    blocks = [int(x) for x in sys.argv[5].split(",")]
    out = decide(r, q, E, D, blocks)
    if out["result"] == "SAT":
        out["verify"] = verify(out["words"], r, D)
    print(json.dumps(out))
