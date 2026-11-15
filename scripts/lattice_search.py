"""Lattice-indexed search: 三元 × 九维 × 三阶 (3^9 = 19683 cells).

Each cell is a 9-trit address. We instantiate a runnable parameter family for the
sub-lattice that matters for MIRUP counterexamples:
 元一 象 (structure):  arity a ∈ {2,3,4,5}  |  band 3 levels  |  symmetry 3 levels
 元二 数 (computation): tightness 3 levels  |  multiplicity 3  |  grid denominator 3
 元三 理 (argument):    dual family 3      |  obstruction type 3 |  reduction depth 3
We only run the cells whose 象/数 part is realizable in <= 20 items.
"""
import itertools, json, random, time
import bpp

def inst_from_cell(a, band, sym, tight, mult, den, L=1000):
    """Build sizes: a-part decompositions of L, perturbed to kill all but one pattern."""
    eps = [0, L//(den*10), L//(den*4)][tight]        # perturbation size
    base = L // a
    if band == 0:   sizes0 = [base + eps] * a        # all just above L/a
    elif band == 1: sizes0 = [base - eps] + [base + eps] * (a - 1)
    else:           sizes0 = [base + 2*eps] * (a - 1) + [base - 3*eps]
    if sym == 1:    sizes0 = [sizes0[0]] * a
    if sym == 2:    sizes0 = [base] * a
    return sizes0 * mult, L

def run(max_inst=4000, seed=7):
    random.seed(seed)
    t0=time.time(); dist={}; best=[]; n=0
    cells=[]
    for a in (2,3,4,5):
        for band in (0,1,2):
            for sym in (0,1,2):
                for tight in (0,1,2):
                    for mult in (2,3,4):
                        for den in (3,5,7):
                            cells.append((a,band,sym,tight,mult,den))
    for cell in cells:
        sizes,L = inst_from_cell(*cell)
        if len(sizes)>14: continue
        try:
            pats,A = bpp.build_matrices(sizes,L)
            lp,_ ,_ = bpp.lp_value(sizes,L,pats_A=(pats,A))
            opt = bpp.opt_value(sizes,L,pats_A=(pats,A),time_limit=8)[0]
        except Exception:
            continue
        if lp is None or opt is None: continue
        n+=1
        gap=round(opt)-int(-(-lp//1) if False else 0)
        import math
        gap=round(opt)-math.ceil(lp-1e-7)
        dist[gap]=dist.get(gap,0)+1
        if gap>=1: best.append({"cell":cell,"sizes":sizes,"L":L,"lp":round(lp,4),"opt":opt,"gap":gap})
        if n>=max_inst or time.time()-t0>420: break
    print(f"cells_total={len(cells)} run={n} time={time.time()-t0:.0f}s")
    print("dist:",dist)
    print("gap>=1 examples:",len(best))
    for b in best[:6]: print(b)
    json.dump({"cells_total":len(cells),"run":n,"dist":dist,"examples":best[:20]},
              open("lattice_result.json","w"),indent=1)
    return dist,best

if __name__=="__main__": run()
