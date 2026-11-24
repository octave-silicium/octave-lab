import unittest,tempfile,json,hashlib
from pathlib import Path
from pipeline.evaluation_packet import packet,write_packet
from pipeline.document_benchmark import suite
class PacketTests(unittest.TestCase):
    def test_reproducible_and_no_gold(self):
        d,g=suite();a=packet(d,23);b=packet(d,23)
        self.assertEqual(a,b);self.assertNotIn("stratum",a["prompt"])
        self.assertEqual(set(a["case_order"]),set(g["expected"]))
        self.assertEqual(hashlib.sha256(a["prompt"].encode()).hexdigest(),a["prompt_sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"candidate";r=write_packet(d,23,p)
            self.assertFalse(r["gold_exported"])
            self.assertEqual({x.name for x in p.iterdir()},{"prompt.txt","manifest.json"})
            self.assertEqual((p/"prompt.txt").read_text(),a["prompt"])
            with self.assertRaises(FileExistsError):write_packet(d,23,p)
    def test_reject_embedded_gold(self):
        d,_=suite();d["cases"][0]["expected"]="ACCEPT"
        with self.assertRaisesRegex(ValueError,"CASE_SCHEMA"):packet(d,23)
