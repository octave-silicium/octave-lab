import unittest
from pipeline.work_graph import Graph,parse,VERSION

def fixture():
    return {
      "occupation_data":[{"O*NET-SOC Code":"11-1111.00","Title":"Synthetic occupation","Description":"Fixture"}],
      "task_statements":[{"O*NET-SOC Code":"11-1111.00","Task ID":"1","Task":"Fixture task","Task Type":"Core"},{"O*NET-SOC Code":"11-1111.00","Task ID":"2","Task":"Unmapped fixture","Task Type":""}],
      "gwas_to_iwas_to_dwas":[{"GWA Element ID":"G","GWA Element Name":"General","IWA Element ID":"I","IWA Element Name":"Intermediate","DWA Element ID":"D1","DWA Element Name":"Detailed 1"},{"GWA Element ID":"G","GWA Element Name":"General","IWA Element ID":"I","IWA Element Name":"Intermediate","DWA Element ID":"D2","DWA Element Name":"Detailed 2"}],
      "tasks_to_dwas":[{"O*NET-SOC Code":"11-1111.00","Task ID":"1","DWA Element ID":"D1"},{"O*NET-SOC Code":"11-1111.00","Task ID":"1","DWA Element ID":"D2"}]}
class GraphTests(unittest.TestCase):
    def test_many_to_many_and_unknown(self):
        g=Graph(fixture(),{})
        p=g.profile("11-1111.00")
        self.assertEqual(p["coverage"],{"tasks":2,"mapped_tasks":1})
        self.assertEqual(len(p["tasks"][0]["activities"]),2)
        self.assertEqual(p["atomic_actions"],[])
        self.assertEqual(p["impact_estimates"],[])
        self.assertEqual(g.audit()["unmapped_tasks"],1)
    def test_dangling(self):
        f=fixture()
        f["tasks_to_dwas"][0]["DWA Element ID"]="missing"
        with self.assertRaisesRegex(ValueError,"DANGLING_EDGE"):Graph(f,{})
    def test_duplicate(self):
        f=fixture();f["tasks_to_dwas"].append(f["tasks_to_dwas"][0])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_EDGE"):Graph(f,{})
    def test_search_and_scope(self):
        g=Graph(fixture(),{})
        self.assertEqual(g.search("SYNTHETIC")["total"],1)
        self.assertEqual(g.search("France")["total"],0)
        self.assertEqual(g.profile("11-1111.00")["geography"],"US")
        with self.assertRaises(ValueError):g.profile("unknown")
    def test_schema_and_count(self):
        raw=b"O*NET-SOC Code,Title,Description\n11-1111.00,Fixture,Fixture\n"
        self.assertEqual(len(parse("occupation_data",raw,strict=False)),1)
        with self.assertRaisesRegex(ValueError,"ROW_COUNT"):parse("occupation_data",raw)
        with self.assertRaisesRegex(ValueError,"SCHEMA"):parse("occupation_data",b"wrong\nx\n")
