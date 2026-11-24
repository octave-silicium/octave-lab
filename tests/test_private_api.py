import hashlib,http.client,json,sqlite3,tempfile,threading,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from pipeline.explorer import make_handler,LazyExplorer
from pipeline.private_api import PrivateRoutes

class PrivateApiTests(unittest.TestCase):
    def test_private_opt_in_and_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"fixture.sqlite"
            c=sqlite3.connect(p)
            c.executescript("""
              CREATE TABLE source(id TEXT);
              CREATE TABLE esco_concept(uri TEXT,kind TEXT);
              CREATE TABLE esco_text(uri TEXT,label TEXT,lang TEXT);
              CREATE TABLE esco_relation(occupation TEXT,skill TEXT,relation TEXT);
              CREATE TABLE fap_mapping(kind TEXT,source TEXT,member TEXT,row_no INTEGER,rome TEXT,qualification TEXT,fap TEXT,source_fap_label TEXT,review TEXT);
              CREATE TABLE pcs_probability(id TEXT);
              CREATE TABLE mmo_internal(source TEXT,sheet TEXT,row_no INTEGER,col TEXT,period TEXT,sector TEXT,establishment_size TEXT,measure TEXT,unit TEXT,value TEXT,quality TEXT);
              INSERT INTO esco_concept VALUES('fixture:occupation','occupation');
              INSERT INTO esco_text VALUES('fixture:occupation','Fixture accountant','en');
              INSERT INTO mmo_internal VALUES('mmo_Q','MMO_trimestriels',1,'C','2026-T2','Fixture','All','Count','contracts','999','RESTRICTED');
            """);c.close()
            sha=hashlib.sha256(p.read_bytes()).hexdigest()
            private=PrivateRoutes(p,sha)
            def exercise(routes):
                server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(LazyExplorer(),routes))
                t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
                try:
                    def get(path,host=None,site=None):
                        conn=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=5)
                        headers={"Host":host or f"127.0.0.1:{server.server_port}"}
                        if site:headers["Sec-Fetch-Site"]=site
                        try:
                            conn.request("GET",path,headers=headers);r=conn.getresponse()
                            self.assertEqual(r.getheader("Cache-Control"),"no-store")
                            return r.status,json.loads(r.read())
                        finally:conn.close()
                    if routes is None:self.assertEqual(get("/api/private/status")[0],404);return
                    self.assertEqual(get("/api/private/status")[1]["snapshot_sha256"],sha)
                    self.assertEqual(len(get("/api/private/esco/search?q=accountant&lang=en")[1]["rows"]),1)
                    self.assertEqual(get("/api/private/status",host="example.org")[0],403)
                    self.assertEqual(get("/api/private/status",site="cross-site")[0],403)
                    self.assertEqual(get("/api/private/esco/search?q=a&q=b")[0],400)
                    self.assertEqual(get("/api/private/esco/search?q=a&limit=101")[0],400)
                    status,result=get("/api/private/mmo/series?source=mmo_Q&sheet=MMO_trimestriels&sector=Fixture&size=All&col=C&start=2026-T2&end=2026-T2")
                    self.assertEqual(status,200);self.assertIsNone(result["rows"][0]["value"])
                    self.assertEqual(get("/api/private/export")[0],400)
                finally:server.shutdown();server.server_close();t.join()
            try:exercise(None);exercise(private)
            finally:private.close()
