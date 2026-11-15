"""Independent re-derivation of the degree-bounded Ryser obstruction bound.

For each r we scan (D, |E|) and report the smallest pair satisfying

    C(|E|,2) <= r * [ floor(|E|/D)*C(D,2) + C(|E| mod D, 2) ]

with |E| > (r-1)*D.  Result: (D,|E|) = (r+1, r^2) with margin 0, i.e. the frontier
any degree-bounded counterexample must sit on.  Used to audit
`collab/ryser-pack` (whose r=6 runs used D=4, |E|=21 -- far below the frontier).
"""
from math import comb
import json
import os

def margin(r, D, E):
    q, rem = divmod(E, D)
    return comb(E, 2) - r * (q * comb(D, 2) + comb(rem, 2))

rows = []
for r in range(3, 13):
    best = None
    for D in range(2, r + 4):
        for E in range((r - 1) * D + 1, (r - 1) * D + 4 * D + 40):
            if margin(r, D, E) <= 0:
                if best is None or (E, D) < (best[1], best[0]):
                    best = (D, E)
    rows.append({"r": r, "D": best[0], "E": best[1],
                 "margin": margin(r, best[0], best[1]),
                 "vertices_per_part_min": -(-best[1] // best[0])})

print(json.dumps(rows, indent=1))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "ryser_bound_table.json")
json.dump(rows, open(out, "w"), indent=1)
print("written:", out)
