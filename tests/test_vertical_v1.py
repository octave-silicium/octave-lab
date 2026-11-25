import json,unittest
from decimal import Decimal
from unittest.mock import patch
from pipeline.vertical_v1 import *

class VerticalV1Tests(unittest.TestCase):
    def test_contributions_and_group_identity(self):
        raw=[("2023Q1","58",Decimal(100),1),("2023Q1","59",Decimal(200),2),("2024Q1","58",Decimal(90),3),("2024Q1","59",Decimal(220),4)]
        s=component_series(raw,("2023Q1","2024Q1"),("58","59"),"urssaf_na88_effectifs_salaries_cvs",{"a":("58",),"b":("59",)})
        c=s["same_quarter_year_on_year"][0]
        self.assertEqual(c["change"],"10")
        self.assertEqual(c["relative_change_pct"],"3.3333")
        self.assertEqual(c["components"]["58"]["contribution_to_total_growth_pp"],"-3.3333")
        self.assertEqual(c["groups"]["b"]["change"],"20")
    def test_missing_component_not_zero(self):
        raw=[("2023Q1","58",Decimal(100),1)]
        a=component_series(raw,("2023Q1","2024Q1"),("58","59"),"urssaf_na88_effectifs_salaries_cvs")
        self.assertIsNone(a["periods"][0]["total"])
        self.assertIsNone(a["same_quarter_year_on_year"][0]["change"])
    def test_duplicate_refusal(self):
        raw=[("2023Q1","58",Decimal(1),1)]*2
        with self.assertRaisesRegex(ValueError,"DUPLICATE_COMPONENT"):component_series(raw,("2023Q1",),("58",),"urssaf_na88_effectifs_salaries_cvs")
    def test_break_gate_even_if_values_exist(self):
        raw=[("2022Q1","58",Decimal(10),1),("2023Q1","58",Decimal(20),2)]
        s=component_series(raw,("2022Q1","2023Q1"),("58",),"urssaf_na88_effectifs_salaries_cvs")
        self.assertEqual(s["same_quarter_year_on_year"][0]["status"],"BLOCKED")
    def test_nonfinite_and_negative(self):
        for v in ("NaN","Infinity","-1",""):
            with self.assertRaisesRegex(ValueError,"INVALID_VALUE"):number(v)
    def test_no_unreviewed_vintage_or_public_values(self):
        old=json.loads(OLD.read_text());r=build(old,lambda _:b"changed");s=safe_summary(r)
        self.assertTrue(all(x["status"]=="BLOCKED" for x in s["sources"].values()))
        self.assertNotIn("analysis",json.dumps(s));self.assertEqual(s["publication"],"BLOCK_PUBLICATION")
    def test_adoption_comparisons_blocked(self):
        fake={"unit":"percent","population":"fixture","selected_codes":{},"selected_years":{"2023":10,"2024":20,"2025":30},"source_flags":{"2023":"b","2024":"","2025":""}}
        with patch("pipeline.vertical_v1.eurostat_ict",return_value=fake):
            a=adoption(b"fixture")
        self.assertTrue(all(c["change"] is None for c in a["comparisons"]))
    def test_safe_summary_allowlist(self):
        r={"result":{"study":"VERTICAL-001","phase":"V1","publication":"BLOCK_PUBLICATION","causal_identification":"NOT_IDENTIFIED","registry_sha256":{},"oem_comparator":{"status":"BLOCKED_MISSING_DATA"},"sources":{"x":{"status":"PARSED_INTERNAL","analysis":{"periods":[{"status":"OBSERVED_INTERNAL","total":"PRIVATE_SENTINEL"}],"same_quarter_year_on_year":[{"status":"DESCRIPTIVE_INTERNAL","change":"PRIVATE_SENTINEL"}],"other":"PRIVATE_SENTINEL"}}}},"sha256":"fixture"}
        s=json.dumps(safe_summary(r));self.assertNotIn("PRIVATE_SENTINEL",s);self.assertNotIn("analysis",s)
