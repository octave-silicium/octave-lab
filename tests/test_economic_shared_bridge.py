import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_shared_state import Actor,Position,State,Project
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Period,Investment
from pipeline.economic_shared_bridge import *

def fixture(loss="0",cap=300,noncap=(1,1,1),cash_b="0",owner="0",order=("DEBT",)):
    actors=(Actor("A","FIRM",sector="X"),Actor("B","FIRM",sector="X"),Actor("C","FIRM",sector="Y"),Actor("S","FIRM",sector="Z"),
            Actor("K","BANK"),Actor("O","INVESTOR"),Actor("E","EXTERNAL"))
    pos=(Position("LOAN","K","A","80",0),Position("TRADE_PAYABLE","E","A","20",0),Position("DEPOSIT","B","K",cash_b),Position("DEPOSIT","O","K",owner))
    state=State(actors,pos,0,"quarter","synthetic","fixture")
    codes=("A","B","C","K")
    policy=BankPolicy("K","50","200","1/10","1",str(cap),loss,"fixture")
    projects=(Project("b","B","S","K","O","100","0","80","100",order,True,4,"fixture"),
              Project("c","C","S","K",None,"100","0","0","100",("DEBT",),True,4,"fixture"))
    z=((0,0,0),)*3
    struct=Structure(("X","Y","Z"),z,z,((1,0,0),(0,1,0),(0,0,1)),(.5,)*3,(0,)*3,(0,)*3,(.5,)*3,(0,0,0),"SYNTHETIC")
    assets=(Asset("bx","X","Z",.0001,.5,0,0,10,"fixture"),Asset("cy","Y","Z",.0001,.5,0,0,10,"fixture"))
    periods=(Period(struct,(None,)*3,(("X","Y","Z"),),(1,1),"fixture"),)*3
    orders=(Investment("b","bx",1,1,2,"fixture"),Investment("c","cy",1,1,2,"fixture"))
    cov=tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"fixture"} for i in range(1,28))
    return state,codes,"E",{"A":50,"B":0,"C":0,"K":0},(policy,),projects,periods,assets,(),orders,dict(noncapital_capacity=noncap,coverage=cov,evidence="fixture")

def run(*a):
    return stress_funding_capital(*a[:-1],**a[-1])

class BridgeTests(unittest.TestCase):
    def test_maturity_map_and_impairment(self):
        a=fixture("1/2");s,r=run(*a);v=r["result"]
        self.assertEqual(v["stress"]["result"]["clearing"]["result"]["unpaid_claims_by_creditor"][-1],"40")
        self.assertEqual(v["headrooms"]["K"]["result"]["capital_after"],"30")
        self.assertEqual([F(x["settled_eur"]) for x in v["projects"]],[50,50])
        self.assertEqual(s.stocks()[("LOAN","K","A",0)],80)
        self.assertFalse(v["stress"]["result"]["settlement_booked"])
    def test_no_loss_and_commission_lag(self):
        _,r=run(*fixture());v=r["result"];self.assertEqual(F(v["settled_total_eur"]),200)
        self.assertEqual([p["capacity"][0] for p in v["capital"]["result"]["periods"]],[1,1,1.5])
        self.assertEqual([p["closing_wip_value"] for p in v["capital"]["result"]["periods"]],[.0002,.0002,0])
    def test_zero_credit_substitution(self):
        _,r=run(*fixture("1",cash_b="20",owner="80",order=("CASH","EQUITY","DEBT")))
        self.assertEqual([F(x["settled_eur"]) for x in r["result"]["projects"]],[100,0])
        self.assertEqual(r["result"]["projects"][0]["sources_eur"],{"CASH":"20","EQUITY":"80","DEBT":"0"})
    def test_supply_rationing_only_delivered_financed(self):
        s,r=run(*fixture(noncap=(1,1,.0001)))
        self.assertAlmostEqual(float(F(r["result"]["settled_total_eur"])),100,places=7)
        self.assertAlmostEqual(float(s.stocks()[("DEPOSIT","S","K",None)]),100,places=7)
        self.assertAlmostEqual(float(s.stocks()[("LOAN","K","B",4)]),50,places=7)
    def test_zero_supply_no_credit(self):
        s,r=run(*fixture(noncap=(1,1,0)))
        self.assertEqual(r["result"]["settled_total_eur"],"0")
        self.assertNotIn(("LOAN","K","B",4),s.stocks())
    def test_future_loan_excluded(self):
        a=list(fixture());s=a[0];a[0]=replace(s,positions=s.positions+(Position("LOAN","K","A","200",4),))
        _,r=run(*a);self.assertEqual(r["result"]["stress"]["result"]["clearing"]["result"]["liabilities"][0][-1],"80")
    def test_unknown_maturity_blocks(self):
        a=list(fixture());s=a[0];a[0]=replace(s,positions=s.positions+(Position("LOAN","K","A","1"),))
        with self.assertRaisesRegex(ValueError,"UNKNOWN_MATURITY"):run(*a)
    def test_mapping_amount_and_supplier(self):
        a=list(fixture());a[5]=(replace(a[5][0],requested="101"),a[5][1])
        with self.assertRaisesRegex(ValueError,"EUR_REFERENCE_PRICE_MAPPING"):run(*a)
        a=list(fixture());s=a[0];a[0]=replace(s,actors=tuple(replace(x,sector="X") if x.id=="S" else x for x in s.actors))
        with self.assertRaisesRegex(ValueError,"BRANCH_PRODUCT_MAPPING"):run(*a)
    def test_replay_and_coverage(self):
        a=fixture();self.assertEqual(run(*a),run(*a))
        b=list(a);b[-1]=dict(b[-1],coverage=b[-1]["coverage"][:-1])
        with self.assertRaisesRegex(ValueError,"AC_COVERAGE"):run(*b)
    def test_debt_ceiling_by_firm_no_reallocation(self):
        _,r=run(*fixture("1/2",cash_b="100",order=("CASH","DEBT")))
        self.assertEqual([F(x["settled_eur"]) for x in r["result"]["projects"]],[100,50])
        self.assertEqual(F(r["result"]["projects"][1]["sources_eur"]["DEBT"]),50)
