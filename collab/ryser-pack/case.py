import sys, json, time
from ryser_sat import decide, exact_verify
R,NV,NE,D = map(int, sys.argv[1:5])
t=time.time()
res,E,info = decide(R,NV,NE,D,verbose=False)
line={"R":R,"NV":NV,"NE":NE,"D":D,"result":res,"elapsed":round(time.time()-t,1)}
line.update(info)
if res=="SAT":
    line["verify"]=exact_verify(E,R,NV,D); line["E"]=E
print(json.dumps(line,ensure_ascii=False)[:1500])
