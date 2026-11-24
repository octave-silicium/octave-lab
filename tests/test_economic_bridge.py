import unittest
from dataclasses import replace
from decimal import Decimal
from pipeline.economic_core import *
from pipeline.economic_calculations import Calculation,calculate
from pipeline.economic_investigation import Investigation,assemble,verify_replay
from pipeline.economic_native import from_record
from pipeline import semantic_v4 as v4

S=Scope("fictional invoice desk","FR","synthetic","2026-01-01","2026-12-31","nominal EUR 2026")
def fixture():
    e=Evidence("fixture:a",1,"ASSUMPTION","synthetic","fixture","a"*64,"fixture","2026-11-24",None,"INTERNAL_ONLY","ASSUMED")
    a=Parameter("fixture:minutes",1,S,Quantity(Decimal("6"),"MINUTE_PER_UNIT"),"ASSUMPTION",(e.key,),"minutes per invoice")
    b=Parameter("fixture:volume",1,S,Quantity(Decimal("100"),"UNIT"),"ASSUMPTION",(e.key,),"invoices")
    c=Claim("fixture:hours",1,"CONDITIONAL_SCENARIO","Illustrative total","planning",S,Quantity(Decimal("10"),"HOUR"),(e.key,),("M010",),"6 min x 100 / 60","synthetic only","different workload","field measurement",(),(a.key,b.key))
    return Graph(Requirements(),evidence=(e,),parameters=(a,b),claims=(c,)),Calculation("fixture:calc",1,"LABOR_HOURS",(a.key,b.key),c.key)
class V02(unittest.TestCase):
    def test_calculation(self):
        g,c=fixture();self.assertEqual(calculate(g,c)["result"],"10")
    def test_units(self):
        g,c=fixture()
        with self.assertRaisesRegex(ValueError,"CALC_UNITS"):calculate(g,replace(c,operation="LABOR_COST"))
    def test_fabricated_number(self):
        g,c=fixture();bad=replace(g.claims[c.output_claim_ref],quantity=Quantity(Decimal("11"),"HOUR"))
        other=Graph(g.requirements,evidence=tuple(g.evidence.values()),parameters=tuple(g.parameters.values()),claims=(bad,))
        with self.assertRaisesRegex(ValueError,"CALC_RESULT_MISMATCH"):calculate(other,c)
    def test_manifest(self):
        g,c=fixture();rows=tuple(Coverage(k,i,"PENDING_QUALIFICATION","fixture only") for k,ids in g.requirements.groups.items() for i in sorted(ids))
        inv=Investigation("fixture:investigation",1,"Workload?","test decision",("baseline","alternative"),"hours","synthetic",g.fingerprint,"b"*64)
        result=assemble(inv,g,rows,(c,))
        self.assertEqual(len(result["manifest"]["sections"]),18)
        self.assertTrue(verify_replay(result,inv,g,rows,(c,)))
        with self.assertRaisesRegex(ValueError,"UNREPRODUCED"):assemble(inv,g,rows)
        with self.assertRaisesRegex(ValueError,"REPLAY_MISMATCH"):verify_replay(result,replace(inv,question="changed"),g,rows,(c,))
    def test_archive_real(self):
        rows=tuple(v4.wrap_archive(x) for x in v4.v2.iter_indeed(only_series="indeed_national_total_daily"))
        valid=[r for r in rows if r.quality[0]=="DESCRIPTIVE_ONLY" and r.value is not None]
        self.assertTrue(valid)
        e,c=from_record(valid[0]);self.assertEqual(c.quantity.value,valid[0].value);self.assertEqual(e.sha256,valid[0].sha256)
