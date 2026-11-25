import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_shared_state import Actor,Position,State,Project,Event
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Period,Investment
from pipeline.economic_operating_path import OperatingStep,operating_path

def fixture(cash="100"):
    actors=(Actor("A","FIRM",sector="X"),Actor("S","FIRM",sector="Y"),Actor("K","BANK"),Actor("H","HOUSEHOLD"),Actor("E","EXTERNAL"),Actor("G","GOVERNMENT"))
    st=State(actors,(Position("DEPOSIT","H","K","100"),Position("DEPOSIT","A","K",cash)),0,"quarter","fixture","fixture")
    s=Structure(("X","Y"),((0,0),(.2,0)),((.1,0),(0,0)),((1,0),(0,1)),(.4,.5),(.1,0),(0,0),(.2,.5),(.0001,0),"SYNTHETIC")
    p=Period(s,(None,None),(("Y",),("X",)),(1,),"fixture")
    a=Asset("machine","X","Y",.0001,.0001,0,0,10,"fixture")
    steps=(OperatingStep(p,(),(),"0","0"),)
    cov=tuple({"id":f"AC{i:02}","disposition":"PENDING_QUALIFICATION","reason":"fixture"} for i in range(1,28))
    return st,steps,(a,),dict(noncapital_capacity=(.001,.001),capital_before="50",other_rwa="0",loan_weight="1",minimum_ratio="1/10",credit_limit="100",coverage=cov,evidence="fixture")
def run(st,steps,assets,kw):
    return operating_path(st,"K","E","H","G",{"X":"A","Y":"S"},steps,assets,(),**kw)

class OperatingTests(unittest.TestCase):
    def test_inputs_import_tax_surplus(self):
        st,steps,a,kw=fixture();s,aa,r=run(st,steps,a,kw);row=r["result"]["periods"][0]
        f={x["firm"]:x for x in row["firms"]}
        self.assertAlmostEqual(float(F(f["A"]["sales_eur"])),100)
        self.assertAlmostEqual(float(F(f["A"]["intermediate_cash_cost_eur"])),30)
        self.assertAlmostEqual(float(F(f["A"]["wages_eur"])),40)
        self.assertAlmostEqual(float(F(f["A"]["production_tax_eur"])),10)
        self.assertAlmostEqual(float(F(f["A"]["gross_operating_cash_proxy_eur"])),20)
        self.assertAlmostEqual(float(F(f["S"]["sales_eur"])),20)
        self.assertAlmostEqual(float(s.stocks()[("DEPOSIT","E","K",None)]),10)
        self.assertAlmostEqual(float(s.stocks()[("DEPOSIT","G","K",None)]),10)
        self.assertAlmostEqual(float(s.stocks()[("DEPOSIT","H","K",None)]),50)
    def test_liquidity_constrains_output(self):
        _,_,r=run(*fixture("15"));row=r["result"]["periods"][0]
        self.assertAlmostEqual(float(F(row["input_prefunding_scale"])),.5,places=6)
        self.assertAlmostEqual(float(F(row["household_consumption_eur"])),50,places=4)
    def test_no_cash_no_production(self):
        _,_,r=run(*fixture("0"))
        self.assertEqual(r["result"]["periods"][0]["household_consumption_eur"],"0")
    def test_self_use_not_cash(self):
        st,steps,a,kw=fixture();p=steps[0].production;s=replace(p.structure,domestic=((.2,0),(0,0)))
        _,_,r=run(st,(replace(steps[0],production=replace(p,structure=s)),),a,kw)
        row=r["result"]["periods"][0];f=next(x for x in row["firms"] if x["firm"]=="A")
        self.assertAlmostEqual(float(F(f["self_use_eur"])),25,places=6)
        self.assertAlmostEqual(float(F(f["sales_eur"])),100,places=6)
        self.assertAlmostEqual(float(F(f["intermediate_cash_cost_eur"])),12.5,places=6)
    def test_import_limit(self):
        st,steps,a,kw=fixture();p=replace(steps[0].production,imported_limits=(0,None))
        _,_,r=run(st,(replace(steps[0],production=p),),a,kw)
        self.assertEqual(r["result"]["periods"][0]["household_consumption_eur"],"0")
    def test_amortization_and_interest(self):
        st,steps,a,kw=fixture();p=steps[0].production
        p=replace(p,structure=replace(p.structure,final=(0,0)))
        project=Project("p","A","S","K",None,"100","0","0","100",("DEBT",),True,2,"fixture")
        o=Investment("p","machine",1,1,1,"fixture")
        first=OperatingStep(p,(project,),(o,),"0","0",amortization=(("p",((1,"1/2"),(2,"1/2"))),))
        s,_,r=run(st,(first,),a,kw)
        self.assertEqual(s.stocks()[("LOAN","K","A",1)],50)
        self.assertEqual(s.stocks()[("LOAN","K","A",2)],50)
        _,_,r=run(st,(first,OperatingStep(p,(),(),"1/10","0"),OperatingStep(p,(),(),"1/10","0")),a,kw)
        rows=r["result"]["periods"]
        self.assertEqual(rows[1]["interest"]["result"]["interest_accrued"],"10")
        self.assertEqual(rows[2]["interest"]["result"]["interest_accrued"],"5")
    def test_invalid_schedule(self):
        st,steps,a,kw=fixture();p=Project("p","A","S","K",None,"100","0","0","100",("DEBT",),True,2,"fixture");o=Investment("p","machine",1,1,1,"fixture")
        first=replace(steps[0],projects=(p,),orders=(o,),amortization=(("p",((1,"1/2"),(2,"1/4"))),))
        with self.assertRaisesRegex(ValueError,"AMORTIZATION_SHARES"):run(st,(first,),a,kw)
    def test_replay_and_coverage(self):
        st,steps,a,kw=fixture();self.assertEqual(run(st,steps,a,kw),run(st,steps,a,kw))
        with self.assertRaisesRegex(ValueError,"AC_COVERAGE"):run(st,steps,a,dict(kw,coverage=kw["coverage"][:-1]))

    def test_partial_delivery_splits_only_drawn_principal(self):
        st,steps,a,kw=fixture();p=steps[0].production
        p=replace(p,structure=replace(p.structure,final=(0,0)))
        project=Project("p","A","S","K",None,"100","0","0","100",("DEBT",),True,2,"fixture")
        o=Investment("p","machine",1,1,1,"fixture")
        first=OperatingStep(p,(project,),(o,),"0","0",amortization=(("p",((1,"1/4"),(2,"3/4"))),))
        close,_,r=run(st,(first,),a,dict(kw,noncapital_capacity=(.001,.00005)))
        self.assertEqual(close.stocks()[("LOAN","K","A",1)],F(25,2))
        self.assertEqual(close.stocks()[("LOAN","K","A",2)],F(75,2))
        self.assertEqual(r["result"]["periods"][0]["projects"][0]["delivered_eur"],"50")
    def test_public_recycling_is_explicit(self):
        st,steps,a,kw=fixture();p=steps[0].production
        next_step=OperatingStep(p,(),(),"0","0",transfers=(Event("public-recycle",1,"DEPOSIT_TRANSFER","G","H","K","10","assumed transfer"),))
        _,_,r=run(st,steps+(next_step,),a,kw)
        self.assertEqual(r["result"]["periods"][1]["household_budget_eur"],"60")
