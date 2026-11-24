import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_physical_pilot import make,TASK_PREFIX,variants
from pipeline.economic_firm import *
from pipeline.economic_firm_pilot import fixture,audit
class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}
class FirmTests(unittest.TestCase):
    def setUp(self):
        self.p,_=make(Fake());self.b,self.bc,self.alts,self.cfg=fixture(self.p)
    def calc(self,i,bc=None,ac=None):
        s,c=self.alts[i]
        return assess(self.p,self.b[1],self.b[2],bc or self.bc,*s,ac or c)["result"]
    def test_retained_payroll(self):
        r=self.calc(1);self.assertEqual(r["payroll_saving_eur"],"0");self.assertGreater(r["active_human_seconds_released"],0)
    def test_eliminated_payroll(self):
        r=self.calc(2);self.assertEqual(r["payroll_saving_eur"],"80");self.assertEqual(r["alternative"]["active_human_seconds"],0);self.assertIsNone(r["alternative"]["employment_effect"])
    def test_output_and_sales(self):
        r=self.calc(3);self.assertEqual(r["alternative"]["sales"],36);self.assertEqual(r["incremental_revenue_eur"],"156")
    def test_unsold(self):
        r=self.calc(3,replace(self.bc,max_sales=23),replace(self.alts[3][1],max_sales=23));self.assertEqual(r["incremental_revenue_eur"],"0");self.assertEqual(r["alternative"]["unsold_correct_outputs"],13)
    def test_cost_identity(self):
        for i in range(4):
            r=self.calc(i)
            for x in (r["baseline"],r["alternative"]):
                self.assertEqual(F(x["revenue_eur"])-F(x["full_scoped_cost_eur"]),F(x["accounting_operating_result_eur"]))
                self.assertEqual(F(x["accounting_operating_result_eur"])+F(x["depreciation_eur"]),F(x["cash_operating_surplus_eur"]))
    def test_npv_identity(self):
        r=self.calc(2);self.assertEqual(F(r["incremental_npv_eur"]),F(r["alternative"]["npv_eur"])-F(r["baseline"]["npv_eur"]))
    def test_zero_rate(self):
        r=self.calc(2,replace(self.bc,discount_basis_points=0),replace(self.alts[2][1],discount_basis_points=0));self.assertEqual(F(r["incremental_npv_eur"]),sum(F(v) for v in r["incremental_cash_flows_eur"]))
    def test_funding_gap(self):
        r=self.calc(3);self.assertEqual(r["alternative"]["funding_gap_at_sampled_dates_eur"],"32500")
    def test_bad_paid_hours(self):
        c=self.alts[1][1];rr=tuple(replace(x,paid_seconds=0) if x.pool=="operator" else x for x in c.resources)
        with self.assertRaisesRegex(ValueError,"PAID_TIME_OR_DOUBLE_COUNT"):self.calc(1,ac=replace(c,resources=rr))
    def test_missing_pool(self):
        c=self.alts[1][1]
        with self.assertRaisesRegex(ValueError,"COST_POOL_COVERAGE"):self.calc(1,ac=replace(c,resources=c.resources[:-1]))
    def test_quality_veto(self):
        _,alts=variants(self.p);s=alts[-1];ac=self.cfg("stress",s)
        with self.assertRaisesRegex(ValueError,"BLOCK_OPERATIONAL_QUALITY"):assess(self.p,self.b[1],self.b[2],self.bc,*s,ac)
    def test_comparison_mismatch(self):
        with self.assertRaisesRegex(ValueError,"FINANCIAL_COMPARABILITY"):self.calc(1,ac=replace(self.alts[1][1],years=4))
    def test_no_sale(self):
        r=self.calc(3,replace(self.bc,max_sales=0),replace(self.alts[3][1],max_sales=0));self.assertIsNone(r["alternative"]["price_floor_at_fixed_activity_eur"])
    def test_replay(self):
        self.assertEqual(self.calc(1),self.calc(1))
    def test_audit(self):self.assertEqual(len(audit(self.p)["cases"]),5)
