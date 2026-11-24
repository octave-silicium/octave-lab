"""Browser acceptance using real O*NET and ROME; private ESCO is not available in CI."""
import json,re,shutil,threading,time
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from pipeline import work_graph,rome_graph
from pipeline.european_work import fetch
from pipeline.rome_inventory import URL
from pipeline.work_explorer import WorkExplorer
from pipeline.explorer import make_handler,LazyExplorer
def run():
    x=WorkExplorer(work_graph.build(),rome_graph.load(fetch(URL)[0]))
    server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(LazyExplorer(),work=x))
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    checks=[]
    try:
        with sync_playwright() as p:
            exe=shutil.which("google-chrome") or shutil.which("chromium")
            browser=p.chromium.launch(**({"executable_path":exe} if exe else {}))
            for width,height in [(1440,900),(1280,800),(768,1024),(390,844)]:
                page=browser.new_page(viewport={"width":width,"height":height})
                errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
                start=time.perf_counter();page.goto(f"http://127.0.0.1:{server.server_port}/work")
                expect(page.locator("#status")).to_contain_text("1016 professions")
                ready=round((time.perf_counter()-start)*1000)
                page.locator("#mode").select_option("concept")
                expect(page.locator("#status")).to_contain_text("2085 concepts")
                page.locator("#results button").first.click()
                expect(page.locator("#profile")).to_contain_text("professions distinctes")
                page.locator("#items button").first.click()
                expect(page.locator("#profile")).to_contain_text("relations natives")
                page.locator("#source").select_option("rome")
                expect(page.locator("#status")).to_contain_text("1923 professions")
                page.locator("#mode").select_option("concept")
                expect(page.locator("#status")).to_contain_text("concepts")
                page.locator("#results button").first.click()
                expect(page.locator("#profile")).to_contain_text("professions distinctes")
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                png=page.screenshot();assert len(png)>1000
                assert not errors
                checks.append({"width":width,"height":height,"ready_ms":ready,"journey_pass":True,"screenshot_rendered":True,"no_js_errors":True,"no_horizontal_overflow":True})
                page.close()
            browser.close()
    finally:server.shutdown();server.server_close();t.join()
    return {"viewports":checks,"scope":"REAL_ONET_ROME_BROWSER","visual_review":"NOT_PERFORMED","wcag":"NOT_AUDITED","screenshots_uploaded":False,"esco_browser":"NOT_TESTED"}
if __name__=="__main__":print(json.dumps(run(),indent=2))
