import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure, state, compare, validate

class StructuralTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((.2,.1),(.1,.2)),((.1,0),(0,.1)),((1,0),(0,1)),(.4,.4),(.05,.05),(.02,.02),(.13,.13),(100,100),"SYNTHETIC")
    def test_null(self):
        r=compare(self.s,self.s)
        self.assertEqual(r["totals"]["q"],0)
        self.assertIsNone(r["employment"])
    def test_reallocation_only(self):
        t=replace(self.s,wage=(.3,.4),surplus=(.23,.13))
        r=compare(self.s,t)
        self.assertEqual(r["totals"]["q"],0)
        self.assertAlmostEqual(r["totals"]["va"],0)
        self.assertAlmostEqual(r["totals"]["wage"],-r["totals"]["surplus"])
    def test_domestic_to_import(self):
        t=replace(self.s,domestic=((.15,.1),(.1,.2)),imported=((.15,0),(0,.1)))
        r=compare(self.s,t)
        self.assertLess(r["totals"]["q"],0)
        self.assertGreater(r["totals"]["imports"],0)
        self.assertAlmostEqual(r["totals"]["imports"]+r["totals"]["bridge"]+r["totals"]["va"],0)
    def test_demand_only(self):
        r=compare(self.s,replace(self.s,final=(110,100)))
        self.assertAlmostEqual(sum(r["structure_shapley"]),0)
        self.assertAlmostEqual(sum(r["demand_shapley"]),r["totals"]["q"])
    def test_mixed_shapley(self):
        t=replace(self.s,domestic=((.15,.1),(.1,.2)),imported=((.15,0),(0,.1)),final=(110,100))
        r=compare(self.s,t)
        self.assertAlmostEqual(sum(r["demand_shapley"])+sum(r["structure_shapley"]),r["totals"]["q"])
        self.assertAlmostEqual(sum(map(sum,r["propagation_orders_0_1_2"]))+sum(r["propagation_order_3_plus"]),r["totals"]["q"])
    def test_capacity(self):
        r=compare(self.s,self.s,(100,200))
        self.assertGreater(r["capacity_excess_requirements"]["A"],0)
        self.assertIsNone(r["realized_output"])
    def test_invalid_account(self):
        with self.assertRaisesRegex(ValueError,"UNIT_ACCOUNT"):validate(replace(self.s,wage=(.3,.4)))
    def test_invalid_shares(self):
        with self.assertRaisesRegex(ValueError,"MARKET_SHARES"):validate(replace(self.s,shares=((1,0),(.1,1))))
    def test_negative(self):
        with self.assertRaisesRegex(ValueError,"NEGATIVE_INPUT"):validate(replace(self.s,final=(-1,100)))
    def test_nonproductive(self):
        with self.assertRaisesRegex(ValueError,"PRODUCTIVITY_BOUND"):validate(replace(self.s,domestic=((.9,.1),(.1,.2)),surplus=(-.57,.13)))
    def test_origin(self):
        with self.assertRaisesRegex(ValueError,"COMPARABILITY"):compare(self.s,replace(self.s,origin="PINNED_2022_CONDITIONAL"))
    def test_market_share_change(self):
        t=replace(self.s,shares=((.8,0),(.2,1)))
        r=compare(self.s,t)
        self.assertAlmostEqual(r["totals"]["q"],0)
        self.assertLess(r["changes"]["g"][0],0)
