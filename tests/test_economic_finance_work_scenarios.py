import unittest
from fractions import Fraction as F
from dataclasses import replace
from pipeline.economic_finance_work_scenarios import *
from pipeline.economic_shared_state import Actor,Position,State,Project
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Period,Investment
from pipeline.economic_operating_path import OperatingStep

def fixture():
    actors=(Actor("A","FIRM",sector="X"),Actor("S","FIRM",sector="Y"),Actor("K","BANK"),Actor("H","HOUSEHOLD"),Actor("E","EXTERNAL"),Actor("G","GOVERNMENT"))
    st=State(actors,(Position("DEPOSIT","H","K","200"),),0,"quarter","fixture","fixture")
    structure=Structure(("X","Y"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(.0001,0),"SYNTHETIC")
    p=Period(structure,(None,None),(("Y",),("X",)),(1,),"fixture")
    a=Asset("machine","X","Y",.0001,.0001,0,0,10,"fixture")
    pr=Project("p","A","S","K",None,"100","0","0","100",("DEBT",),True,5,"fixture")
    o=Investment("p","machine",1,1,1,"fixture")
    steps=(OperatingStep(p,(pr,),(o,),"0","0"),OperatingStep(p,(),(),"0","0"))
    scenarios=(BankScenario("ref","50","100","fixture"),BankScenario("cut","50","50","fixture"),BankScenario("freeze","50","0","fixture"))
    cov=tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"fixture"} for i in range(1,28))
    kw=dict(hourly_compensation={"X":"10","Y":"10"},reference_hours={"X":"5","Y":"5"},noncapital_capacity=(0,.0001),other_rwa="0",loan_weight="1",minimum_ratio="1/10",coverage=cov,evidence="fixture")
    return st,steps,(a,),scenarios,kw

def run(st,steps,a,scenarios,kw):
    return compare(st,"K","E","H","G",{"X":"A","Y":"S"},steps,a,(),scenarios,**kw)

class FinanceWorkTests(unittest.TestCase):
    def test_credit_capital_hours(self):
        r=run(*fixture())["result"]["scenarios"]
        self.assertEqual([r[k][0]["investment_settled_eur"] for k in ("ref","cut","freeze")],["100","50","0"])
        self.assertEqual([r[k][1]["conditional_work"]["X"]["conditional_paid_hours"] for k in ("ref","cut","freeze")],["5","5/2","0"])
        self.assertEqual([r[k][0]["conditional_work"]["X"]["conditional_paid_hours"] for k in ("ref","cut","freeze")],["0","0","0"])
        self.assertEqual(r["ref"][1]["conditional_work"]["X"]["conditional_fte_equivalent"],"1")
    def test_balance_and_maturity(self):
        r=run(*fixture())["result"]["scenarios"]["ref"][0]["balance"]
        self.assertEqual(r["A"]["productive_capital_proxy"],"100")
        self.assertEqual(r["A"]["future_debt_gross"],"100")
        self.assertEqual(r["A"]["due_debt_gross"],"0")
        self.assertEqual(r["A"]["modeled_assets_less_non_equity_liabilities_net_of_allowance"],"0")
        self.assertIsNone(r["K"]["full_balance_sheet"])
        self.assertEqual(sum(F(x["financial_net_position_gross"]) for x in r.values()),0)
    def test_no_fabricated_jobs_and_replay(self):
        x=run(*fixture());self.assertEqual(x,run(*fixture()))
        self.assertIsNone(x["result"]["actual_jobs"])
        self.assertEqual(x["result"]["differences"]["freeze"][1]["conditional_hours_delta"]["X"],"-5")
    def test_rate_required(self):
        st,s,a,c,kw=fixture()
        with self.assertRaisesRegex(ValueError,"WORK_PARAMETERS"):run(st,s,a,c,dict(kw,hourly_compensation={"X":"0","Y":"10"}))
    def test_bank_capital_scenario(self):
        st,s,a,c,kw=fixture();c=(c[0],BankScenario("capital_stress","5","100","fixture"))
        r=run(st,s,a,c,kw)["result"]["scenarios"]
        self.assertEqual(r["capital_stress"][0]["investment_settled_eur"],"50")
    def test_actual_settlement_stress(self):
        st,s,a,c,kw=fixture();st=replace(st,positions=st.positions+(Position("LOAN","K","A","60",0),))
        s=(replace(s[0],recognition="1"),s[1])
        r=run(st,s,a,c,kw)["result"]["scenarios"]["ref"][0]
        self.assertEqual(r["bank_capital_proxy"],"-10")
        self.assertEqual(r["investment_settled_eur"],"0")
        self.assertEqual(r["balance"]["A"]["due_debt_gross"],"60")
        self.assertEqual(r["balance"]["K"]["bank_allowance_memo"],"60")
