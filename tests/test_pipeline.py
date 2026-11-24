import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1] / 'pipeline'))
from run import validate_csv, analyze_sector, is_complete_quarter

class PipelineTest(unittest.TestCase):
  def test_reject_html(self):
    with self.assertRaises(ValueError):validate_csv(b'<html>x</html>','indeed_fr_sector')
  def test_reject_empty_csv(self):
    with self.assertRaises(ValueError):validate_csv(b'date,value\n','indeed_fr_sector')
  def test_sector_requires_real_coverage(self):
    csv=b'date,jobcountry,variable,display_name,indeed_job_postings_index\n2026-06-01,FR,total postings,Accounting,120\n'
    with self.assertRaises(ValueError):validate_csv(csv,'indeed_fr_sector')
  def test_aggregate_is_not_sector(self):
    csv=b'date,jobcountry,indeed_job_postings_index_SA,variable\n'+b''.join(f'2023-01-{i:02d},FR,100,total postings\n'.encode() for i in range(1,11))
    with self.assertRaises(ValueError):validate_csv(csv,'indeed_fr_sector')
  def test_sector_synthetic_quarters(self):
    import csv, io, datetime as dt
    out=io.StringIO();w=csv.writer(out);w.writerow(['date','jobcountry','variable','display_name','indeed_job_postings_index'])
    for year,value in [(2024,130),(2025,100)]:
      for day in range(1,91):
        date=dt.date(year,1,1)+dt.timedelta(days=day-1)
        w.writerow([date.isoformat(),'FR','total postings','synthetic_accounting',value])
    with tempfile.TemporaryDirectory() as t:
      r=analyze_sector(out.getvalue().encode(),Path(t))
      self.assertEqual(r['yoy_comparisons'],1)
      self.assertIn('-23.08',(Path(t)/'indeed_sector_yoy_comparison.csv').read_text())

  def test_incomplete_quarter_rejected(self):
    import datetime as dt
    obs=[(dt.date(2026,4,1)+dt.timedelta(days=i),100.0) for i in range(65)]
    self.assertFalse(is_complete_quarter(obs,'2026Q2'))

  def test_complete_quarter_accepted(self):
    import datetime as dt
    obs=[(dt.date(2026,4,1)+dt.timedelta(days=i),100.0) for i in range(91)]
    self.assertTrue(is_complete_quarter(obs,'2026Q2'))

if __name__=='__main__':unittest.main()
