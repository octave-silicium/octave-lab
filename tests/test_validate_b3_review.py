import hashlib
import unittest
from tools.validate_b3_review import validate, refs

class B3Test(unittest.TestCase):
    def setUp(self):
        self.q={"summary":{"revision":"x","publication_authorized":False},
                "groups":[{"group_id":"g0","priority":"P0_REVIEW"},{"group_id":"g1","priority":"P1_REVIEW",
                           "members":[{"id":"i","path":"docs/RESULT-001.md","line":1,"verbatim":"M001 D01"}],
                           "file_suggestions":[]}]}
        self.r={"queue_revision":"x","publication_authorized":False,
                "non_p0_order_sha256":hashlib.sha256(b"g1").hexdigest(),"rows":[]}
    def test_routing_not_review(self):
        s=validate(self.r,self.q,{"LIM-D06"},{"M001","D01"})["summary"]
        self.assertEqual(s["routing_only_pending"],1)
        self.assertEqual(s["first_pass_reviewed"],0)
    def test_literal_ids_not_partial(self):
        self.assertEqual(refs("LIM-D06 M001 M0012 D01",{"D06","LIM-D06","M001","D01"}),["D01","LIM-D06","M001"])
    def test_drift(self):
        self.r["non_p0_order_sha256"]="bad"
        with self.assertRaises(ValueError): validate(self.r,self.q,set(),set())
    def test_outside_scope(self):
        self.r["rows"]=[{"ordinal":1}]
        with self.assertRaises(ValueError): validate(self.r,self.q,set(),set())
    def test_no_false_closure(self):
        self.r["rows"]=[{"ordinal":2,"disposition":"CONTRACT","candidate_families":["LIM-D06"],
                         "rationale":"test","verification_status":"CONTEXT_AND_EVIDENCE_PENDING","closure_authorized":True}]
        with self.assertRaises(ValueError): validate(self.r,self.q,{"LIM-D06"},set())
