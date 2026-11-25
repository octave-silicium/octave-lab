import unittest,tempfile
from pathlib import Path
from pipeline.vertical_mmo import compare,records,PINS,digest as md
from pipeline.vertical_v2b3 import integrate
from pipeline.economic_core import canonical,digest
class MmoTests(unittest.TestCase):
    def test_exact_change_missing_zero(self):
        r=compare({"values":{"a":3,"b":0,"c":None}},{"values":{"a":4,"b":1,"c":2}})
        self.assertEqual(r["a"]["pct"],"100/3");self.assertIsNone(r["b"]["pct"]);self.assertNotIn("c",r)
    def test_wrong_vintage(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"wrong.xlsx";p.write_bytes(b"wrong")
            with self.assertRaisesRegex(ValueError,"UNREVIEWED_WORKBOOK"):records(p,"quarterly")
    def test_integration_fixture(self):
        b={"phase":"V2b2","publication":"BLOCK_PUBLICATION","economic_evidence":{"national_context":[{"id":"N01"},{"id":"N02"}]},"claims":[],"overview":{"claim_refs":[],"observation_refs":[]},"sections":[{"id":"D10","content":"","claim_refs":[]}],"coverage":[{"id":"M049","reason":"","claim_refs":[]}],"code_sha256":{}}
        m={"phase":"V2b3-MMO","publication":"BLOCK_PUBLICATION","sources":{k:{"sha256":v} for k,v in PINS.items()}}
        r=integrate({"result":b,"sha256":digest(canonical(b))},{"result":m,"sha256":md(m)})
        self.assertEqual(r["result"]["phase"],"V2b3");self.assertEqual(r["result"]["claims"][0]["id"],"C08");self.assertEqual(b["claims"],[])
    def test_tamper(self):
        with self.assertRaisesRegex(ValueError,"BASE_HASH"):integrate({"result":{},"sha256":"bad"},{})
