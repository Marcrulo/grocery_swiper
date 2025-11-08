# capture_build_id_sync.py
from playwright.sync_api import sync_playwright
import re
import threading
import os

target_url = "https://www.tilbudsugen.dk/partner/netto-114?page=100"
pattern = re.compile(
    r"https://www\.tilbudsugen\.dk/_next/data/([^/]+)/dk/single/[^/?]+\.json\?id=[^&\s]+"
)

found = {}
evt = threading.Event()

def on_request(request):
    try:
        u = request.url
    except Exception:
        return
    m = pattern.search(u)
    if m and 'build_id' not in found:
        found['build_id'] = m.group(1)
        evt.set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.on("request", on_request)
    page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
    # wait up to 10 seconds for matching request
    evt.wait(timeout=10)
    browser.close()

build_id = found.get('build_id')
print("Captured build id:", build_id)
