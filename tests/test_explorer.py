import unittest
from decimal import Decimal
from pipeline.explorer import Explorer,archive_catalog
from pipeline import semantic_v4 as v4

class ExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x=Explorer(archive_catalog())
    def test_sources(self):
        self.assertEqual(len(self.x.sources()),4)
    def test_real_indeed(self):
        s="indeed_national_total_daily"
        self.assertEqual(self.x.discover(s,{})["total"],1)
        d=self.x.detail(s,"0","2020-02-01","2020-02-02")
        self.assertEqual(d["total"],2)
        self.assertEqual(Decimal(d["points"][0]["value"]),Decimal(100))
        self.assertEqual(d["publication"],"BLOCK_PUBLICATION")
    def test_exact_dimensions(self):
        s="indeed_sector_total_daily"
        d=self.x.discover(s,{})
        self.assertEqual(d["total"],34)
        f=d["choices"]["occupation_family"][0]["value"]
        self.assertEqual(self.x.discover(s,{"occupation_family":f})["total"],1)
        self.assertEqual(self.x.discover(s,{"occupation_family":"not_a_family"})["total"],0)
        with self.assertRaises(ValueError): self.x.discover(s,{"industry":"J"})
    def test_pages(self):
        d=self.x.detail("indeed_national_total_daily","0")
        self.assertEqual(len(d["records"]),50)
        self.assertEqual(d["next_offset"],50)
        self.assertEqual(self.x.detail("indeed_national_total_daily","0",offset=50)["offset"],50)
    def test_proof(self):
        r=self.x.point("indeed_national_total_daily","0","2020-02-01")
        self.assertEqual(len(r["sha256"]),64)
        self.assertEqual(Decimal(r["value"]),Decimal(100))
    def test_invalid(self):
        for p in ("2024Q1","2026-02-31"):
            with self.assertRaises(ValueError): self.x.detail("indeed_national_total_daily","0",p)
        with self.assertRaises(ValueError): self.x.detail("indeed_national_total_daily","999")
    def test_insee(self):
        d=self.x.discover("insee_employment",{})
        self.assertEqual(d["total"],10)
        self.assertEqual(self.x.detail("insee_employment","0")["total"],50)
    def test_live_mask(self):
        c=v4.v3.Cell("eurostat_nace","2025",tuple(sorted(dict(freq="A",geo="FR",indic_is="E_AI_TANY",nace_r2="J",size_emp="GE10",unit="PC_ENT").items())),"E_AI_TANY","PC_ENT",Decimal("42"),"|C","a"*64,"2026-11-24T06:00:00+00:00","fixture")
        d=Explorer(v4.Catalog([v4.wrap_live(c)])).detail("eurostat_nace","0")
        self.assertIsNone(d["points"][0]["value"])
        self.assertIsNone(d["records"][0]["value"])
