"""Browser-level smoke test; requires Playwright and a running local Streamlit server."""
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


PAGES = [
    ("Evidence map", "Machine health research command center"),
    ("Maintenance replay", "Hypothetical failure cost"),
    ("Official NASA test", "Primary candidate:"),
    ("Temporal replay", "Cycle-by-cycle engine replay"),
    ("Physical bearings", "Physical vibration validation"),
    ("Adaptive reliability", "Adaptive forecasting and reliability"),
    ("Independent replication", "Independent physical method replication"),
    ("Physical vibration replay", "Physical bearing vibration replay"),
    ("Technical report", "Technical evidence report"),
]


def run(url, output):
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(url, wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="AERIS | Research Intelligence", exact=True)).to_be_visible(timeout=60000)
        for number, (name, marker) in enumerate(PAGES, 1):
            if number > 1:
                page.get_by_text(name, exact=True).first.click()
            expect(page.get_by_text(marker, exact=False).first).to_be_visible(timeout=30000)
            expect(page.get_by_text("Content integrity verified for", exact=False)).to_be_visible()
            expect(page.get_by_text("Research evidence integrity check failed", exact=False)).to_have_count(0)
            expect(page.get_by_test_id("stException")).to_have_count(0)
            page.screenshot(path=str(output / f"{number:02d}-{name.lower().replace(' ', '-')}.png"), full_page=True, animations="disabled")
        page.get_by_text("Virtual degradation laboratory",exact=True).first.click()
        expect(page.get_by_role("heading",name="Paired maintenance comparison")).to_be_visible(timeout=30000)
        expect(page.get_by_test_id("stException")).to_have_count(0)
        page.screenshot(path=str(output/"10-virtual-degradation-laboratory.png"),full_page=True,animations="disabled")
        page.get_by_text("Vibration laboratory", exact=True).first.click()
        expect(page.get_by_role("heading", name="AERIS | Vibration Laboratory", exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_text("48 Hz", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="Frequency spectrum")).to_be_visible()
        expect(page.get_by_test_id("stException")).to_have_count(0)
        page.screenshot(path=str(output/"11-vibration-laboratory.png"), full_page=True, animations="disabled")
        page.get_by_text("vertical", exact=True).first.click()
        expect(page.get_by_text("80 Hz", exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_test_id("stException")).to_have_count(0)
        if errors:
            raise RuntimeError(f"Browser errors: {errors}")
        browser.close()


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:8501")
    parser.add_argument("--output",type=Path,default=Path("browser-evidence"))
    args=parser.parse_args()
    run(args.url,args.output)
