import json,unittest
from fractions import Fraction as F
from pipeline.vertical_v2b2 import *
class SignatureTests(unittest.TestCase):
    def fixture(self):
        def s(v,sel):return {"selectors":sel,"levels":{p:{"value":str(x)} for p,x in v.items()}}
        a={"geo":"FR","nace_r2":"J","freq":"Q","s_adj":"SCA"}
        return {"gva_real":s({"2025-Q2":100,"2026-Q2":110},{**a,"unit":"CLV20_MEUR","na_item":"B1G"}),
                "total_hours":s({"2025-Q2":100,"2026-Q2":90},{**a,"unit":"THS_HW","na_item":"EMP_DC"})}
    def test_exact_identity(self):
        r=change(self.fixture(),"2025-Q2","2026-Q2")
        self.assertEqual(r["signature"],"GVA_UP_HOURS_DOWN")
        self.assertEqual(F(r["productivity_change_pct"]),F(200,9))
    def test_missing_no_imputation(self):
        self.assertIsNone(change(self.fixture(),"2025-Q2","2026-Q3")["signature"])
    def test_wrong_scope(self):
        s=self.fixture();s["total_hours"]["selectors"]["s_adj"]="NSA"
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE_NATIVE_SCOPE"):signatures(s)
    def test_other_signs(self):
        self.assertEqual(sign_signature(F(2),F(1)),"GVA_UP_HOURS_GROW_SLOWER")
        self.assertEqual(sign_signature(F(1),F(2)),"GVA_UP_HOURS_GROW_FASTER")
        self.assertEqual(sign_signature(F(-1),F(-1)),"BOTH_DOWN")
    def test_vintage_refusal(self):
        pin={"sources":{"x":{"sha256":"old"}}};e={"result":{"sources":{"x":{"status":"RETRIEVED","sha256":"new"}}}}
        with self.assertRaisesRegex(ValueError,"UNREVIEWED_ECONOMIC_VINTAGE"):pin_check(e,pin)
