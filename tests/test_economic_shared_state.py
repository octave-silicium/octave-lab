import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_shared_state import *

def fixture():
    actors=tuple(Actor(a,k) for a,k in (("A","FIRM"),("B","FIRM"),("S","FIRM"),("O","INVESTOR"),("K","BANK")))
    pos=tuple(Position("DEPOSIT",a,"K",v) for a,v in (("A","100"),("B","20"),("O","80")))
    return State(actors,pos,0,"quarter","fixture","synthetic")

def project(id="p",firm="A",order=("CASH",),want="100",reserve="0",equity="0",debt="0",partial=False):
    return Project(id,firm,"S","K","O",want,reserve,equity,debt,order,partial,4,"fixture")

class SharedStateTests(unittest.TestCase):
    def test_cash_only_no_debt(self):
        s,r=fund_projects(fixture(),(project(),),{})
        self.assertEqual(r["result"]["projects"][0]["sources"],{"CASH":"100","EQUITY":"0","DEBT":"0"})
        self.assertFalse(any(p.instrument=="LOAN" for p in s.positions))
        self.assertEqual(s.stocks()[("DEPOSIT","S","K",None)],100)
    def test_equity_only(self):
        s,r=fund_projects(fixture(),(project(firm="B",order=("EQUITY",),want="80",equity="80"),),{})
        self.assertEqual(s.stocks()[("EQUITY","O","B",None)],80)
        self.assertEqual(s.stocks()[("DEPOSIT","B","K",None)],20)
        self.assertFalse(any(p.instrument=="LOAN" for p in s.positions))
    def test_mixed_and_reserve(self):
        s,r=fund_projects(fixture(),(project(firm="B",order=("CASH","EQUITY","DEBT"),reserve="10",equity="40",debt="60"),),{"K":"60"})
        self.assertEqual(r["result"]["projects"][0]["sources"],{"CASH":"10","EQUITY":"40","DEBT":"50"})
        self.assertEqual(s.stocks()[("DEPOSIT","B","K",None)],10)
        self.assertEqual(s.stocks()[("LOAN","K","B",4)],50)
        self.assertEqual(sum(s.net_financial_positions().values()),0)
    def test_credit_competition_order(self):
        p=project("a","A",("DEBT",),want="60",debt="60",partial=True)
        q=project("b","B",("DEBT",),want="60",debt="60",partial=True)
        _,r=fund_projects(fixture(),(p,q),{"K":80})
        _,t=fund_projects(fixture(),(q,p),{"K":80})
        self.assertEqual([x["paid_acquisition"] for x in r["result"]["projects"]],["60","20"])
        self.assertEqual(t["result"]["projects"][0]["firm"],"B")
        self.assertEqual(r["result"]["bank_caps_remaining"]["K"],"0")
    def test_owner_finite_and_refusal_atomic(self):
        p=project("a","A",("EQUITY",),want="60",equity="80")
        q=project("b","B",("EQUITY",),want="60",equity="80")
        s,r=fund_projects(fixture(),(p,q),{})
        self.assertEqual([x["paid_acquisition"] for x in r["result"]["projects"]],["60","0"])
        self.assertEqual(s.stocks()[("DEPOSIT","O","K",None)],20)
    def test_zero_credit_substitute(self):
        _,r=fund_projects(fixture(),(project(firm="B",order=("DEBT","CASH","EQUITY"),equity="80",debt="100"),),{"K":0})
        self.assertEqual(r["result"]["projects"][0]["sources"],{"CASH":"20","EQUITY":"80","DEBT":"0"})
    def test_no_funding_no_mutation(self):
        s=fixture();t,r=fund_projects(s,(project(firm="B",order=(),want="100"),),{})
        self.assertEqual(s.fingerprint,t.fingerprint)
        self.assertEqual(r["result"]["projects"][0]["unfunded"],"100")
    def test_debt_and_time(self):
        s=fixture();t,_=apply(s,(Event("l",0,"LOAN_ORIGINATION","B","K","K","30","fixture",2),))
        self.assertEqual(t.stocks()[("DEPOSIT","B","K",None)],50)
        u,_=apply(t,(Event("r",0,"LOAN_REPAYMENT","B","K","K","10","fixture",2),))
        self.assertEqual(u.stocks()[("LOAN","K","B",2)],20)
        self.assertEqual(advance(u).due_stock()["matured"],[])
        self.assertEqual(advance(advance(u)).due_stock()["matured"][0]["stock"],"20")
    def test_unknown_maturity_and_immutable(self):
        s=fixture();t=replace(s,positions=s.positions+(Position("LOAN","K","B","10"),))
        self.assertEqual(len(t.due_stock()["unknown_maturity"]),1)
        self.assertEqual(t.due_stock()["matured"],[])
        with self.assertRaisesRegex(ValueError,"INSUFFICIENT_POSITION"):
            apply(s,(Event("x",0,"DEPOSIT_TRANSFER","B","A","K","21","fixture"),))
        self.assertEqual(s.stocks()[("DEPOSIT","B","K",None)],20)
    def test_reject_wrong_axis_time_float_and_duplicates(self):
        s=fixture();e=Event("x",0,"DEPOSIT_TRANSFER","B","A","K","1","fixture")
        with self.assertRaisesRegex(ValueError,"DUPLICATE_EVENT"):apply(s,(e,e))
        with self.assertRaisesRegex(ValueError,"EVENT_PERIOD"):apply(advance(s),(e,))
        with self.assertRaisesRegex(ValueError,"EXACT_AMOUNT"):amount(0.1)
        with self.assertRaisesRegex(ValueError,"UNKNOWN_COUNTERPARTY"):replace(s,positions=s.positions+(Position("LOAN","K","Z","1",1),))
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_EUR_ONLY"):replace(s,basis="OBSERVED")
    def test_permutation_and_exact_replay(self):
        s=fixture();t=replace(s,actors=s.actors[::-1],positions=s.positions[::-1])
        self.assertEqual(s.fingerprint,t.fingerprint)
        e=Event("x",0,"DEPOSIT_TRANSFER","B","A","K","1/3","fixture")
        a,r=apply(s,(e,));b,z=apply(t,(e,))
        self.assertEqual(r,z);self.assertEqual(a.stocks()[("DEPOSIT","B","K",None)],F(59,3))
    def test_ac_coverage_fail_closed(self):
        rows=tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"not qualified in fixture"} for i in range(1,28))
        self.assertEqual(validate_transversal_coverage(rows)["entries"],27)
        with self.assertRaisesRegex(ValueError,"AC_COVERAGE"):validate_transversal_coverage(rows[:-1])
        with self.assertRaisesRegex(ValueError,"AC_DISPOSITION"):validate_transversal_coverage((dict(rows[0],disposition="APPLIED_QUALIFIED"),)+rows[1:])
        with self.assertRaisesRegex(ValueError,"AC_EVIDENCE"):validate_transversal_coverage((dict(rows[0],disposition="HYPOTHESIS_ONLY"),)+rows[1:])

    def test_duplicate_across_batches_and_governed_entrypoint(self):
        s=fixture();e=Event("x",0,"DEPOSIT_TRANSFER","B","A","K","1","fixture")
        u,_=apply(s,(e,))
        with self.assertRaisesRegex(ValueError,"REPLAYED_EVENT"):apply(u,(e,))
        with self.assertRaisesRegex(ValueError,"REPLAYED_EVENT"):apply(advance(u),(replace(e,period=1),))
        rows=tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"fixture"} for i in range(1,28))
        _,r=run_funding(s,(project(),),{},rows)
        self.assertEqual(r["result"]["coverage"]["entries"],27)
        with self.assertRaisesRegex(ValueError,"AC_COVERAGE"):run_funding(s,(project(),),{},rows[:-1])
