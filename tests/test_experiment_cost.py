import unittest,copy
from decimal import Decimal
from pipeline.experiment_cost import cost_ledger
def tagged(v,b="MEASURED"):return {"value":v,"basis":b,"reference":"fixture-not-observed"}
def fixture():
    return {"currency":"EUR","scope":"DECLARED_PROCESS_BOUNDARY","hourly_rates":{"operator":tagged("36","ASSUMPTION"),"supervisor":tagged("72","ASSUMPTION")},"annual_fixed":{k:tagged("100","ASSUMPTION") for k in ("licenses","maintenance","integration_amortization")},"annual_volume":tagged("100","ASSUMPTION"),"cases":[{"id":"A","wall_seconds":tagged("30"),"human_time_complete":True,"reference":"fixture","human_intervals":[{"person":"p1","role":"operator","phase":"initial","start_seconds":"0","end_seconds":"20","reference":"fixture"},{"person":"p2","role":"supervisor","phase":"supervision","start_seconds":"10","end_seconds":"30","reference":"fixture"}],"direct_costs":{"model_api":tagged("0.10"),"compute":tagged("0.05"),"other_variable":tagged("0","EXPLICIT_ZERO")},"error_cost":tagged("0","ASSUMPTION")}]}
class CostTests(unittest.TestCase):
    def test_full_cost_and_person_time(self):
        r=cost_ledger(["A"],fixture())
        self.assertEqual(Decimal(r["human_person_seconds"]["total"]),40)
        self.assertEqual(Decimal(r["wall_seconds"]["total"]),30)
        self.assertEqual(Decimal(r["mean_full_cost_eur"]),Decimal("3.75"))
    def test_missing_not_zero(self):
        f=fixture();del f["cases"][0]["direct_costs"]["compute"]
        r=cost_ledger(["A"],f)
        self.assertIsNone(r["mean_full_cost_eur"])
        self.assertEqual(r["full_cost_eur"]["covered_cases"],0)
    def test_overlap(self):
        f=fixture();f["cases"][0]["human_intervals"][1]["person"]="p1"
        with self.assertRaisesRegex(ValueError,"HUMAN_OVERLAP"):cost_ledger(["A"],f)
    def test_incomplete_and_invalid_zero(self):
        f=fixture();f["cases"][0]["human_time_complete"]=False
        with self.assertRaisesRegex(ValueError,"COMPLETENESS"):cost_ledger(["A"],f)
        f=fixture();f["cases"][0]["direct_costs"]["compute"]=tagged("1","EXPLICIT_ZERO")
        with self.assertRaisesRegex(ValueError,"ZERO_BASIS"):cost_ledger(["A"],f)
    def test_nonmeasured_wall(self):
        f=fixture();f["cases"][0]["wall_seconds"]=tagged("30","ASSUMPTION")
        with self.assertRaisesRegex(ValueError,"BASIS"):cost_ledger(["A"],f)
