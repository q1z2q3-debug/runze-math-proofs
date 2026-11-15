"""Local search for the real frontier of the degree-bounded Ryser route.

Object: E codewords of length r over an alphabet of size q, such that
  (1) any two codewords agree in at least one coordinate   (=> intersecting family, nu = 1),
  (2) each symbol is used at most D times in each coordinate (=> max degree <= D),
  (3) E > (r-1)*D                                          (=> tau >= ceil(E/D) >= r > (r-1)nu).

Theorem C says the tight point (D,E)=(r+1,r^2) is empty, so search the next feasible band
(D,E) = (r+2, r^2+r-1), and also a few neighbours.
"""
import random, sys, json, time

def energy(words, r, q, D):
    """#pairs disagreeing everywhere + degree overflow."""
    n = len(words)
    bad = 0
    for i in range(n):
        a = words[i]
        for j in range(i + 1, n):
            b = words[j]
            if not any(a[p] == b[p] for p in range(r)):
                bad += 1
    degs = [[0] * q for _ in range(r)]
    for w in words:
        for p in range(r):
            degs[p][w[p]] += 1
    over = sum(max(0, d - D) for row in degs for d in row)
    return bad, over

def solve(r, q, E, D, seconds=60, seed=0, restarts=200):
    random.seed(seed)
    t_end = time.time() + seconds
    best = None
    for _ in range(restarts):
        if time.time() > t_end:
            break
        words = [[random.randrange(q) for _ in range(r)] for _ in range(E)]
        # enforce degrees by resampling positions that overflow
        for p in range(r):
            pos = list(range(E))
            random.shuffle(pos)
            k = 0
            while k < E:
                val = words[pos[k]][p]
                cnt = sum(1 for i in range(E) if words[i][p] == val)
                if cnt > D:
                    words[pos[k]][p] = (val + 1 + random.randrange(q - 1)) % q
                else:
                    k += 1
        # hill climb on conflicting pairs
        for step in range(60000):
            if time.time() > t_end:
                break
            es = energy(words, r, q, D)
            hit = (es[0] == 0 and es[1] == 0)
            if best is None or es < best[0]:
                best = (es, [w[:] for w in words])
            if hit:
                return {"status": "SAT", "words": words, "energy": es, "step": step}
            # pick a conflicting pair, fix one coordinate of one of them
            i = random.randrange(E)
            p = random.randrange(r)
            v = random.randrange(q)
            old = words[i][p]
            words[i][p] = v
            ne = energy(words, r, q, D)
            if ne > es and random.random() > 0.35:
                words[i][p] = old
    return {"status": "NO SOLUTION FOUND", "best": best[0] if best else None,
            "words": best[1] if best else None}

if __name__ == "__main__":
    r = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    q = int(sys.argv[2]) if len(sys.argv) > 2 else r
    E = int(sys.argv[3]) if len(sys.argv) > 3 else r * r + r - 1
    D = int(sys.argv[4]) if len(sys.argv) > 4 else r + 2
    sec = int(sys.argv[5]) if len(sys.argv) > 5 else 60
    res = solve(r, q, E, D, seconds=sec)
    print(json.dumps({k: v for k, v in res.items() if k != "words"}))
    print("r=%d q=%d E=%d D=%d ceil(E/D)=%d need>=r(%d)" % (r, q, E, D, -(-E // D), r))
    if res.get("words"):
        print("words =", res["words"])
