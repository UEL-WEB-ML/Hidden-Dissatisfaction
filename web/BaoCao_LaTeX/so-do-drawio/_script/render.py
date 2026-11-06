"""Xuất .drawio -> .png bằng draw.io viewer (Chromium headless).
python3 render.py out_png_dir file1.drawio file2.drawio ..."""
import html, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(device_scale_factor=2.5, viewport={"width": 2400, "height": 1600})
    for f in sys.argv[2:]:
        xml = Path(f).read_text()
        cfg = html.escape(json.dumps({"xml": xml, "toolbar": "", "border": 16, "nav": False, "resize": True}), quote=True)
        pg.set_content(f'<html><body style="margin:0;background:#fff"><div class="mxgraph" data-mxgraph="{cfg}"></div>'
                       f'<script src="https://viewer.diagrams.net/js/viewer-static.min.js"></script></body></html>')
        pg.wait_for_selector(".mxgraph svg", timeout=60000)
        pg.wait_for_timeout(800)
        el = pg.locator(".mxgraph svg").first
        name = Path(f).stem + ".png"
        el.screenshot(path=str(out / name), omit_background=False)
        print("ok", name)
    b.close()
