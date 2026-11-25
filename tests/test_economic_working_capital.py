import unittest
from dataclasses import replace
from fractions import Fraction as F
from test_economic_operating_path import fixture,run
from pipeline.economic_working_capital import *
from pipeline.economic_shared_state import Position,Event
from pipeline.economic_operating_path import OperatingStep

class WorkingTests(unittest.TestCase):
    def test_local_not_uniform(self):
        st,steps,a,kw=fixture("0");p=steps[0].production
        p=replace(p,structure=replace(p.structure,final=(.00005,.00005)))
        common=replace(steps[0],production=p)
        _,_,old=run(st,(common,),a,kw)
        _,_,new=run(st,(replace(common,working=WorkingPolicy()),),a,kw)
        self.assertEqual(old["result"]["periods"][0]["household_consumption_eur"],"0")
        self.assertEqual(new["result"]["periods"][0]["household_consumption_eur"],"50")
    def test_working_credit_only_drawn_need(self):
        st,steps,a,kw=fixture("15");policy=WorkingPolicy((Facility("A","40",1,"fixture"),))
        s,_,r=run(st,(replace(steps[0],working=policy),),a,kw);row=r["result"]["periods"][0]
        self.assertAlmostEqual(float(F(row["working_credit_drawn"])),15,places=6)
        self.assertEqual(row["household_consumption_eur"],"100")
        self.assertEqual(s.stocks()[("LOAN","K","A",1)],15)
    def test_supplier_credit_and_payment(self):
        st,steps,a,kw=fixture("10");st=replace(st,positions=st.positions+(Position("DEPOSIT","S","K","20"),))
        policy=WorkingPolicy((),(TradeTerm("A","S","1","30",1,"fixture"),))
        first=replace(steps[0],working=policy)
        s,_,r=run(st,(first,),a,kw);row=r["result"]["periods"][0]
        self.assertAlmostEqual(float(F(row["household_consumption_eur"])),100,places=4)
        d=s.stocks()[("TRADE_PAYABLE","S","A",1)]
        self.assertAlmostEqual(float(d),20,places=4)
        self.assertEqual(row["working_credit_drawn"],"0")
        self.assertEqual(row["trade_bfr"]["S"]["trade_receivables"],str(d))
        self.assertEqual(row["trade_invoice_receipt"]["result"]["cash_created"],"0")
        p=replace(first.production,structure=replace(first.production.structure,final=(0,0)))
        _,_,rr=run(st,(first,OperatingStep(p,(),(),"0","0",working=policy)),a,kw)
        claim=next(x for x in rr["result"]["periods"][1]["settlement"]["result"]["claims"] if x["key"][0]=="TRADE_PAYABLE")
        self.assertEqual(F(claim["paid"]),d)
        self.assertEqual(claim["closing_gross"],"0")
    def test_cap_and_existing_outstanding(self):
        st,steps,a,kw=fixture("10");st=replace(st,positions=st.positions+(Position("DEPOSIT","S","K","20"),Position("TRADE_PAYABLE","S","A","15",3)))
        p=WorkingPolicy((),(TradeTerm("A","S","1","20",1,"fixture"),))
        s,_,r=run(st,(replace(steps[0],working=p),),a,kw)
        self.assertLessEqual(sum(amount(x.stock) for x in s.positions if x.instrument=="TRADE_PAYABLE"),20)
        self.assertLess(float(F(r["result"]["periods"][0]["household_consumption_eur"])),100)
    def test_no_supply_no_working_draw(self):
        st,steps,a,kw=fixture("0");p=WorkingPolicy((Facility("A","40",1,"fixture"),))
        _,_,r=run(st,(replace(steps[0],working=p),),a,dict(kw,noncapital_capacity=(0,0)))
        self.assertEqual(r["result"]["periods"][0]["working_credit_drawn"],"0")
    def test_overdue_veto(self):
        st,steps,a,kw=fixture("0");st=replace(st,positions=st.positions+(Position("LOAN","K","A","10",0),))
        p=WorkingPolicy((Facility("A","40",1,"fixture"),))
        _,_,r=run(st,(replace(steps[0],working=p),),a,kw)
        row=r["result"]["periods"][0];self.assertEqual(row["working_credit_envelope"],"0");self.assertEqual(row["household_consumption_eur"],"0")
    def test_invoice_replay(self):
        st,_,_,_=fixture();x,rr=invoice(st,(("x","A","S","10",1),),evidence="fixture")
        self.assertEqual(x.stocks()[("TRADE_PAYABLE","S","A",1)],10)
        with self.assertRaisesRegex(ValueError,"REPLAYED_EVENT"):invoice(x,(("x","A","S","10",1),),evidence="fixture")
    def test_invalid_terms(self):
        st,steps,a,kw=fixture();p=WorkingPolicy((),(TradeTerm("A","S","2","20",1,"fixture"),))
        with self.assertRaisesRegex(ValueError,"TRADE_SHARE"):run(st,(replace(steps[0],working=p),),a,kw)
