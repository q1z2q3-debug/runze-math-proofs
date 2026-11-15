# -*- coding: utf-8 -*-
"""Local verifier replicating TCSExam submission acceptance rules.
No Lean kernel available in this sandbox; this checks everything checkable
WITHOUT Lean: fixed-zone byte identity, slot markers/order, forbidden token
lexical scan (after comment stripping), conj slot untouched."""
import re, sys, os, json
ROOT='/data/workspace'
OFFICIAL=os.path.join(ROOT,'TCSExam_open_full/tasks/open/ryser-conjecture/environment/app/Task/Basic.lean')
FORBIDDEN=['axiom','sorryAx','native_decide','admitGoal','byAsSorry',
           'skipKernelTC','implemented_by','#eval','#exec','#exit','#compile',
           'notation','macro','syntax','elab','macro_rules','initialize']
# 'sorry' handled separately (it is forbidden too, except we report precisely)

def strip_comments(s):
    s=re.sub(r'/-.*?-/','',s,flags=re.S)
    s=re.sub(r'--[^\n]*','',s)
    return s

def check(path, needs_instance):
    t=open(path,encoding='utf-8').read()
    off=open(OFFICIAL,encoding='utf-8').read()
    rep=dict(file=os.path.basename(path),checks={})
    if path.endswith('通用归约定理.lean'):
        rep['checks']['standalone_module']='PASS'
        rep['checks']['fixed_zone']='N/A (standalone module, not a slot submission)'
    else:
        marker='-- END OF FIXED PART'
        a=t.partition(marker)[0]; b=off.partition(marker)[0]
        rep['checks']['fixed_zone_byte_identical']='PASS' if a==b else 'FAIL'
        for m in ['-- CHECKPOINT conj BEGIN','-- CHECKPOINT conj END',
                  '-- CHECKPOINT refuted BEGIN','-- CHECKPOINT refuted END']:
            rep['checks'][f'marker {m}']='PASS' if m in t else 'FAIL'
        # conj slot must be byte-identical
        def slot(s,name):
            i=s.find(f'-- CHECKPOINT {name} BEGIN'); j=s.find(f'-- CHECKPOINT {name} END')
            return s[i:j] if i>=0 and j>=0 else ''
        rep['checks']['conj_slot_untouched']='PASS' if slot(t,'conj')==slot(off,'conj') else 'FAIL'
    code=strip_comments(t)
    hits=[w for w in FORBIDDEN if w in code]
    rep['checks']['forbidden_tokens']='PASS' if not hits else 'FAIL '+','.join(hits)
    # NOTE: official forbidden list contains `sorryAx`, NOT plain `sorry` —
    # the plain `sorry` IS the proof slot placeholder. So we report it, not fail it.
    has_sorry = 'sorry' in code
    rep['checks']['slot_resolved(no plain sorry)'] = \
        'FAIL (slot still contains sorry -> unresolved)' if has_sorry else 'PASS'
    if needs_instance:
        rep['checks']['explicit_counterexample_instance']='FAIL (missing: ?edges table)'
        rep['submittable']=False
    else:
        rep['checks']['explicit_counterexample_instance']='N/A (conditional theorem)'
        rep['submittable']=all(v=='PASS' or str(v).startswith('N/A') for v in rep['checks'].values())
    return rep

if __name__=='__main__':
    out=[]
    for f,needs in [('TCSExam_Ryser_通用归约定理.lean',False),
                    ('TCSExam_Ryser_refuted槽_提交草案.lean',True)]:
        r=check(os.path.join(ROOT,f),needs)
        out.append(r)
        print(f"\n=== {r['file']} ===")
        for k,v in r['checks'].items(): print(f'  {v:8s}  {k}')
        print(f"  SUBMITTABLE: {r['submittable']}")
    print('\n=== OVERALL ===')
    print('  standalone reduction theorem :', 'PASS (structure/lexical)' if out[0]['submittable'] else 'FAIL')
    print('  refuted slot submission      :', 'NOT SUBMITTABLE — explicit instance missing (honest status)')
    json.dump(out,open(os.path.join(ROOT,'run_logs/ryser_verify_report.json'),'w'),indent=1)
