import unittest
import tempfile
from pathlib import Path
from dataclasses import replace
from decimal import Decimal
from pipeline import semantic_v4 as s

H="a"*64
V="2026-11-24T06:00:00+00:00"

def euro(period="2024",flag="",value=Decimal("40"),**kwargs):
    args=dict(source="eurostat_nace",period=period,dimensions=tuple(sorted(dict(freq="A",geo="FR",indic_is="E_AI_TANY",nace_r2="J",size_emp="GE10",unit="PC_ENT").items())),measure="E_AI_TANY",unit="PC_ENT",value=value,flag=flag,sha256=H,vintage=V,locator="fixture")
    args.update(kwargs)
    return s.wrap_live(s.v3.Cell(**args))

def dpae(period="2025Q2"):
    d=tuple(sorted((k,"native") for k in s.v3.URSSAF["urssaf_dpae_na38"]["dims"]))
    return s.wrap_live(s.v3.Cell("urssaf_dpae_na38",period,d,"dpae_cvs","declarations",Decimal(12),"",H,V,"fixture"))

class UnifiedTests(unittest.TestCase):
    def test_flags(self):
        self.assertEqual(s.flag_reasons("bu"),("SERIES_BREAK","LOW_RELIABILITY"))
        self.assertEqual(euro(flag="u").quality[0],"RESTRICTED")
        self.assertEqual(euro(flag="b").quality[0],"REVIEW_REQUIRED")
        self.assertEqual(euro(flag="x").quality[0],"RESTRICTED")

    def test_confidential(self):
        self.assertIsNone(euro(flag="|C").internal_result()["value"])

    def test_missing(self):
        self.assertEqual(euro(flag="u",value=None).quality[0],"WITHHELD")

    def test_dpae_quality(self):
        self.assertEqual(dpae().quality[0],"RESTRICTED")
        self.assertEqual(dpae("2024Q4").quality[0],"DESCRIPTIVE_ONLY")

    def test_compare(self):
        self.assertEqual(s.compare(euro(),euro("2025")),"BLOCK_2025_DEFINITION_REVIEW")
        self.assertEqual(s.compare(euro(),euro("2025",flag="u")),"BLOCK_QUALITY")
        self.assertEqual(s.compare(dpae("2024Q4"),dpae("2025Q4")),"BLOCK")

    def test_query(self):
        c=s.Catalog([euro("2023"),euro("2024"),euro("2025",flag="b")])
        q=c.query("eurostat_nace",{"geo":"FR"},limit=1)
        self.assertEqual(q["total"],3)
        self.assertEqual(q["next_offset"],1)
        self.assertEqual(c.query("eurostat_nace",offset=2,limit=1)["records"][0]["raw_flag"],"b")
        self.assertTrue(c.query("eurostat_nace",{"geo":"DE"})["zero_results_means_no_coverage"])
        with self.assertRaises(ValueError):
            c.query("eurostat_nace",{"occupation":"J"})
        with self.assertRaises(ValueError):
            c.query("eurostat_nace",start="2024Q1")
        with self.assertRaises(PermissionError):
            c.query("eurostat_nace",purpose="public_chart")

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            s.Catalog([euro(),euro()])

    def test_vintage(self):
        with self.assertRaises(ValueError):
            s.Catalog([euro(),euro("2025",vintage="2026-11-25T00:00:00+00:00")])

    def test_native_cannot_be_changed(self):
        with self.assertRaises(ValueError):
            replace(euro(),value=Decimal(42))

    def test_pilot_excluded(self):
        cells=s.v2.v1.read_pilot()
        with self.assertRaises(ValueError):
            s.wrap_archive(s.v2.wrap(cells[0]))

    def test_vault(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):
                s.local_vintage_store(d,"eurostat_nace",b"test",retrieved_at=V)
            a=s.local_vintage_store(d,"eurostat_nace",b"test",retrieved_at=V,approved=True)
            self.assertEqual(a,s.local_vintage_store(d,"eurostat_nace",b"test",retrieved_at=V,approved=True))
            p=Path(d)/"eurostat_nace"/a["sha256"]/"original.bin"
            p.write_bytes(b"tamper")
            with self.assertRaises(ValueError):
                s.local_vintage_store(d,"eurostat_nace",b"test",retrieved_at=V,approved=True)

    def test_vault_repo_forbidden(self):
        with self.assertRaises(ValueError):
            s.local_vintage_store(s.v2.ROOT/"private","eurostat_nace",b"test",retrieved_at=V,approved=True)
