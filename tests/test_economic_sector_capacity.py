import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure,state
from pipeline.economic_sector_capacity import Limits,allocate

class CapacityTests(unittest.TestCase):
    def setUp(self):
        # qA=.5*qB+yA; qB=yB. B uses domestic A and imported B.
        self.s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
        self.l=Limits((None,None),(None,None),(("A","B"),),"Synthetic fixture")
    def run_case(self,l=None,s=None):return allocate(s or self.s,l or self.l)["result"]
    def test_unconstrained(self):
        r=self.run_case();self.assertEqual(r["served_final"],(100,100));self.assertAlmostEqual(r["totals"]["q"],250)
    def test_equal_ration(self):
        r=self.run_case(replace(self.l,branch=(120,None)))
        self.assertEqual(r["served_final"],(80,80));self.assertAlmostEqual(r["feasible_output"][0],120)
    def test_priority_A(self):
        r=self.run_case(replace(self.l,branch=(120,None),tiers=(("A",),("B",))))
        self.assertEqual(r["served_final"],(100,40))
    def test_priority_B(self):
        r=self.run_case(replace(self.l,branch=(120,None),tiers=(("B",),("A",))))
        self.assertEqual(r["served_final"],(70,100))
    def test_import(self):
        r=self.run_case(replace(self.l,imported=(None,10)))
        self.assertEqual(r["served_final"],(50,50));self.assertAlmostEqual(r["feasible_imports"][1],10)
    def test_zero_and_unrelated(self):
        r=self.run_case(replace(self.l,imported=(None,0),tiers=(("B",),("A",))))
        self.assertEqual(r["served_final"],(100,0))
    def test_idle(self):
        r=self.run_case(replace(self.l,branch=(200,120)))
        self.assertEqual(r["idle_branch_capacity"],(50,20));self.assertIsNone(r["actual_output"])
    def test_joint_caps(self):
        r=self.run_case(replace(self.l,branch=(120,None),imported=(None,10),tiers=(("B",),("A",))))
        self.assertEqual(r["served_final"],(95,50))
    def test_invalid_tiers(self):
        with self.assertRaisesRegex(ValueError,"TIER_PARTITION"):self.run_case(replace(self.l,tiers=(("A",),("A",))))
    def test_negative(self):
        with self.assertRaisesRegex(ValueError,"LIMIT"):self.run_case(replace(self.l,branch=(-1,None)))
    def test_non_observed(self):
        with self.assertRaisesRegex(ValueError,"LIMIT_EVIDENCE"):self.run_case(replace(self.l,origin="OBSERVED"))
    def test_accounting(self):
        r=self.run_case(replace(self.l,branch=(120,None)))
        t=r["totals"];self.assertAlmostEqual(sum(r["served_final"]),t["imports"]+t["bridge"]+t["va"])
    def test_cycle(self):
        s=replace(self.s,domestic=((.2,.4),(.1,.1)),surplus=(.2,.2))
        r=self.run_case(replace(self.l,branch=(80,90)),s)
        self.assertLessEqual(r["feasible_branch_output"][0],80+1e-8)
        self.assertLessEqual(r["feasible_branch_output"][1],90+1e-8)
    def test_replay(self):
        self.assertEqual(allocate(self.s,self.l),allocate(self.s,self.l))
