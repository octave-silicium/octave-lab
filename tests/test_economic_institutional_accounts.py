import unittest
from decimal import Decimal as D
from pipeline.economic_institutional_bridge import transportation_bounds,proportional_shock
class InstitutionalBridgeTests(unittest.TestCase):
    def test_exact_extrema(self):
        r=transportation_bounds({"A":6,"B":4},{"X":7,"Y":3})
        candidates=[(x,6-x,7-x,x-3) for x in range(3,7)]
        for i,c in enumerate(r["cells"]):
            self.assertEqual(D(c["lower"]),min(x[i] for x in candidates))
            self.assertEqual(D(c["upper"]),max(x[i] for x in candidates))
    def test_discrepancy(self):
        r=transportation_bounds({"A":"1.2"},{"X":"1.8"})
        self.assertEqual(r["rows"]["UNALLOCATED_RESIDUAL"],"0.6")
        self.assertEqual(r["original_row_minus_column"],"-0.6")
    def test_reverse_discrepancy(self):
        r=transportation_bounds({"A":5},{"X":4})
        self.assertEqual(r["columns"]["UNALLOCATED_RESIDUAL"],"1")
    def test_zero(self):
        r=transportation_bounds({"A":0,"B":1},{"X":1})
        self.assertEqual(r["cells"][0]["upper"],"0")
    def test_invalid(self):
        with self.assertRaisesRegex(ValueError,"NONNEGATIVE"):transportation_bounds({"A":-1},{"X":1})
    def test_reserved(self):
        with self.assertRaisesRegex(ValueError,"RESERVED_AXIS"):transportation_bounds({"UNALLOCATED_RESIDUAL":1},{"X":1})
    def test_shock(self):
        r=transportation_bounds({"A":6,"B":4},{"X":7,"Y":3})
        x=proportional_shock(r,"A",-3)
        self.assertEqual((D(x[0]["lower"]),D(x[0]["upper"])),(D(-3),D("-1.5")))
    def test_excessive_shock(self):
        r=transportation_bounds({"A":6},{"X":6})
        with self.assertRaisesRegex(ValueError,"SHOCK"):proportional_shock(r,"A",-7)
