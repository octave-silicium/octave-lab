import unittest
from dataclasses import replace
from decimal import Decimal
from pipeline import semantic_v2 as s

H="a"*64
V="2026-11-24T04:00:00+00:00"


def cell(series="indeed_sector_total_daily", period="2024-01-01", value=Decimal("100"), **kw):
    args=dict(series=series,period=period,dimensions=s.dims("native","v1",country="FR",occupation_family="IT"),
        value=value,status="OBSERVED",vintage=V,sha256=H,source_url="https://example.org/data",locator="fixture:1",method="v1")
    args.update(kw)
    return s.Cell(**args)


class SemanticV2Tests(unittest.TestCase):
    def test_dimension_distinction(self):
        self.assertNotEqual(s.dims("Indeed","v1",occupation_family="IT"),s.dims("NACE","v1",industry="IT"))

    def test_native_unknown(self):
        self.assertEqual(s.dims("Dares","v1",region_code="")[0].value,"[source blank]")

    def test_no_unqualified_dimension(self):
        with self.assertRaises(ValueError):
            s.dims("native","v1",bogus="x")

    def test_missing_never_zero(self):
        v,flag=s.parse_value("")
        self.assertIsNone(v)
        self.assertTrue(flag)
        a=cell(value=v,status="MISSING",raw_flag=flag)
        self.assertEqual(s.release(a,"public_chart")["decision"],"BLOCK")

    def test_missing_requires_flag(self):
        with self.assertRaises(ValueError):
            cell(value=None,status="MISSING")

    def test_no_nonfinite(self):
        for v in (Decimal("NaN"),Decimal("Infinity"),Decimal("-1")):
            with self.assertRaises(ValueError):
                cell(value=v)

    def test_invalid_day(self):
        with self.assertRaises(ValueError):
            cell(period="2024-02-30")

    def test_no_cross_source(self):
        a=cell()
        b=replace(a,series="indeed_national_total_daily",period="2024-01-02")
        self.assertEqual(s.compare(a,b)["reason"],"SEMANTIC_MISMATCH")

    def test_no_cross_dimensions(self):
        a=cell()
        b=replace(a,dimensions=s.dims("native","v1",country="FR",occupation_family="Sales"),period="2024-01-02")
        self.assertEqual(s.compare(a,b)["decision"],"BLOCK")

    def test_no_cross_vintage(self):
        a=cell()
        b=replace(a,period="2024-01-02",sha256="b"*64)
        self.assertEqual(s.compare(a,b)["decision"],"BLOCK")

    def test_dares_2013(self):
        a=cell(series="dares_offers_monthly",period="2013-06")
        b=replace(a,period="2013-07")
        self.assertEqual(s.compare(a,b)["reason"],"DARES_JULY_2013_REVIEW")

    def test_no_public_authorization(self):
        a=cell()
        self.assertEqual(s.release(a,"public_chart",attributed=True)["decision"],"BLOCK")
        self.assertEqual(s.release(a,"public_chart",attributed=True,adapted_database=False)["decision"],"REVIEW_REQUIRED")

    def test_work_node_proposed_only(self):
        s.WorkNodeRef("action","candidate","a1","v1")
        with self.assertRaises(ValueError):
            s.WorkNodeRef("action","candidate","a1","v1","VALIDATED")

    def test_archive_bytes(self):
        import tempfile
        import pathlib
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/"x.csv"
            p.write_bytes(b"abc")
            self.assertEqual(s.raw_verified(p,hashlib.sha256(b"abc").hexdigest(),3),b"abc")
            with self.assertRaises(ValueError):
                s.raw_verified(p,H,3)

    def test_legacy_requires_backing(self):
        with self.assertRaises(ValueError):
            cell(series="insee_employment",period="2024Q1")

    def test_legacy_size_preserved(self):
        rows=[s.wrap(o) for o in s.v1.read_pilot() if o.series=="eurostat_ai_tany"]
        self.assertTrue(rows)
        self.assertTrue(all(any(d.kind=="enterprise_size" and d.value=="GE10" for d in c.dimensions) for c in rows))

if __name__=="__main__":
    unittest.main()
