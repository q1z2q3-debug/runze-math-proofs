"""Real frontier for the degree-bounded Ryser route.

Theorem C (new; see docs/ryser-review.md): at the tight point (D,E)=(r+1,r^2) the counting
bound is exactly tight, which forces every part's degrees to be (r+1,...,r+1,1); then for every
edge the number of edges it agrees with is a multiple of r, but has to equal E-1 = r^2-1,
which is not a multiple of r.  Hence the tight point is EMPTY for all r >= 3.

This script finds, for each r, the smallest (D,E) with E > (r-1)D that survives both the
counting bound and the edge-identity obstruction: the real search frontier.
"""
from math import comb
import json


def margin(r, D, E):
    q, rem = divmod(E, D)
    return comb(E, 2) - r * (q * comb(D, 2) + comb(rem, 2))


def identity_ok(r, D, E):
    if margin(r, D, E) != 0:
        return True
    rem = E % D
    return any(k * (D - 1) + (r - k) * (rem - 1) == E - 1 for k in range(r + 1))


rows = []
for r in range(3, 11):
    tgt = None
    for D in range(r + 1, 4 * r + 6):
        for E in range((r - 1) * D + 1, (r - 1) * D + 6 * D + 60):
            if margin(r, D, E) <= 0 and identity_ok(r, D, E):
                if tgt is None or (E, D) < (tgt[1], tgt[0]):
                    tgt = (D, E)
    tight = dict(D=r + 1, E=r * r, margin=margin(r, r + 1, r * r),
                 edge_identity_ok=identity_ok(r, r + 1, r * r))
    real = dict(D=tgt[0], E=tgt[1], margin=margin(r, tgt[0], tgt[1]),
                vertices_per_part=-(-tgt[1] // tgt[0]))
    rows.append(dict(r=r, tight=tight, first_real_target=real))
    msg = "r={} tight=(D={},E={}) empty -> first real target: D={} E={} margin={} vertices per part={}"
    print(msg.format(r, tight["D"], tight["E"], real["D"], real["E"],
                     real["margin"], real["vertices_per_part"]))

json.dump(rows, open("data/ryser_frontier_theoremC.json", "w"), indent=1)
print("written data/ryser_frontier_theoremC.json")
