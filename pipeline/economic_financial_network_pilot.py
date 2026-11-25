"""Independent exact benchmarks for regular clearing networks."""
import json
from fractions import Fraction as F
from .economic_financial_network import clear,credit_headroom
def audit():
    r=clear(("A","B","C"),((0,80,0),(0,0,60),(0,0,0)),(20,20,50),(50,0,0),evidence="Synthetic")
    assert r["result"]["payments"]==["50","40","30"]
    policies={}
    for loss,expected in [("0",300),("1/2",100),("1",0)]:
        c=credit_headroom(r,"B",capital=50,existing_rwa=200,minimum_ratio="1/10",new_risk_weight=1,credit_limit=300,loss_recognition=loss,requests={"A":100,"C":200},evidence="Synthetic")
        assert F(c["result"]["approved_total"])==expected;policies[loss]=c
    topologies={}
    for name,L,expected in [
      ("pairs",((0,80,0,0),(80,0,0,0),(0,0,0,80),(0,0,80,0)),[F(400,9),F(500,9),100,100]),
      ("cycle",((0,80,0,0),(0,0,80,0),(0,0,0,80),(80,0,0,0)),[F(2500,41),F(2820,41),F(3076,41),F(3281,41)])]:
        c=clear(("A","B","C","D"),L,(20,)*4,(0,20,20,20),evidence="Synthetic")
        # For the cycle, independently derive A: A=.8*(20+.8*(20+.8*(20+.8*A))).
        if name=="cycle":
            a=(F(4,5)*20+F(4,5)**2*20+F(4,5)**3*20)/(1-F(4,5)**4)
            expected=[a]
            for _ in range(3):expected.append(20+F(4,5)*expected[-1])
        assert list(map(F,c["result"]["payments"]))==expected
        topologies[name]=c
    return {"status":"SYNTHETIC_NETWORK_AUDIT","chain":r,"credit":policies,"topologies":topologies}
if __name__=="__main__":print(json.dumps(audit(),indent=2))
