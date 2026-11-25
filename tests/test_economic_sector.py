import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_sector import run,validate
from pipeline.economic_sector_pilot import fixture,audit

class SectorTests(unittest.TestCase):
    def setUp(self):self.t=fixture()
    def test_benchmark(self):self.assertEqual(len(audit()["cases"]),5)
    def test_null(self):self.assertEqual(run(self.t,(0,0,0,0))["result"]["gross_output_requirement_change"],"0")
    def test_row_balance(self):
        with self.assertRaisesRegex(ValueError,"ROW_BALANCE"):validate(replace(self.t,final_domestic=(1,2,3,4)))
    def test_column_balance(self):
        with self.assertRaisesRegex(ValueError,"COLUMN_BALANCE"):validate(replace(self.t,imports=(501,110,350,15000)))
    def test_negative(self):
        with self.assertRaisesRegex(ValueError,"NEGATIVE_FINAL_USE"):run(self.t,(-100000,0,0,0))
    def test_capacity(self):
        r=run(self.t,(100,0,0,0),self.t.output)["result"]
        self.assertEqual(r["capacity_status"],"REQUIREMENTS_EXCEED_CAPACITY");self.assertIsNone(r["realized_output_change"])
    def test_bad_capacity(self):
        with self.assertRaisesRegex(ValueError,"CAPACITY_BASELINE"):run(self.t,(1,0,0,0),(1,2,3,4))
    def test_decomposition(self):
        r=run(self.t,(100,0,0,0))["result"]
        self.assertEqual(sum(F(r[k]) for k in ("gross_value_added_requirement_change","imported_intermediate_requirement_change","intermediate_product_tax_change")),100)
        self.assertIsNone(r["gdp_change"]);self.assertIsNone(r["employment_change"])
    def test_linearity(self):
        a=run(self.t,(100,0,0,0))["result"];b=run(self.t,(-100,0,0,0))["result"]
        self.assertEqual(F(a["gross_output_requirement_change"]),-F(b["gross_output_requirement_change"]))
    def test_metadata(self):
        with self.assertRaisesRegex(ValueError,"TABLE_METADATA"):validate(replace(self.t,price_basis="PURCHASER"))
    def test_replay(self):self.assertEqual(run(self.t,(100,0,0,0)),run(self.t,(100,0,0,0)))
