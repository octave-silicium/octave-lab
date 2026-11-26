import copy
import hashlib
import unittest
from tools.validate_b2_review import validate

class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.q={"summary":{"revision":"x","publication_authorized":False},
                "groups":[{"group_id":"g","priority":"P0_REVIEW","members":[{"id":"i","path":"p","line":1}]}]}
        self.r={"queue_revision":"x","publication_authorized":False,
                "p0_order_sha256":hashlib.sha256(b"g").hexdigest(),
                "rows":[{"ordinal":1,"disposition":"ACTIVE_GAP","candidate_families":["LIM-D06"],
                         "rationale":"review rights","verification_status":"CONTEXT_AND_EVIDENCE_PENDING",
                         "closure_authorized":False}]}
    def test_binding(self):
        self.assertEqual(validate(self.r,self.q,{"LIM-D06"})["rows"][0]["group_id"],"g")
    def test_drift(self):
        self.q["groups"][0]["group_id"]="wrong"
        with self.assertRaises(ValueError): validate(self.r,self.q,{"LIM-D06"})
    def test_no_closure(self):
        self.r["rows"][0]["closure_authorized"]=True
        with self.assertRaises(ValueError): validate(self.r,self.q,{"LIM-D06"})
    def test_missing_mapping(self):
        self.r["rows"]=[]
        with self.assertRaises(ValueError): validate(self.r,self.q,{"LIM-D06"})
    def test_unknown_family(self):
        with self.assertRaises(ValueError): validate(self.r,self.q,set())
