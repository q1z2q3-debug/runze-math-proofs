import json, time, signal
from ryser_sat import decide, exact_verify

class TO(Exception): pass
def handler(s,f): raise TO()
signal.signal(signal.SIGALRM, handler)

params=[(4,4,16,5),(4,5,16,5),(4,6,16,5),(4,5,17,5),(5,5,25,6),(5,6,25,6)]
out=[]
for R,NV,NE,D in params:
    t=time.time(); signal.alarm(75)
    try:
        res,E,info = decide(R,NV,NE,D,verbose=False)
        signal.alarm(0)
        line={"R":R,"NV":NV,"NE":NE,"D":D,"result":res,"elapsed":round(time.time()-t,1)}
        if res=='SAT':
            v=exact_verify(E,R,NV,D)
            line["verify"]=v
        out.append(line)
    except TO:
        out.append({"R":R,"NV":NV,"NE":NE,"D":D,"result":"TIMEOUT","elapsed":75})
    except Exception as e:
        out.append({"R":R,"NV":NV,"NE":NE,"D":D,"result":"ERR","err":str(e)[:100]})
    print(json.dumps(out[-1],ensure_ascii=False)[:300], flush=True)
json.dump(out,open("frontier.json","w"),indent=1)
