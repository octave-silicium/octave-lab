import unittest
from datetime import date
from pipeline.data_observatory import check,run,validate_indeed,read_registry
class ObservatoryTests(unittest.TestCase):
    def test_registry(self):
        s=read_registry();self.assertEqual(len(s),14);self.assertEqual(sum(x["kind"]=="manual" for x in s),3)
    def test_calendar(self):
        sources=[{"id":"d","frequency":"daily"},{"id":"w","frequency":"weekly"},{"id":"m","frequency":"monthly"}]
        checker=lambda s:{"id":s["id"],"status":"CHECKED"}
        self.assertEqual(run(sources,True,date(2026,11,24),checker)["due"],1)
        self.assertEqual(run(sources,True,date(2026,11,23),checker)["due"],2)
        self.assertEqual(run(sources,False,date(2026,11,24),checker)["due"],3)
    def test_valid_native(self):
        raw=b"date,jobcountry,variable,indeed_job_postings_index_SA\n2026-01-01,FR,total postings,100\n"
        self.assertEqual(validate_indeed(raw,"indeed_national")["selected_rows"],1)
        with self.assertRaises(ValueError):validate_indeed(raw.replace(b",FR,",b",US,"),"indeed_national")
    def test_fail_closed(self):
        s={"id":"x","kind":"xlsx","url":"https://example.org"}
        r=check(s,lambda *a:(b"<html>blocked</html>","text/html",""))
        self.assertEqual(r["status"],"FAILED");self.assertEqual(r["promotion"],"NOT_PERFORMED")
    def test_manual_no_network(self):
        def fail(*a):raise AssertionError("unexpected call")
        self.assertEqual(check({"id":"x","kind":"manual","reason":"fixture"},fail)["status"],"MANUAL_REVIEW")
