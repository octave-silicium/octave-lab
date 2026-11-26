import copy
import unittest
from tools.requirements_matrix import project_document, validate

class MatrixTest(unittest.TestCase):
    def setUp(self):
        self.obj={"version":"1","status":"TARGET","entries":[{"id":"M001","status":"OPEN","acceptance":"test"},"a","b"]}
    def rows(self,obj=None):
        return project_document("x","g.json",obj or self.obj,("entries",),"abc")
    def test_exact_record_and_status(self):
        r=self.rows()[0]
        self.assertEqual(r["record"],self.obj["entries"][0])
        self.assertEqual(r["original_status"],"OPEN")
        self.assertEqual(r["source"]["pointer"],"/entries/0")
    def test_namespace(self):
        self.assertNotEqual(self.rows()[0]["id"],project_document("y","g.json",self.obj,("entries",),"abc")[0]["id"])
    def test_unnamed_reorder_identity(self):
        obj=copy.deepcopy(self.obj)
        obj["entries"].reverse()
        self.assertEqual({r["id"] for r in self.rows()}, {r["id"] for r in self.rows(obj)})
    def test_reject_duplicate(self):
        rows=self.rows()
        with self.assertRaises(ValueError): validate(rows+rows)
    def test_reject_drift(self):
        rows=self.rows()
        rows[0]["record"]={"id":"M001","status":"CLOSED"}
        with self.assertRaises(ValueError): validate(rows)
    def test_reject_promotion(self):
        rows=self.rows()
        rows[0]["qualification_promoted"]=True
        with self.assertRaises(ValueError): validate(rows)
    def test_map_pointer_escaping(self):
        rows=project_document("z","g.json",{"entries":{"a/b~c":"v"}},("entries",),"abc")
        self.assertEqual(rows[0]["source"]["pointer"],"/entries/a~1b~0c")
