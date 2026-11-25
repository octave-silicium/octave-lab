"""Independent benchmark: ONS 1 April 2022 guidance, explicitly fictional Table 1."""
from dataclasses import replace
from fractions import Fraction as F
from .economic_sector import Table,run

def fixture():
    z=((700,200,1200,8000),(10,50,20,3000),(1000,240,900,6500),(15000,17000,16500,150000))
    x=(24765,28830,25595,553250)
    # Table 1 gives columns, not final demand. Infer rows as output minus domestic intermediate uses.
    y=tuple(x[i]-sum(z[i]) for i in range(4))
    return Table("sector:ons-guide",1,"UK fictional",2022,"ONS fictional products","GBP million","BASIC_CURRENT","https://www.ons.gov.uk/economy/nationalaccounts/supplyandusetables/articles/inputoutputanalyticaltables/guidanceforuse","OFFICIAL_FICTIONAL_BENCHMARK",("cheese","pastries","milk","other"),z,x,(500,110,350,15000),(15,10,5,750),(7540,11220,6620,370000),y)

def audit():
    t=fixture();out={}
    for k,delta,cap in (("null",(0,0,0,0),None),("cheese",(100,0,0,0),None),("pastries",(0,100,0,0),None),("decline",(-100,0,0,0),None),("capacity_stress",(100,0,0,0),tuple(t.output))):
        r=run(t,delta,cap);assert r==run(t,delta,cap);out[k]=r
    # ONS publishes rounded effects and inverse; match at published precision.
    b=out["cheese"]["result"]
    assert abs(F(b["gross_output_requirement_change"])-F("202.8"))<F("0.2")
    assert abs(F(b["gross_value_added_requirement_change"])-F("95.1"))<F("0.15")
    assert abs(F(b["imported_intermediate_requirement_change"])-F("4.7"))<F("0.15")
    return {"fixture":"ONS_IO_EXTERNAL_FICTIONAL_BENCHMARK","table":__import__("dataclasses").asdict(t),"cases":out,"ons_published_rounded":{"output":202.8,"gva":95.1,"imports":4.7,"intermediate_taxes":0.2},"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}

if __name__=="__main__":
    import json
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
