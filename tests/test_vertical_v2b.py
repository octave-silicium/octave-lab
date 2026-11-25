import unittest,json
from fractions import Fraction as F
from pipeline.vertical_v2b import select,ratios,QUARTERS,build,coverage
class EconomicDataTests(unittest.TestCase):
    def test_native_exact_selection(self):
        d={"freq":["Q"],"unit":["THS_HW"],"s_adj":["SCA"],"nace_r2":["J"],"na_item":["EMP_DC"],"geo":["FR"],"time":["2019-Q1","2019-Q2","2019-Q3"]}
        j={"id":list(d),"size":[len(v) for v in d.values()],"dimension":{k:{"category":{"index":{x:i for i,x in enumerate(v)}}} for k,v in d.items()},"value":{"0":123,"1":456,"2":789},"status":{"1":"b","2":"p"}}
        s=select(j,{"unit":"THS_HW","s_adj":"SCA","na_item":"EMP_DC"},QUARTERS)
        self.assertEqual(s["levels"]["2019-Q1"]["value"],"123")
        self.assertIsNone(s["levels"]["2019-Q2"]["value"])
        self.assertEqual(s["levels"]["2019-Q3"]["value"],"789")
        self.assertIsNone(s["levels"]["2019-Q4"]["value"])
        with self.assertRaisesRegex(ValueError,"MISSING_NATIVE_SELECTOR"):select(j,{"unit":"THS_PER","s_adj":"SCA","na_item":"EMP_DC"},QUARTERS)
    def test_ratios_units_and_missing(self):
        def s(x):return {"levels":{"2019-Q1":{"value":str(x)}}}
        r=ratios({"gva_real":s(20),"total_hours":s(400),"compensation":s(12),"employee_hours":s(300),"gva_nominal":s(24),"total_persons":s(1)})
        self.assertEqual(r["real_gva_per_total_hour"]["levels"]["2019-Q1"],"50")
        self.assertEqual(r["compensation_per_employee_hour"]["levels"]["2019-Q1"],"40")
        self.assertEqual(r["employee_compensation_share"]["levels"]["2019-Q1"],"50")
        self.assertEqual(r["hours_per_person"]["levels"]["2019-Q1"],"400")
        self.assertIsNone(r["real_gva_per_total_hour"]["levels"]["2026-Q3"])
        self.assertIsNone(ratios({"gva_real":s(1),"total_hours":s(0)})["real_gva_per_total_hour"]["levels"]["2019-Q1"])
    def test_failure_and_safe_summary(self):
        r=build(lambda u:b"invalid")
        self.assertTrue(all(s["status"]=="BLOCKED" for s in r["result"]["sources"].values()))
        self.assertNotIn('"levels"',json.dumps(coverage(r)))
        self.assertEqual(r["result"]["publication"],"BLOCK_PUBLICATION")
