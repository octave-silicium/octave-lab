import unittest
from pipeline.economic_income_bridge import reconcile,effects

class IncomeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.args=([100,200],[30,50],[10,20],[100,200],[45,73],[55,127],[30,70],[3,6],[1,2],[23,53])
    def run_bridge(self,args=None,**kw):
        return reconcile(*(args or self.args),aggregate_product_tax=kw.get("aggregate_product_tax",8),atol=1e-9)
    def test_identities(self):
        r=self.run_bridge()
        self.assertEqual(r["intermediate_valuation_bridge"],(5,3))
        for x,y in zip(r["gva_intensity"],(.55,.635)): self.assertAlmostEqual(x,y)
    def test_shock(self):
        r=effects([10,20],self.run_bridge())
        self.assertAlmostEqual(r["gva"],18.2)
        self.assertAlmostEqual(r["compensation"],10)
        self.assertAlmostEqual(r["tax"],.6)
        self.assertAlmostEqual(r["surplus_mixed"],7.6)
        self.assertAlmostEqual(r["intermediate_bridge"],.8)
        self.assertIsNone(r["employment"])
    def test_null_and_signed(self):
        r=self.run_bridge()
        self.assertEqual(effects([0,0],r)["gva"],0)
        self.assertAlmostEqual(effects([-10,-20],r)["gva"],-18.2)
    def test_bad_balance(self):
        a=list(self.args);a[-1]=[24,53]
        with self.assertRaisesRegex(ValueError,"OPERATING_ACCOUNT"): self.run_bridge(a)
    def test_bad_valuation(self):
        with self.assertRaisesRegex(ValueError,"INTERMEDIATE_VALUATION_BRIDGE"): self.run_bridge(aggregate_product_tax=9)
    def test_bad_output(self):
        a=list(self.args);a[3]=[99,200]
        with self.assertRaisesRegex(ValueError,"OUTPUT"): self.run_bridge(a)
    def test_bad_axis(self):
        a=list(self.args);a[6]=[30]
        with self.assertRaisesRegex(ValueError,"AXIS"): self.run_bridge(a)
