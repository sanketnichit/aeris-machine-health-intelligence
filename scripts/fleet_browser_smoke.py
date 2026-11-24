"""Browser integration check against the isolated synthetic demo stack."""
import argparse
import json
import os
from urllib.request import Request,urlopen
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def incidents(api_url):
    token=os.environ.get("AERIS_API_TOKEN")
    request=Request(api_url.rstrip("/")+"/v1/incidents?limit=1000",
                    headers={"Authorization":"Bearer "+token} if token else {})
    with urlopen(request,timeout=10) as response:
        return json.load(response)["incidents"]


def run(url,output,api_url="http://127.0.0.1:8080",review=False):
    output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={"width":1440,"height":1000})
        errors=[]
        page.on("pageerror",lambda exc:errors.append(str(exc)))
        page.goto(url,wait_until="domcontentloaded")
        expect(page.get_by_role("heading",name="AERIS | Research Intelligence",exact=True)).to_be_visible(timeout=60000)
        page.get_by_text("Telemetry fleet",exact=True).first.click()
        expect(page.get_by_role("heading",name="AERIS | Telemetry fleet",exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_text("Registered assets",exact=True)).to_be_visible()
        expect(page.get_by_text("Operational forecast withheld",exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_text("Historical benchmark context — not asset calibration",exact=True)).to_be_visible()
        # Asset selector defaults to alphabetical first synthetic-drift.
        expect(page.get_by_text("Review the listed observations and open incidents with an engineer.",exact=True)).to_be_visible()
        expect(page.get_by_test_id("stException")).to_have_count(0)
        page.screenshot(path=str(output/"fleet-advisory.png"),full_page=True,animations="disabled")
        page.get_by_text("Recent monitoring events",exact=True).click()
        page.get_by_text("Review incidents",exact=True).click()
        expect(page.get_by_text("Download incident history",exact=True)).to_be_visible()
        expect(page.get_by_text("Download monitoring events",exact=True)).to_be_visible()
        page.screenshot(path=str(output/"fleet-events-and-incidents.png"),full_page=True,animations="disabled")
        page.get_by_text("Exploratory deviation analysis",exact=True).click()
        expect(page.get_by_text("Robust deviation from prior observed values only.",exact=False)).to_be_visible()
        expect(page.get_by_test_id("stException")).to_have_count(0)
        page.screenshot(path=str(output/"fleet-deviation.png"),full_page=True,animations="disabled")
        if review:
            active=[i for i in incidents(api_url) if i["status"] in ("open","acknowledged")]
            assert active and active[0]["status"]=="open"
            target=active[0]["incident_id"]
            page.get_by_label("Review note",exact=True).fill("Browser acknowledgement test")
            page.get_by_role("button",name="Submit review",exact=True).click()
            expect(page.get_by_text("acknowledged",exact=True).first).to_be_visible(timeout=30000)
            current=next(i for i in incidents(api_url) if i["incident_id"]==target)
            assert current["status"]=="acknowledged"
            assert current["history"][-1]["note"]=="Browser acknowledgement test"
            page.screenshot(path=str(output/"fleet-acknowledged.png"),full_page=True,animations="disabled")
        if errors:
            raise RuntimeError(f"Browser errors: {errors}")
        browser.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:8501")
    parser.add_argument("--output",type=Path,default=Path("fleet-browser-evidence"))
    parser.add_argument("--api-url",default="http://127.0.0.1:8080")
    parser.add_argument("--review",action="store_true")
    args=parser.parse_args()
    run(args.url,args.output,args.api_url,args.review)
