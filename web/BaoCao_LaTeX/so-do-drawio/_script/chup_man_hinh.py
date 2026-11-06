"""Chụp màn hình web Hidden Dissatisfaction cho báo cáo.
Chạy: python3 shoot.py <out_dir>"""
import json, sys, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4200"
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
ACC = {"spec": ("demo_specialist", "DemoSpecialist#2026"), "mgr": ("demo_manager", "DemoManager#2026")}


def api(path, token, method="GET", body=None):
    req = urllib.request.Request(BASE + "/api/v1" + path, method=method,
                                 headers={"Authorization": "Bearer " + token, "content-type": "application/json"},
                                 data=json.dumps(body).encode() if body else None)
    return json.load(urllib.request.urlopen(req))


def token(role):
    u, p = ACC[role]
    req = urllib.request.Request(BASE + "/api/v1/auth/login", method="POST", headers={"content-type": "application/json"},
                                 data=json.dumps({"username": u, "password": p}).encode())
    return json.load(urllib.request.urlopen(req))["token"]


def ctx(b, role, w=1440, h=900, mobile=False):
    c = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if mobile else 1.5,
                      is_mobile=mobile, has_touch=mobile, locale="vi-VN")
    if role:
        t = token(role)
        c.add_init_script(f"localStorage.setItem('hd-token', {json.dumps(t)}); localStorage.setItem('hd-lang','vi');")
    else:
        c.add_init_script("localStorage.setItem('hd-lang','vi');")
    return c


def shot(page, url, name, full=True, wait=1200, action=None):
    page.goto(BASE + url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(wait)
    if action:
        action(page); page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("ok", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    tm = token("mgr")
    orders = api("/orders?status=OPEN&limit=50", tm)["items"]
    inprog = [o for o in orders if o["status"] == "IN_PROGRESS"]
    pend = [o for o in orders if o["status"] == "PENDING"]
    closed = api("/orders?status=COMPLETED&limit=5", tm)["items"]
    first = orders[0]["order_id"]
    json.dump({"inprog": inprog[:3], "first": first}, open(OUT / "ids.json", "w"), default=str, indent=1)

    # --- chưa đăng nhập
    c = ctx(b, None); pg = c.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    shot(pg, "/html/login.html", "login", full=False)
    def bad_login(pg):
        pg.fill("#l-user", "demo_specialist"); pg.fill("#l-pass", "sai-mat-khau-123")
        pg.keyboard.press("Enter"); pg.wait_for_timeout(1200)
    shot(pg, "/html/login.html", "login-sai-mat-khau", full=False, action=bad_login)
    c.close()

    # --- Specialist
    c = ctx(b, "spec"); pg = c.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    shot(pg, "/html/index.html", "spec-risk-queue")
    shot(pg, "/html/order.html?id=" + first, "spec-order-detail")
    shot(pg, "/html/attempt.html", "spec-attempt")
    shot(pg, "/html/profile.html", "spec-profile")
    c.close()

    # --- Manager
    c = ctx(b, "mgr"); pg = c.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    shot(pg, "/html/overview.html", "mgr-overview", wait=2000)
    shot(pg, "/html/index.html", "mgr-risk-queue")
    if inprog:
        shot(pg, "/html/order.html?id=" + inprog[0]["order_id"], "mgr-order-inprogress")
    if closed:
        shot(pg, "/html/order.html?id=" + closed[0]["order_id"], "mgr-order-closed")
    shot(pg, "/html/decision.html", "mgr-decision")
    shot(pg, "/html/audit.html", "mgr-audit")
    shot(pg, "/html/settings.html", "mgr-settings")
    c.close()

    # --- Điện thoại
    for role, pages in (("spec", [("index.html", "m-risk-queue"), ("order.html?id=" + first, "m-order")]),
                        ("mgr", [("overview.html", "m-overview")])):
        c = ctx(b, role, 390, 844, mobile=True); pg = c.new_page()
        for u, n in pages:
            shot(pg, "/html/" + u, n)
        c.close()
    c = ctx(b, None, 390, 844, mobile=True); pg = c.new_page(); shot(pg, "/html/login.html", "m-login", full=False); c.close()
    # máy tính bảng
    c = ctx(b, "mgr", 820, 1180); pg = c.new_page(); shot(pg, "/html/index.html", "t-risk-queue"); c.close()
    b.close()
    print("JS errors:", errs)
