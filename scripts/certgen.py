import json, bpp
from fractions import Fraction

INST = {
 "instC": ([4,6,6,9,16,29,32,37,40,62], 81),
 "instB1": ([6,4,4,3,3], 12),
 "instB2": ([7,7,7,7], 12),
}
out = {"generated_by": "bpp.py (HiGHS LP/MILP + exact Fraction simplex)",
       "semantics": "patterns = subsets of item copies with sum <= L; configuration LP; OPT = integer optimum",
       "instances": {}}
for name,(sizes,L) in INST.items():
    pats,A = bpp.build_matrices(sizes,L)
    lp,x,_ = bpp.lp_value(sizes,L,pats_A=(pats,A))
    opt = bpp.opt_value(sizes,L,pats_A=(pats,A))[0]
    vol = bpp.volume(sizes,L)
    ex = bpp.exact_lp_fraction(sizes,L) if name=="instC" else None
    rec = {"sizes":sizes,"L":L,"n":len(sizes),"patterns":len(pats),
           "volume":str(vol),"lp_float":lp,"lp_exact":str(ex) if ex else None,
           "ceil_lp":int(-(-lp//1)+ (0 if lp%1==0 else 0)) if False else None,
           "opt":opt}
    out["instances"][name]=rec

# explicit instC certificates (already machine-checked in Lean)
instC = out["instances"]["instC"]
instC["certificates"] = {
  "primal_natcover": {
    "denominator_D": 3,
    "total_weight": 9,
    "patterns_0based":[ [0,4,5,6],[2,3,5,7],[1,2,6,7],[1,2,5,8],[3,6,8],[0,7,8],[0,1,3,9],[4,9] ],
    "weights":[1,1,1,1,1,1,1,2],
    "pattern_loads":{"0-4-5-6":81,"2-3-5-7":81,"1-2-6-7":81,"1-2-5-8":81,"3-6-8":81,"0-7-8":81,"0-1-3-9":81,"4-9":78},
    "meaning":"sum_p w_p * cover_p(i) >= D for every item i, total sum = 9 = 3*D  =>  lpVal <= 9/D = 3"
  },
  "dual_natdual": {
    "denominator_D": 28,
    "weights":[1,2,2,3,6,10,11,13,14,22],
    "total_weight": 84,
    "meaning":"for every pattern p: sum_{i in p} w_i <= D, and sum_i w_i = 84 = 3*D  =>  lpVal >= 84/D = 3"
  },
  "packing_4_bins": {
    "assign": [0,0,0,1,3,0,0,1,2,3],
    "bin_loads": [77,46,40,78],
    "capacity": 81
  },
  "no_packing_3_bins": "kernel-enumerated over all 3^10 = 59049 assignments",
  "opt_number": 4, "ceil_lp": 3, "gap_opt_minus_ceil_lp": 1
}
json.dump(out, open("/home/user/Doubao/chats/38453827622628354/tcsexam-mirup/certificates.json","w"), indent=1, ensure_ascii=False)
print(json.dumps({k:v for k,v in out["instances"].items()}, indent=1)[:800])
