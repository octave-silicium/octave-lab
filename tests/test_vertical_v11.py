import unittest
from decimal import Decimal
from pipeline.vertical_v1 import component_series
from pipeline.vertical_v11 import diagnostic,summarize,audit,OLD
import json
class CoverageTests(unittest.TestCase):
    def test_dpae_hold(self):
        a=component_series([("2024Q1","x",Decimal(10),1),("2025Q1","x",Decimal(11),2)],("2024Q1","2025Q1"),("x",),"urssaf_dpae_na38_quarterly")
        a=diagnostic(a,"dpae")
        self.assertEqual(a["periods"][1]["status"],"CANDIDATE_REVISED_VINTAGE_REVIEW")
        self.assertIsNone(a["same_quarter_year_on_year"][0]["change"])
        self.assertNotIn("components",a["same_quarter_year_on_year"][0])
        self.assertEqual(summarize(a)["candidate_periods"],["2025Q1"])
    def test_break_preserved(self):
        a=component_series([("2022Q1","x",Decimal(10),1),("2023Q1","x",Decimal(11),2)],("2022Q1","2023Q1"),("x",),"urssaf_na88_effectifs_salaries_cvs")
        a=diagnostic(a,"employment")
        self.assertEqual(a["same_quarter_year_on_year"][0]["status"],"BLOCKED")
        self.assertNotEqual(a["periods"][0]["segment"],a["periods"][1]["segment"])
    def test_changed_vintage(self):
        a=audit(json.loads(OLD.read_text()),lambda u:b"new")
        self.assertTrue(all(r["status"]=="BLOCKED" for r in a["sources"].values()))
