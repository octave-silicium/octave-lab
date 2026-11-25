import unittest,json
from unittest.mock import patch
from pipeline.vertical_v0 import audit,OLD,SOURCES

class VerticalV0Tests(unittest.TestCase):
    def test_failure_independent_and_no_causal_claim(self):
        old=json.loads(OLD.read_text())
        def fetch(u):
            if u==SOURCES["urssaf_headcount"]:raise TimeoutError("test")
            return b"fixture"
        parsers={k:(n,lambda b, v=old["selected_studies"][n]:v) for k,n in (("urssaf_headcount","private_employment"),("urssaf_dpae","dpae"),("eurostat_ai","ai_adoption"))}
        with patch("pipeline.vertical_v0.PARSERS",parsers):
            a=audit(old,fetch)
        self.assertEqual(a["parsed_sources"],2)
        self.assertEqual(a["sources"]["urssaf_headcount"]["status"],"BLOCKED")
        self.assertEqual(a["publication"],"BLOCK_PUBLICATION")
        self.assertEqual(a["historical_reproduction"],"NOT_ESTABLISHED")
        self.assertNotIn("selected_studies",a)
        self.assertTrue(a["sources"]["urssaf_dpae"]["2025_excluded"])
        self.assertTrue(a["sources"]["eurostat_ai"]["blocked_comparisons_preserved"])
