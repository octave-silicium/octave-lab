import copy,json,unittest
from pipeline.limitations_audit import validate,read,REG
class LimitationsTests(unittest.TestCase):
    def setUp(self):
        self.r=read(REG);self.a=read("governance/economic_mechanisms_v2.json");self.s=read("governance/shapiro_enrichment_v1.json")
    def check(self,r=None,old=None):return validate(r or self.r,self.a,self.s,old)
    def test_coverage(self):
        obs=self.check()
        self.assertEqual(len([o for o in obs if o["id"].startswith("M")]),64)
        self.assertEqual(len([o for o in obs if o["id"].startswith("SH")]),21)
        self.assertEqual(len([o for o in obs if o["id"].startswith("IF-")]),13)
        self.assertTrue(all(o["linked_limitations"] for o in obs if o["id"].startswith("M")))
    def test_duplicate(self):
        r=copy.deepcopy(self.r);r["entries"].append(r["entries"][0])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_ID"):self.check(r)
    def test_silent_removal(self):
        r=copy.deepcopy(self.r);r["entries"].pop()
        with self.assertRaisesRegex(ValueError,"SILENT_REMOVAL"):self.check(r,self.r)
    def test_invalid_mapping(self):
        r=copy.deepcopy(self.r);r["entries"][0]["mechanisms"]=["M999"]
        with self.assertRaisesRegex(ValueError,"MAPPING"):self.check(r)
    def test_cycle(self):
        r=copy.deepcopy(self.r);r["entries"][0]["dependencies"]=[r["entries"][2]["id"]]
        with self.assertRaisesRegex(ValueError,"DEPENDENCY_CYCLE"):self.check(r)
    def test_no_evidence(self):
        r=copy.deepcopy(self.r);r["entries"][0].update(status="RESOLVED",resolution_status="RESOLVED")
        with self.assertRaisesRegex(ValueError,"UNPROVEN_CLOSURE"):self.check(r)
    def test_permanent(self):
        r=copy.deepcopy(self.r);e=next(x for x in r["entries"] if x["type"]=="INTRINSIC");e.update(status="RESOLVED",resolution_status="RESOLVED")
        with self.assertRaisesRegex(ValueError,"INTRINSIC_CLOSURE"):self.check(r)
    def test_missing_source(self):
        r=copy.deepcopy(self.r);r["entries"][0]["sources"]=["missing"]
        with self.assertRaisesRegex(ValueError,"SOURCE"):self.check(r)
    def test_open_dependencies(self):
        r=copy.deepcopy(self.r);e=r["entries"][2];e.update(status="RESOLVED",resolution_status="RESOLVED",reviewer="synthetic",review_date="2026-11-25",closure_reason="fixture",closure_evidence=[{"path":REG,"criterion":"fixture","verification_ref":"fixture"}])
        with self.assertRaisesRegex(ValueError,"OPEN_DEPENDENCY"):self.check(r)
