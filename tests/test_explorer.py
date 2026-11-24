import unittest
from decimal import Decimal
from pipeline.explorer import Explorer,archive_catalog,LazyExplorer,series_key
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

    def test_native_search_and_facet_counts(self):
        s="insee_employment"
        self.assertTrue(self.x.discover(s,{},"industrie")["total"]>=1)
        d=self.x.discover(s,{},"tertiaire marchand")
        self.assertTrue(d["total"]>=1)
        self.assertEqual(self.x.discover(s,{},"impossible_xyz")["total"],0)
        self.assertEqual(self.x.discover(s,{},"INDUSTRIE")["total"],self.x.discover(s,{},"industrie")["total"])
        g=self.x.discover(s,{})["series"][0]
        filtered=self.x.discover(s,{"industry":g["dimensions"]["industry"]})
        self.assertGreater(len(filtered["choices"]["industry"]),1)
    def test_temporal_windows(self):
        d=self.x.detail("indeed_national_total_daily","0")
        w=d["windows"][0]
        self.assertEqual(w["count"],30)
        self.assertEqual(self.x.detail("indeed_national_total_daily","0",w["start"],w["end"])["total"],30)
    def test_comparison_gate_no_change(self):
        s="indeed_national_total_daily"
        d=self.x.comparison(s,"0","2020-02-01","2020-02-02")
        self.assertEqual(d["decision"],"REVIEW_REQUIRED")
        self.assertIsNone(d["change"])
        d=self.x.comparison(s,"0","2019-01-01","2020-02-02")
        self.assertEqual(d["reason"],"MISSING_ENDPOINT")
    def test_comparison_restricted_interval(self):
        dims=tuple(sorted((k,"native") for k in v4.v3.URSSAF["urssaf_dpae_na38"]["dims"]))
        cells=[v4.wrap_live(v4.v3.Cell("urssaf_dpae_na38",p,dims,"dpae_cvs","declarations",Decimal("20"),"","a"*64,"2026-11-24T06:00:00+00:00","fixture")) for p in ("2025Q1","2025Q2","2025Q4")]
        d=Explorer(v4.Catalog(cells)).comparison("urssaf_dpae_na38","0","2025Q1","2025Q4")
        self.assertEqual(d["reason"],"QUALITY_RESTRICTION_IN_INTERVAL")
        self.assertIsNone(d["change"])

    def test_stable_identity(self):
        source="indeed_sector_total_daily"
        g=self.x.discover(source,{})["series"][0]
        self.assertEqual(len(g["id"]),64)
        self.assertEqual(g["id"],series_key(source,g["dimensions"].items(),g["measure"],g["unit"]))
        self.assertEqual(self.x.detail(source,g["id"])["id"],g["id"])
        self.assertNotEqual(g["id"],series_key(source,g["dimensions"].items(),g["measure"],"other"))
    def test_lazy_scope_and_restore(self):
        source="indeed_national_total_daily"
        calls=[]
        def loader(s):
            calls.append(s)
            return v4.Catalog(self.x.catalog.by[s])
        x=LazyExplorer(loader=loader)
        self.assertEqual(len(x.sources()),4)
        self.assertEqual(calls,[])
        g=x.discover(source,{})["series"][0]
        d=x.detail(source,g["id"])
        self.assertEqual(calls,[source])
        self.assertEqual(x.restore(source,g["id"],d["snapshot_sha256"])["decision"],"MATCH")
        self.assertEqual(x.restore(source,g["id"],"0"*64)["decision"],"VINTAGE_MISMATCH")
        self.assertEqual(calls,[source])
        with self.assertRaises(ValueError):x.get("eurostat_nace")
    def test_lazy_failure_isolated(self):
        source="indeed_national_total_daily"
        def loader(s):
            if s=="dares_offers_monthly":raise OSError("fixture")
            return v4.Catalog(self.x.catalog.by[s])
        x=LazyExplorer(loader=loader)
        with self.assertRaises(OSError):x.get("dares_offers_monthly")
        self.assertEqual(x.discover(source,{})["total"],1)
    def test_real_selective_loader(self):
        from pipeline.explorer import load_source
        source="indeed_national_total_daily"
        cat=load_source(source)
        self.assertEqual(set(cat.by),{source})
        self.assertEqual(len(cat.by[source]),2478)
