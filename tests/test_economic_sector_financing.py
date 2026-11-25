import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Vintage,Investment,Period
from pipeline.economic_sector_financing import Funding,funded_path

class FinancingTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(100,80),"SYNTHETIC")
        self.a=Asset("machine","A","B",2,10,0,0,10,"synthetic")
        self.v=Vintage("machine",10,0,20)
        self.p=Period(self.s,(None,None),(("A","B"),),(1,),"synthetic")
        self.i=Investment("order","machine",1,5,2,"synthetic")
        self.f=Funding(0,10,10,0,0,0,0,0,"synthetic")
    def run_case(self,policies=None,orders=None,cash=0,debt=0,cap=(0,100),periods=None):
        policies=policies or (self.f,)*4
        return funded_path(periods or (self.p,)*len(policies),(self.a,),(self.v,), (self.i,) if orders is None else orders,policies,borrower="A",initial_cash=cash,initial_debt=debt,noncapital_capacity=cap,period_unit="YEAR",evidence="synthetic")["result"]
    def test_credit_finances_delivery(self):
        r=self.run_case()["periods"];self.assertEqual(r[0]["new_debt_draw"],10)
        self.assertEqual([x["capital"]["capacity"][0] for x in r],[100,100,150,150])
    def test_credit_ceiling(self):
        r=self.run_case((replace(self.f,debt_ceiling=4),)*4)["periods"]
        self.assertAlmostEqual(r[0]["investment_acquired"],4);self.assertAlmostEqual(r[2]["capital"]["capacity"][0],120)
    def test_no_credit(self):
        r=self.run_case((replace(self.f,new_credit_limit=0),)*4)["periods"]
        self.assertEqual(r[0]["unfinanced_investment"],10);self.assertEqual(r[2]["capital"]["capacity"][0],100)
    def test_cash_first_and_reserve(self):
        r=self.run_case((replace(self.f,cash_reserve=2),)*4,cash=5)["periods"][0]
        self.assertEqual(r["cash_used_for_acquisition"],3);self.assertEqual(r["new_debt_draw"],7);self.assertEqual(r["closing_cash"],2)
    def test_supply_rationing_no_unused_draw(self):
        r=self.run_case(cap=(0,45),cash=5)["periods"][0]
        self.assertAlmostEqual(r["investment_financially_approved"],10);self.assertAlmostEqual(r["investment_acquired"],5)
        self.assertAlmostEqual(r["new_debt_draw"],0);self.assertAlmostEqual(r["approved_but_undelivered"],5)
    def test_service(self):
        f=replace(self.f,interest_rate=.1,principal_fraction=.2,equity_injection=3)
        r=self.run_case((self.f,f),orders=())["periods"] # no opening debt, zero service
        self.assertEqual(r[1]["interest_paid"],0)
        r=self.run_case((f,),orders=(),debt=10)["periods"][0]
        self.assertAlmostEqual(r["interest_paid"],1);self.assertAlmostEqual(r["principal_paid"],2);self.assertAlmostEqual(r["closing_debt"],8)
    def test_overdue_principal_not_double_counted(self):
        f=replace(self.f,interest_rate=.1,principal_fraction=.2)
        r=self.run_case((f,replace(f,equity_injection=10)),debt=10,orders=())["periods"]
        self.assertEqual(r[0]["closing_debt"],10);self.assertEqual(r[0]["closing_principal_overdue"],2)
        self.assertAlmostEqual(r[1]["principal_due"],3.6);self.assertAlmostEqual(r[1]["interest_paid"],2);self.assertAlmostEqual(r[1]["closing_debt"],6.4)
    def test_arrears_blocks_investment(self):
        r=self.run_case((replace(self.f,interest_rate=.1,debt_ceiling=30),)*4,debt=10)["periods"][0]
        self.assertTrue(r["investment_blocked_by_arrears"]);self.assertEqual(r["investment_acquired"],0);self.assertEqual(r["closing_interest_arrears"],1)
    def test_operating_cash_is_lagged(self):
        f=replace(self.f,new_credit_limit=0,surplus_to_cash=.1)
        r=self.run_case((f,)*3,orders=(replace(self.i,period=2,lag=1),))["periods"]
        self.assertEqual(r[0]["closing_cash"],5);self.assertEqual(r[1]["investment_acquired"],5);self.assertEqual(r[2]["capital"]["capacity"][0],125)
    def test_operating_loss_arrears(self):
        f=replace(self.f,other_operating_cash=-4)
        r=self.run_case((f,self.f),orders=(replace(self.i,period=2),),cash=1)["periods"]
        self.assertEqual(r[0]["closing_operating_arrears"],3);self.assertTrue(r[1]["investment_blocked_by_arrears"]);self.assertEqual(r[1]["new_debt_draw"],0)
    def test_ceiling_breach_visible(self):
        r=self.run_case((replace(self.f,debt_ceiling=5),),orders=(),debt=10)["periods"][0]
        self.assertEqual(r["debt_ceiling_breach"],5)
    def test_multiple_orders(self):
        r=self.run_case((replace(self.f,new_credit_limit=10),)*4,orders=(self.i,replace(self.i,id="second")) )["periods"][0]
        self.assertAlmostEqual(r["investment_acquired"],10);self.assertEqual(len(r["capital"]["investment_orders"]),2)
        self.assertAlmostEqual(r["capital"]["investment_orders"][0]["acquired_units"],2.5)
    def test_no_lookahead(self):
        a=self.run_case()["periods"][0];b=self.run_case((self.f,replace(self.f,equity_injection=100)))["periods"][0]
        self.assertEqual(a,b)
    def test_invalid_rate(self):
        with self.assertRaisesRegex(ValueError,"RATES"):self.run_case((replace(self.f,interest_rate=-.1),),orders=())
    def test_invalid_order(self):
        with self.assertRaisesRegex(ValueError,"ORDER_SCOPE"):self.run_case(orders=(replace(self.i,units=-1),))
    def test_replay_and_nulls(self):
        a=self.run_case();self.assertEqual(a,self.run_case());self.assertIsNone(a["actual_default"]);self.assertIsNone(a["actual_profit"])
