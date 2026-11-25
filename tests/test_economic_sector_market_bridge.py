import unittest
from dataclasses import replace
from pipeline.economic_sector_market_bridge_pilot import fixture,mapping
from pipeline.economic_sector_market_bridge import bridge,BuyerUse

class SectorMarketBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m=fixture()
    def test_demand_vs_intermediate(self):
        a,b=self.m[:2]
        f=bridge(self.s,a,b,mapping(a,b))["result"]
        i=bridge(self.s,a,b,mapping(a,b,"INTERMEDIATE_DOMESTIC"))["result"]
        self.assertAlmostEqual(sum(f["sector"]["structure_shapley"]),0)
        self.assertAlmostEqual(sum(i["sector"]["demand_shapley"]),0)
    def test_no_volume(self):
        a,b=self.m[0],self.m[3]
        r=bridge(self.s,a,b,mapping(a,b))["result"]
        self.assertEqual(r["market"]["before_sales"],r["market"]["after_sales"])
        self.assertAlmostEqual(r["sector"]["totals"]["q"],0)
    def test_price_only_not_propagated(self):
        a,b=self.m[0],self.m[3]
        r=bridge(self.s,a,b,mapping(a,b))["result"]
        self.assertNotEqual(r["market"]["price_component_eur_per_cohort"],"0")
        self.assertAlmostEqual(r["flows"][0]["delta_reference_mEUR"],0)
    def test_quantity_mismatch(self):
        a,b=self.m[:2];m=mapping(a,b);u=m.uses[0]
        with self.assertRaisesRegex(ValueError,"USE_RECONCILIATION"):bridge(self.s,a,b,replace(m,uses=(replace(u,after=u.after+1),)))
    def test_internalization_block(self):
        a,b=self.m[0],self.m[4]
        with self.assertRaisesRegex(ValueError,"INTERNALIZATION"):bridge(self.s,a,b,mapping(a,b))
    def test_coverage(self):
        a,b=self.m[:2]
        with self.assertRaisesRegex(ValueError,"BASE_COVERAGE"):bridge(self.s,a,b,mapping(a,b,weight="1000000"))
    def test_observed_block(self):
        a,b=self.m[:2]
        with self.assertRaisesRegex(ValueError,"ADMISSION"):bridge(replace(self.s,origin="PINNED_2022_CONDITIONAL"),a,b,mapping(a,b))
    def test_missing_evidence(self):
        a,b=self.m[:2]
        with self.assertRaisesRegex(ValueError,"EVIDENCE"):bridge(self.s,a,b,replace(mapping(a,b),scale_evidence=""))
    def test_unknown_buyer(self):
        a,b=self.m[:2];m=mapping(a,b)
        with self.assertRaisesRegex(ValueError,"USE_CLASS"):bridge(self.s,a,b,replace(m,uses=(BuyerUse("INTERMEDIATE_DOMESTIC","UNKNOWN",m.uses[0].before,m.uses[0].after),)))
