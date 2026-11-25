"""Synthetic end-to-end W002 replay; no claim of a real market or A38 mapping."""
from dataclasses import replace
from .economic_market import run
from .economic_market_pilot import cases
from .economic_physical_pilot import make
from .work_graph import build
from .economic_sector_structural import Structure
from .economic_sector_market_bridge import Mapping,BuyerUse,bridge

def fixture():
    p,_=make(build());markets=cases(p)
    s=Structure(("SERVICE","BUYER"),((.2,.1),(.1,.2)),((.1,0),(0,.1)),((1,0),(0,1)),(.4,.4),(.05,.05),(.02,.02),(.13,.13),(100,100),"SYNTHETIC")
    return s,markets

def mapping(a,b,kind="FINAL_DOMESTIC",weight="10"):
    x,z=run(a)["result"],run(b)["result"]
    return Mapping("SERVICE","Fictional domestic economy",2022,"EUR_MILLION_REFERENCE_BASIC_PRICE","100",100,weight,(BuyerUse(kind,None if kind=="FINAL_DOMESTIC" else "BUYER",x["sales"],z["sales"]),),"Fictional homogeneous service mapped to SERVICE","10 disjoint hypothetical cohorts unless varied; no representativeness claim","Hypothetical fixed basic price EUR 100 per report")

def audit():
    s,m=fixture()
    out={}
    for name,t in [("first_mover",m[1]),("diffusion",m[2]),("constant_demand",m[3]),("retain_gain",m[6])]:
        for k in ("FINAL_DOMESTIC","INTERMEDIATE_DOMESTIC"):
            r=bridge(s,m[0],t,mapping(m[0],t,k))
            assert r==bridge(s,m[0],t,mapping(m[0],t,k))
            out[name+":"+k]=r
    try: bridge(s,m[0],m[4],mapping(m[0],m[4]))
    except ValueError as e: blocked=str(e)
    else: raise AssertionError("INTERNALIZATION_ADMITTED")
    return {"fixture":"W002_SYNTHETIC_TWO_BRANCH","cases":out,"internalization_block":blocked,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    print(json.dumps(audit(),indent=2,ensure_ascii=False))
