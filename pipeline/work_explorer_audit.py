import json,threading
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from urllib.parse import urlencode
from . import work_graph,rome_graph
from .european_work import fetch
from .rome_inventory import URL
from .work_explorer import WorkExplorer
from .explorer import make_handler,LazyExplorer
def run():
    x=WorkExplorer(work_graph.build(),rome_graph.load(fetch(URL)[0]))
    server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(LazyExplorer(),work=x))
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    def get(path,q={}):
        c=HTTPConnection("127.0.0.1",server.server_port,timeout=30)
        try:
            c.request("GET",path+"?"+urlencode(q));r=c.getresponse();return r.status,r.read()
        finally:c.close()
    try:
        for path in ("/work","/work.js","/work.css"):assert get(path)[0]==200
        s=json.loads(get("/api/work/sources")[1])["sources"]
        result={}
        for source in ("onet","rome"):
            status,b=get("/api/work/search",{"source":source,"limit":1});assert status==200
            d=json.loads(b);ident=d["rows"][0]["id"]
            status,b=get("/api/work/profile",{"source":source,"id":ident,"limit":1});assert status==200
            p=json.loads(b);assert p["actions"]==[] and p["publication"]=="BLOCK_PUBLICATION"
            result[source]={"occupations":d["total"],"profile_http":"PASS","profile_native_rows":p["total"]}
        assert get("/api/work/search",{"source":"esco"})[0]==400
        return {"scope":"REAL_ONET_ROME_HTTP_ESCO_NOT_CONFIGURED","sources":result,"assets":"PASS","no_fallback":"PASS","public":False}
    finally:server.shutdown();server.server_close();t.join()
if __name__=="__main__":print(json.dumps(run(),indent=2))
