import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_shared_state import Actor,Position,State,Project,Event
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Period,Investment
from pipeline.economic_integrated_path import *

def fixture():
    actors=(Actor("A","FIRM",sector="X"),Actor("S","FIRM",sector="Y"),Actor("K","BANK"),Actor("H","HOUSEHOLD"),Actor("E","EXTERNAL"),Actor("O","INVESTOR"))
    st=State(actors,(Position("DEPOSIT","H","K","100"),Position("DEPOSIT","A","K","100"),Position("DEPOSIT","O","K","100")),0,"quarter","fixture","fixture")
    s=Structure(("X","Y"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(.0001,0),"SYNTHETIC")
    p=Period(s,(None,None),(("X","Y"),),(1,),"fixture")
    a=Asset("machine","X","Y",.0001,.0001,0,0,10,"fixture")
    pr=Project("p1","A","S","K",None,"100","0","0","100",("CASH",),False,3,"fixture")
    o=Investment("p1","machine",1,1,1,"fixture")
    steps=(IntegratedStep(p,(pr,),(o,),"0","0"),IntegratedStep(p,(),(),"0","0"),IntegratedStep(p,(),(),"0","0"))
    cov=tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"fixture"} for i in range(1,28))
    return st,steps,(a,),dict(noncapital_capacity=(0,.0001),capital_before="50",other_rwa="0",loan_weight="1",minimum_ratio="1/10",credit_limit="100",coverage=cov,evidence="fixture")
def run(st,steps,assets,kw):
    return integrated_path(st,"K","E","H",{"X":"A","Y":"S"},steps,assets,(),**kw)

class IntegratedTests(unittest.TestCase):
    def test_cash_investment_lag_and_income(self):
        s,a,r=run(*fixture());rows=r["result"]["periods"]
        self.assertEqual([x["household_consumption_eur"] for x in rows],["0","100","75"])
        self.assertEqual([x["household_closing_deposits_eur"] for x in rows],["150","100","125/2"])
        self.assertEqual([x["capital"]["capacity"][0] for x in rows],[0,.0001,.0001])
        self.assertEqual(rows[0]["projects"][0]["delivered_eur"],"100")
        self.assertFalse(any(p.instrument=="LOAN" for p in s.positions))
    def test_debt_interest_and_repayment(self):
        st,steps,a,kw=fixture();p=replace(steps[0].projects[0],order=("DEBT",),loan_due=1)
        steps=(replace(steps[0],projects=(p,)),replace(steps[1],interest_rate="1/10"))
        s,aa,r=run(st,steps,a,kw);rows=r["result"]["periods"]
        self.assertEqual(rows[1]["interest"]["result"]["interest_accrued"],"10")
        self.assertEqual(rows[1]["closing_capital_proxy"],"60")
        self.assertEqual(rows[1]["settlement"]["result"]["bank_receipts"],"100")
        self.assertTrue(any(p.instrument=="LOAN" for p in s.positions))
    def test_zero_supply_no_draw(self):
        st,steps,a,kw=fixture();p=replace(steps[0].projects[0],order=("DEBT",))
        kw=dict(kw,noncapital_capacity=(0,0));s,_,r=run(st,(replace(steps[0],projects=(p,)),),a,kw)
        self.assertEqual(r["result"]["periods"][0]["projects"][0]["delivered_eur"],"0")
        self.assertFalse(any(p.instrument=="LOAN" for p in s.positions))
    def test_reinvest_from_sales(self):
        st,steps,a,kw=fixture();p=replace(steps[0].projects[0],id="p2",requested="50")
        o=replace(steps[0].orders[0],id="p2",period=3,units=.5)
        end=replace(steps[2],projects=(p,),orders=(o,))
        s,_,r=run(st,steps[:2]+(end,),a,kw)
        self.assertEqual(r["result"]["periods"][2]["projects"][0]["delivered_eur"],"50")
    def test_budget_and_replay(self):
        st,steps,a,kw=fixture();x=run(st,steps,a,kw);self.assertEqual(x,run(st,steps,a,kw))
        for row in x[2]["result"]["periods"]:self.assertLessEqual(F(row["household_consumption_eur"]),F(row["household_budget_eur"]))
    def test_reject_intermediate(self):
        st,steps,a,kw=fixture();p=steps[0].production
        bad=replace(p,structure=replace(p.structure,domestic=((.1,0),(0,0))))
        with self.assertRaisesRegex(ValueError,"REAL_CASH_CLOSURE"):run(st,(replace(steps[0],production=bad),),a,kw)
    def test_loan_overdue_veto(self):
        st,steps,a,kw=fixture();st=replace(st,positions=st.positions+(Position("LOAN","K","A","200",0),))
        p=replace(steps[0].projects[0],order=("DEBT",))
        s,_,r=run(st,(replace(steps[0],projects=(p,),recognition="1/2"),),a,kw)
        self.assertEqual(r["result"]["periods"][0]["projects"][0]["delivered_eur"],"0")
        self.assertIn("A",r["result"]["periods"][0]["overdue_credit_veto"])
    def test_interest_no_compounding_and_duplicate(self):
        st,steps,a,kw=fixture();st=replace(st,positions=st.positions+(Position("LOAN","K","A","100",2),Position("INTEREST_PAYABLE","K","A","5",0)))
        x,r=accrue(st,"K","1/10",evidence="fixture")
        self.assertEqual(r["result"]["interest_accrued"],"10")
        self.assertEqual(x.stocks()[("INTEREST_PAYABLE","K","A",0)],15)
        with self.assertRaisesRegex(ValueError,"REPLAYED_EVENT"):accrue(x,"K","1/10",evidence="fixture")
    def test_no_coverage_no_run(self):
        st,steps,a,kw=fixture()
        with self.assertRaisesRegex(ValueError,"AC_COVERAGE"):run(st,steps,a,dict(kw,coverage=kw["coverage"][:-1]))
