"""Deterministic analytical pilot for shared state; no empirical estimates."""
import json
from .economic_shared_state import *
def main():
    actors=tuple(Actor(a,k) for a,k in (("A","FIRM"),("B","FIRM"),("S","FIRM"),("O","INVESTOR"),("K","BANK")))
    s=State(actors,tuple(Position("DEPOSIT",a,"K",v) for a,v in (("A","100"),("B","20"),("O","80"))),0,"quarter","synthetic","analytical fixture")
    def p(id,firm,order,eq=0,debt=0,partial=False):
        return Project(id,firm,"S","K","O","100","0",str(eq),str(debt),order,partial,4,"analytical")
    cases={"cash":((p("a","A",("CASH",)),),{},["100"]),
           "credit_zero_substitution":((p("b","B",("DEBT","CASH","EQUITY"),80,100),),{"K":0},["100"]),
           "competition":((p("a","A",("DEBT",),0,100,True),p("b","B",("DEBT",),0,100,True)),{"K":120},["100","20"]),
           "refused":((p("b","B",("CASH",)),),{},["0"])}
    reg=json.loads((Path(__file__).resolve().parents[1]/"governance"/"transversal_enrichment_v1.json").read_text())
    rows=tuple({"id":e["id"],"disposition":"PENDING_QUALIFICATION","reason":"No scientific qualification of "+e["concept"]+" in this financial sub-ledger."} for e in reg["entries"])
    out={}
    for k,(projects,caps,expected) in cases.items():
        close,governed=run_funding(s,projects,caps,rows)
        r=governed["result"]["funding"]
        assert [x["paid_acquisition"] for x in r["result"]["projects"]]==expected
        assert sum(close.net_financial_positions().values())==0
        out[k]=r
    print(json.dumps({"status":"SYNTHETIC_COMMON_STATE_PILOT","cases":out,"coverage":validate_transversal_coverage(rows)},indent=2))
if __name__=="__main__":main()
