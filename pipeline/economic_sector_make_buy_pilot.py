"""Matched W002 make/buy comparison, entirely fictional economy and mappings."""
from dataclasses import replace
from .economic_market import InternalProduction
from .economic_sector_market_bridge_pilot import fixture as market_fixture
from .economic_sector_structural import Structure
from .economic_sector_make_buy import Allocation,MakeBuyMapping,bridge

def fixture():
    _,ms=market_fixture(); external=ms[2]; internal=ms[4]
    manual=replace(internal,id="market:make-manual",internal_production=InternalProduction("A",internal.sellers[0].reference,"Synthetic dedicated cohort, all recurring costs charged"))
    auto=replace(internal,id="market:make-auto",internal_production=InternalProduction("A",internal.sellers[0].alternative,"Synthetic dedicated cohort, all recurring costs charged"))
    s=Structure(("SERVICE","BUYER","TECH"),((.2,.1,.05),(.1,.2,.1),(.05,.05,.2)),((.1,0,0),(0,.08,0),(0,.02,.1)),((1,0,0),(0,1,0),(0,0,1)),(.35,.35,.35),(.05,.05,.05),(.02,.02,.02),(.13,.13,.13),(100,100,100),"SYNTHETIC")
    allocations=(Allocation("running","DOMESTIC","TECH","1/2"),Allocation("running","IMPORTED","TECH","1/2"),Allocation("intake","DOMESTIC","BUYER","1"),Allocation("error","DOMESTIC","BUYER","1"),Allocation("fixed:overhead","DOMESTIC","BUYER","1"),Allocation("fixed:license_maintenance","IMPORTED","TECH","1"))
    m=MakeBuyMapping("SERVICE","BUYER","12",500,"10",allocations,"Fictional ten independent cohorts; native 500 periods/year; payroll assumed D1; all recurring nonpayroll treated as CI at reference basic prices; 50/50 running origin and imported licence assumed; own activity ancillary, not sold; capital/transition excluded from recurring.")
    return s,external,manual,auto,m

def audit():
    s,e,m,a,mp=fixture()
    cases={}
    for name,x,y in (("make_manual",e,m),("make_automated",e,a)):
        r=bridge(s,x,y,mp);assert r==bridge(s,x,y,mp);cases[name]=r
    # Reverse direction requires a baseline containing the internal activity; explicit
    # recalibration to the post-make state is not silently inferred from a receipt.
    # Same assumed base supports both flows in this synthetic fixture.
    cases["buy_from_manual"]=bridge(s,m,e,mp)
    cases["buy_from_automated"]=bridge(s,a,e,mp)
    cases["manual_to_automated"]=bridge(s,m,a,mp)
    return {"fixture":"W002_MAKE_BUY_SYNTHETIC","cases":cases,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    print(json.dumps(audit(),indent=2,ensure_ascii=False))
