import csv,io,unittest
from pipeline.task_ratings import Ratings,FIELDS
from pipeline.work_graph import Graph
from test_work_graph import fixture
def data(flag="N",value="4.2",scale="IM",cat=""):
    g=Graph(fixture(),{})
    t=next(n for n in g.nodes.values() if n["kind"]=="task")
    code,tid=t["native_id"].split(":")
    fields=sorted(FIELDS)
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
    w.writerow({"O*NET-SOC Code":code,"Task ID":tid,"Scale ID":scale,"Scale Name":"Fixture","Category":cat,"Data Value":value,"N":"25","Recommend Suppress":flag,"Date":"01/2026","Domain Source":"Fixture"})
    cats=("Scale ID,Category,Category Description\n"+"".join(f"FT,{i},Fixture {i}\n" for i in range(1,8))).encode()
    return g,out.getvalue().encode(),cats,t["id"]
class RatingTests(unittest.TestCase):
    def test_mask(self):
        g,r,c,t=data("Y")
        self.assertIsNone(Ratings(g,r,c).task(t)["ratings"][0]["value"])
    def test_native_scale(self):
        g,r,c,t=data()
        p=Ratings(g,r,c).task(t)
        self.assertEqual(p["ratings"][0]["value"],"4.2")
        self.assertIsNone(p["duration_seconds"])
    def test_invalid_range(self):
        g,r,c,t=data(value="6")
        with self.assertRaisesRegex(ValueError,"SCALE_RANGE"):Ratings(g,r,c)
    def test_unknown_precision(self):
        g,r,c,t=data("")
        self.assertEqual(Ratings(g,r,c).task(t)["ratings"][0]["status"],"REVIEW_REQUIRED")

    def test_api_opt_in(self):
        from pipeline.work_explorer import WorkExplorer
        g,r,c,t=data()
        with self.assertRaises(ValueError):WorkExplorer(onet=g).dispatch("/api/work/ratings",{"id":t})
        x=WorkExplorer(onet=g,ratings=Ratings(g,r,c))
        self.assertEqual(x.dispatch("/api/work/ratings",{"id":t})["ratings"][0]["value"],"4.2")
