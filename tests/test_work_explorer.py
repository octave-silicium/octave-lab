import unittest
from pipeline.work_explorer import WorkExplorer
from pipeline.work_graph import Graph
from test_work_graph import fixture
class WorkExplorerTests(unittest.TestCase):
    def test_scope_search_and_profile(self):
        g=Graph(fixture(),{})
        x=WorkExplorer(onet=g)
        self.assertEqual(x.search("onet","synthétic")["total"],1)
        p=x.profile("onet","11-1111.00",limit=1)
        self.assertEqual(p["total"],2)
        self.assertEqual(p["next_offset"],1)
        self.assertEqual(p["rows"][0]["kind"],"TASK")
        self.assertEqual(len(p["rows"][0]["related"]),2)
        self.assertEqual(p["actions"],[])
        with self.assertRaises(ValueError):x.search("rome")
        with self.assertRaises(ValueError):x.search("onet",limit=101)
