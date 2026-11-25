import unittest
from dataclasses import replace
from decimal import Decimal as D
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Vintage,Investment,Period
from pipeline.economic_sector_financing import Funding,funded_path
from pipeline.economic_financial_counterparts import counterpart
class CounterpartTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(100,80),"SYNTHETIC")
        self.a=Asset("machine","A","B",2,10,0,0,10,"synthetic");self.v=Vintage("machine",10,0,20)
        self.p=Period(self.s,(None,None),(("A","B"),),(1,),"synthetic")
        self.i=Investment("order","machine",1,5,2,"synthetic")
        self.f=Funding(0,10,10,0,0,0,0,0,"synthetic")
    def case(self,pol=None,orders=None,cash=0,debt=0,owner=100,ops=100,reval=()):
        pol=pol or (self.f,)*3
        r=funded_path((self.p,)*len(pol),(self.a,),(self.v,),(self.i,) if orders is None else orders,pol,borrower="A",initial_cash=cash,initial_debt=debt,noncapital_capacity=(0,100),period_unit="YEAR",evidence="synthetic")
        return counterpart(r,{"borrower":cash,"owner":owner,"supplier":0,"operations":ops},initial_equity=20,equity_revaluations=reval,evidence="synthetic")["result"]
    def stock(self,r,t,ins,c,d):
        return D(next(x["stock"] for x in r["periods"][t-1]["positions"] if (x["instrument"],x["creditor"],x["debtor"])==(ins,c,d)))
    def test_credit_creates_deposit_and_claim(self):
        r=self.case();self.assertEqual(self.stock(r,1,"LOAN","bank","borrower"),10)
        self.assertEqual(self.stock(r,1,"DEPOSIT","supplier","bank"),10)
        self.assertEqual(self.stock(r,1,"DEPOSIT","borrower","bank"),0)
    def test_net_financial_assets_zero(self):
        for row in self.case()["periods"]:
            self.assertEqual(sum(map(D,row["net_financial_assets"].values())),0)
    def test_repayment(self):
        r=self.case((replace(self.f,principal_fraction=.2),),orders=(),cash=3,debt=10)
        self.assertEqual(self.stock(r,1,"LOAN","bank","borrower"),8);self.assertEqual(self.stock(r,1,"DEPOSIT","borrower","bank"),1)
    def test_interest_accrual_and_payment(self):
        f=replace(self.f,interest_rate=.1)
        r=self.case((f,replace(f,equity_injection=3)),orders=(),debt=10)
        self.assertEqual(self.stock(r,1,"INTEREST_PAYABLE","bank","borrower"),1)
        self.assertEqual(self.stock(r,2,"INTEREST_PAYABLE","bank","borrower"),0)
    def test_overdue_memo_no_duplicate_loan(self):
        r=self.case((replace(self.f,principal_fraction=.2),),orders=(),debt=10)
        self.assertEqual(self.stock(r,1,"LOAN","bank","borrower"),10)
        self.assertEqual(D(r["periods"][0]["borrower_principal_overdue_memo"]),2)
    def test_equity_subscription(self):
        r=self.case((replace(self.f,equity_injection=4,cash_reserve=2),))
        self.assertEqual(self.stock(r,1,"EQUITY","owner","borrower"),24)
        self.assertEqual(self.stock(r,1,"DEPOSIT","owner","bank"),96)
    def test_equity_revaluation_not_cash(self):
        r=self.case(reval=((2,5),));base=self.case()
        self.assertEqual(self.stock(r,2,"EQUITY","owner","borrower"),25)
        self.assertEqual(self.stock(r,2,"DEPOSIT","owner","bank"),self.stock(base,2,"DEPOSIT","owner","bank"))
        self.assertEqual(D(r["periods"][1]["net_revaluation"]["owner"]),5)
    def test_operating_arrears(self):
        f=replace(self.f,other_operating_cash=-4)
        r=self.case((f,replace(self.f,equity_injection=3)),orders=(),cash=1)
        self.assertEqual(self.stock(r,1,"OPERATING_PAYABLE","operations","borrower"),3)
        self.assertEqual(self.stock(r,2,"OPERATING_PAYABLE","operations","borrower"),0)
    def test_operating_receipts_transfer(self):
        r=self.case((replace(self.f,surplus_to_cash=.1),),orders=())
        self.assertEqual(self.stock(r,1,"DEPOSIT","operations","bank"),95)
        self.assertEqual(self.stock(r,1,"DEPOSIT","borrower","bank"),5)
    def test_owner_cannot_create_cash(self):
        with self.assertRaisesRegex(ValueError,"NEGATIVE_POSITION"):self.case((replace(self.f,equity_injection=4),),owner=1)
    def test_operations_cannot_create_cash(self):
        with self.assertRaisesRegex(ValueError,"NEGATIVE_POSITION"):self.case((replace(self.f,surplus_to_cash=.1),),ops=1)
    def test_reject_negative_revaluation(self):
        with self.assertRaisesRegex(ValueError,"NEGATIVE_POSITION"):self.case(reval=((1,-21),))
    def test_deterministic(self):
        self.assertEqual(self.case(),self.case());self.assertIsNone(self.case()["actual_bank_capital"])
