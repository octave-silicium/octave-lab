"""Browser smoke tests on real archived data; no screenshot publication."""
import json,time,re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
base="http://127.0.0.1:8765"
out=Path("browser-audit");out.mkdir(exist_ok=True)
checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch()
    for width,height in [(1440,900),(1280,800),(768,1024),(390,844)]:
        page=browser.new_page(viewport={"width":width,"height":height})
        errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
        t=time.perf_counter();page.goto(base);expect(page.locator("#count")).to_have_text(re.compile(r"2\s?478"),timeout=15000)
        ready_ms=round((time.perf_counter()-t)*1000)
        assert page.locator("#count").inner_text().replace("\u202f","").replace("\xa0","")=="2478"
        expect(page.locator("#plot svg")).to_have_count(1)
        assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth+1")
        page.locator("#table-tab").click()
        page.locator("#rows button").first.click()
        assert page.locator("#proof .proof-value").inner_text()=="100"
        page.locator("#next").click()
        expect(page.locator("#page")).to_have_text(re.compile(r"^51"))
        page.locator("#theme").click()
        assert page.locator("html").get_attribute("data-theme")=="light"
        page.locator("#theme").click()
        page.locator("#chart-tab").click()
        page.locator("#start").fill("2020-02-01");page.locator("#end").fill("2020-02-02")
        page.locator("#range button[type=submit]").click()
        expect(page.locator("#count")).to_have_text("2")
        page.locator("#plot circle").first.click()
        expect(page.locator("#proof .proof-value")).to_have_text("100")
        page.locator(".compare-panel summary").click()
        page.locator("#compare-form button").click()
        expect(page.locator("#compare-result")).to_contain_text("Aucun taux calculé")
        page.locator("#windows button").first.click()
        expect(page.locator("#count")).to_have_text("30")
        page.locator("#sources button").filter(has_text="Insee").click()
        page.locator("#series-query").fill("industrie")
        page.locator("#series-search button").click()
        expect(page.locator("#active-filters")).to_contain_text("industrie")
        page.locator("#active-filters button").first.click()
        page.wait_for_selector("#series-select")
        expect(page.locator('#series-select option[value="0"]')).to_have_count(1)
        page.locator("#series-select").select_option("0")
        expect(page.locator("#count")).to_have_text("50")
        assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth+1")
        page.screenshot(path=str(out/f"viewport-{width}.png"),full_page=True)
        assert not errors
        checks.append({"width":width,"height":height,"ready_ms":ready_ms,"journey_pass":True,"no_horizontal_overflow":True,"no_js_errors":True,"screenshot_rendered":True})
        page.close()
    page=browser.new_page()
    response=page.request.get(base+"/api/sources")
    assert response.ok and response.headers["cache-control"]=="no-store"
    assert page.request.get(base+"/api/sources",headers={"Host":"example.org"}).status==403
    assert page.request.get(base+"/api/export").status==404
    browser.close()
print(json.dumps({"viewports":checks,"security_smoke":"PASS","screenshots_publicly_uploaded":False,"visual_review":"NOT_PERFORMED","wcag_conformance":"NOT_AUDITED"},indent=2))
