import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capacity_dynamics import Period,CapacityOrder,trajectory

class DynamicCapacityTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
        self.p=Period(self.s,(0,10),(("A","B"),),"synthetic")
    def run_path(self,ps=None,cap=(150,100),stock=(0,20),orders=()):
        return trajectory(ps or (self.p,)*4,cap,stock,orders,period_unit="QUARTER",evidence="synthetic")["result"]
    def test_buffer_depletion(self):
        r=self.run_path()
        self.assertAlmostEqual(r["periods"][0]["closing_stock"][1],10)
        self.assertAlmostEqual(r["periods"][1]["closing_stock"][1],0)
        self.assertAlmostEqual(sum(r["periods"][2]["served_final"]),100)
    def test_replenishment(self):
        p=replace(self.p,deliveries=(0,30))
        r=self.run_path((self.p,self.p,self.p,p))
        self.assertAlmostEqual(sum(r["periods"][3]["served_final"]),200)
        self.assertAlmostEqual(r["closing_stock"][1],10)
    def test_lag(self):
        o=CapacityOrder(1,2,"A",30,"synthetic")
        r=self.run_path(cap=(120,100),stock=(0,100),orders=(o,))
        self.assertAlmostEqual(sum(r["periods"][0]["served_final"]),160)
        self.assertAlmostEqual(sum(r["periods"][1]["served_final"]),160)
        self.assertAlmostEqual(sum(r["periods"][2]["served_final"]),200)
        self.assertEqual(r["periods"][2]["capacity"][0],150)
    def test_retirement(self):
        o=CapacityOrder(1,1,"A",-30,"synthetic")
        r=self.run_path(stock=(0,100),orders=(o,))
        self.assertEqual(r["periods"][1]["capacity"][0],120)
        self.assertAlmostEqual(sum(r["periods"][1]["served_final"]),160)
    def test_pending(self):
        r=self.run_path(orders=(CapacityOrder(4,1,"A",10,"synthetic"),))
        self.assertEqual(len(r["pending_orders"]),1)
    def test_negative_capacity(self):
        with self.assertRaisesRegex(ValueError,"NEGATIVE_COMMISSIONED_CAPACITY"):
            self.run_path(orders=(CapacityOrder(1,1,"A",-160,"synthetic"),))
    def test_no_instant_order(self):
        with self.assertRaisesRegex(ValueError,"ORDER"):
            self.run_path(orders=(CapacityOrder(1,0,"A",10,"synthetic"),))
    def test_stock_balance(self):
        r=self.run_path()
        self.assertAlmostEqual(20+r["cumulative_deliveries"][1]-r["cumulative_imported_input_use"][1],r["closing_stock"][1])
        for p in r["periods"]:self.assertAlmostEqual(p["flow_stock_residual"],0)
    def test_negative_delivery(self):
        with self.assertRaisesRegex(ValueError,"DELIVERIES"):
            self.run_path((replace(self.p,deliveries=(0,-1)),))
    def test_idle(self):
        r=self.run_path(cap=(200,150),stock=(0,100))
        self.assertAlmostEqual(r["periods"][0]["idle_capacity"][0],50)
    def test_replay(self):
        self.assertEqual(self.run_path(),self.run_path())
    def test_null_output(self):
        r=self.run_path()
        self.assertIsNone(r["actual_output"])
        self.assertIsNone(r["employment"])
