import unittest
from fractions import Fraction as F
from pipeline.economic_financial_network import clear,credit_headroom
class NetworkTests(unittest.TestCase):
    def chain(self,e=(50,0,0)):
        return clear(("A","B","C"),((0,80,0),(0,0,60),(0,0,0)),(20,20,50),e,evidence="synthetic")
    def credit(self,r=None,loss=1,**kw):
        p=dict(capital=50,existing_rwa=200,minimum_ratio=".1",new_risk_weight=1,credit_limit=300,loss_recognition=loss,requests={"A":100,"C":200},evidence="synthetic")
        p.update(kw);return credit_headroom(r or self.chain(),"B",**p)["result"]
    def test_cascade(self):
        r=self.chain()["result"]
        self.assertEqual(r["payments"],["50","40","30"])
        self.assertEqual(r["default_rounds"],[["A"],["B"],["C"]])
        self.assertEqual(r["unpaid_claims_by_creditor"],["0","40","30"])
    def test_full_payment(self):
        r=self.chain((100,0,0))["result"];self.assertEqual(r["payments"],["100","80","50"]);self.assertEqual(r["default_rounds"],[])
    def test_external_conservation(self):
        r=self.chain()["result"];self.assertEqual(sum(map(F,r["external_paid"]))+sum(map(F,r["remaining_liquidity"])),50)
    def test_unpaid_conservation(self):
        r=self.chain()["result"];self.assertEqual(sum(map(F,r["unpaid_total_by_debtor"])),110)
    def test_cycle(self):
        r=clear(("A","B"),((0,80),(80,0)),(20,20),(0,20),evidence="synthetic")["result"]
        self.assertEqual(list(map(F,r["payments"])),[F(400,9),F(500,9)])
    def test_no_external_rejected(self):
        with self.assertRaisesRegex(ValueError,"EXTERNAL_LEAK"):clear(("A","B"),((0,1),(1,0)),(0,0),(0,0),evidence="synthetic")
    def test_self_rejected(self):
        with self.assertRaisesRegex(ValueError,"SELF_CLAIM"):clear(("A",),((1,),),(1,),(0,),evidence="synthetic")
    def test_negative_rejected(self):
        with self.assertRaisesRegex(ValueError,"NONNEGATIVE"):self.chain((-1,0,0))
    def test_no_loss_assumption(self):
        r=self.credit(loss=0);self.assertEqual(r["approved_total"],"300");self.assertEqual(r["assumed_impairment"],"0")
    def test_partial_loss(self):
        r=self.credit(loss=".5");self.assertEqual(r["approved_total"],"100");self.assertEqual(r["approved"],{"A":"100/3","C":"200/3"})
    def test_full_loss(self):
        r=self.credit();self.assertEqual(r["capital_shortfall"],"10");self.assertEqual(r["approved_total"],"0")
    def test_credit_limit(self):
        r=self.credit(loss=0,credit_limit=60);self.assertEqual(r["approved"],{"A":"20","C":"40"})
    def test_risk_weight(self):
        r=self.credit(loss=".5",new_risk_weight=2);self.assertEqual(r["approved_total"],"50")
    def test_tamper(self):
        r=self.chain();r["result"]["payments"][0]="100"
        with self.assertRaisesRegex(ValueError,"RECEIPT"):self.credit(r)
    def test_same_margins_different_topology(self):
        a=clear(("A","B","C","D"),((0,80,0,0),(80,0,0,0),(0,0,0,80),(0,0,80,0)),(20,)*4,(0,20,20,20),evidence="synthetic")["result"]
        b=clear(("A","B","C","D"),((0,80,0,0),(0,0,80,0),(0,0,0,80),(80,0,0,0)),(20,)*4,(0,20,20,20),evidence="synthetic")["result"]
        self.assertEqual(a["payments"][2:],["100","100"])
        self.assertTrue(all(F(x)<100 for x in b["payments"]))
    def test_zero_obligation(self):
        r=clear(("A",),((0,),),(0,),(3,),evidence="synthetic")["result"];self.assertEqual(r["remaining_liquidity"],["3"])
    def test_deterministic(self):self.assertEqual(self.chain(),self.chain())
