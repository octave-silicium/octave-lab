import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_shared_state import Actor,Position,State,Event,Project,advance
from pipeline.economic_shared_settlement import *

def fixture(cash="50"):
    return State(tuple(Actor(a,k) for a,k in (("A","FIRM"),("B","FIRM"),("S","FIRM"),("K","BANK"),("E","EXTERNAL"))),
        (Position("DEPOSIT","A","K",cash),Position("DEPOSIT","S","K","100"),Position("LOAN","K","A","80",0),
         Position("TRADE_PAYABLE","E","A","20",0)),0,"quarter","synthetic","fixture")

def coverage():
    return tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"fixture"} for i in range(1,28))

class SettlementTests(unittest.TestCase):
    def test_partial_and_deposits(self):
        s,a,r=settle(fixture(),"K","E",recognition="1/2",evidence="fixture")
        self.assertEqual(s.stocks()[("LOAN","K","A",0)],40)
        self.assertEqual(s.stocks()[("DEPOSIT","E","K",None)],10)
        self.assertEqual(r["result"]["deposits_extinguished"],"40")
        self.assertEqual(a[0].value,"20")
        self.assertEqual(r["result"]["net_impairment_expense_proxy"],"20")
    def test_no_double_impairment_and_recovery(self):
        s,a,_=settle(fixture(),"K","E",recognition="1/2",evidence="fixture")
        s,a,r=settle(advance(s),"K","E",a,recognition="1/2",evidence="fixture")
        self.assertEqual(r["result"]["net_impairment_expense_proxy"],"0")
        s=advance(s);s,_=apply(s,(Event("pay",2,"DEPOSIT_TRANSFER","S","A","K","50","fixture"),))
        s,a,r=settle(s,"K","E",a,recognition="1/2",evidence="fixture")
        self.assertEqual(r["result"]["net_impairment_expense_proxy"],"-20")
        self.assertEqual(a,());self.assertNotIn(("LOAN","K","A",0),s.stocks())
    def test_discharge_not_double_loss(self):
        s,a,_=settle(fixture(),"K","E",recognition="1",evidence="fixture")
        d=Discharge(("LOAN","K","A",0),"40","assumed legal discharge")
        s,a,r=settle(advance(s),"K","E",a,(d,),recognition="1",evidence="fixture")
        self.assertEqual(r["result"]["net_impairment_expense_proxy"],"0")
        self.assertEqual(r["result"]["explicit_discharge"],"40");self.assertEqual(a,())
        self.assertNotIn(d.key,s.stocks())
    def test_discharge_uncovered_loss(self):
        d=Discharge(("LOAN","K","A",0),"40","fixture")
        s,a,r=settle(fixture(),"K","E",(),(d,),recognition="0",evidence="fixture")
        self.assertEqual(r["result"]["net_impairment_expense_proxy"],"40")
    def test_pure_loan_no_external_leak(self):
        s=fixture("80");s=replace(s,positions=tuple(p for p in s.positions if p.instrument!="TRADE_PAYABLE"))
        close,_,r=settle(s,"K","E",recognition="0",evidence="fixture")
        self.assertEqual(r["result"]["method"],"ACYCLIC_TOPOLOGICAL")
        self.assertEqual(r["result"]["bank_receipts"],"80")
    def test_chain(self):
        s=fixture("50");s=replace(s,positions=s.positions+(Position("TRADE_PAYABLE","B","A","100",0),Position("LOAN","K","B","25",0)))
        close,_,r=settle(s,"K","E",recognition="0",evidence="fixture")
        self.assertEqual(r["result"]["bank_receipts"],"45")
        self.assertEqual(close.stocks()[("DEPOSIT","E","K",None)],5)
    def test_regular_cycle(self):
        s=fixture();s=replace(s,positions=s.positions+(Position("TRADE_PAYABLE","B","A","100",0),Position("TRADE_PAYABLE","A","B","60",0),Position("TRADE_PAYABLE","E","B","10",0)))
        close,_,r=settle(s,"K","E",recognition="0",evidence="fixture")
        self.assertEqual(r["result"]["method"],"REGULAR_SIMULTANEOUS")
        self.assertEqual(sum(close.net_financial_positions().values()),0)
    def test_cycle_outside_leak_required(self):
        s=fixture();s=replace(s,positions=s.positions+(Position("TRADE_PAYABLE","B","A","100",0),Position("TRADE_PAYABLE","A","B","60",0)))
        with self.assertRaisesRegex(ValueError,"EXTERNAL_LEAK_REQUIRED"):settle(s,"K","E",recognition="0",evidence="fixture")
    def test_future_unknown_and_repeat(self):
        s=fixture();s=replace(s,positions=s.positions+(Position("LOAN","K","A","1",3),))
        t,_,_=settle(s,"K","E",recognition="0",evidence="fixture")
        self.assertEqual(t.stocks()[("LOAN","K","A",3)],1)
        with self.assertRaisesRegex(ValueError,"REPLAYED_EVENT"):settle(t,"K","E",recognition="0",evidence="fixture")
        s=replace(s,positions=s.positions+(Position("LOAN","K","B","1"),))
        with self.assertRaisesRegex(ValueError,"UNKNOWN_MATURITY"):settle(s,"K","E",recognition="0",evidence="fixture")
    def test_discharge_overpayment_refused(self):
        with self.assertRaisesRegex(ValueError,"DISCHARGE_EXCEEDS_UNPAID"):
            settle(fixture(),"K","E",(),(Discharge(("LOAN","K","A",0),"41","fixture"),),recognition="1",evidence="fixture")
    def test_path_capital_and_rwa(self):
        p=Project("b","B","S","K",None,"100","0","0","100",("DEBT",),True,3,"fixture")
        steps=(Step((),(p,),"1/2"),Step((Event("cash",1,"DEPOSIT_TRANSFER","S","A","K","50","fixture"),),(),"1/2"))
        s,a,r=finance_path(fixture(),"K","E",steps,capital_before="50",other_rwa="120",loan_weight="1",minimum_ratio="1/10",credit_limit="100",coverage=coverage())
        rows=r["result"]["periods"]
        self.assertEqual([x["closing_capital_proxy"] for x in rows],["30","50"])
        self.assertEqual([x["rwa_after_funding_proxy"] for x in rows],["260","220"])
        self.assertEqual(s.period,2);self.assertEqual(a,())
    def test_negative_capital_blocks_credit(self):
        p=Project("b","B","S","K",None,"100","0","0","100",("DEBT",),True,3,"fixture")
        _,_,r=finance_path(fixture(),"K","E",(Step((),(p,),"1"),),capital_before="10",other_rwa="0",loan_weight="1",minimum_ratio="1/10",credit_limit="100",coverage=coverage())
        row=r["result"]["periods"][0]
        self.assertEqual(row["closing_capital_proxy"],"-30");self.assertEqual(row["credit_ceiling"],"0")
