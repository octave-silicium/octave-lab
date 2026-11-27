import copy
import unittest
from pipeline.economic_postlab_governance import ROOT, MAIN, DETAIL, LEDGER, read, validate, template, validate_receipt

class TestPostlabGovernance(unittest.TestCase):
    def setUp(self):
        self.main=read(ROOT/MAIN)
        self.detail=read(ROOT/DETAIL)
        self.ledger=read(ROOT/LEDGER)
    def test_inventory(self):
        self.assertEqual(validate(self.main,self.detail,self.ledger)["items"],297)
    def test_missing(self):
        self.ledger["entries"].pop()
        with self.assertRaisesRegex(ValueError,"MISSING_OR_UNKNOWN"):
            validate(self.main,self.detail,self.ledger)
    def test_unproven_closure(self):
        self.ledger["entries"][0]["status"]="COMPLETE"
        with self.assertRaisesRegex(ValueError,"UNPROVEN_CLOSURE"):
            validate(self.main,self.detail,self.ledger)
    def test_unproven_step(self):
        next(iter(self.ledger["entries"][0]["steps"].values()))["status"]="DONE"
        with self.assertRaisesRegex(ValueError,"UNPROVEN_DONE"):
            validate(self.main,self.detail,self.ledger)
    def test_unreviewed_template(self):
        r=template(self.ledger,"V3e")
        self.assertEqual(len(r["dispositions"]),297)
        with self.assertRaises(ValueError):
            validate_receipt(self.ledger,r)
    def test_receipt_complete_and_missing(self):
        r=template(self.ledger,"fixture")
        r.update(status="REVIEWED",date="fixture",reviewer="fixture",scope="fixture",baseline_commit="fixture",next_milestone="fixture")
        for d in r["dispositions"]:
            d.update(status="OUT_OF_SCOPE",reason="synthetic test only",next_action="review at next scope")
        self.assertEqual(validate_receipt(self.ledger,r)["dispositions"],297)
        r["dispositions"].pop()
        with self.assertRaisesRegex(ValueError,"RECEIPT_COVERAGE"):
            validate_receipt(self.ledger,r)
    def test_changed_label(self):
        self.ledger["entries"][0]["label"]="changed"
        with self.assertRaisesRegex(ValueError,"LABEL_OR_KIND_CHANGED"):
            validate(self.main,self.detail,self.ledger)
