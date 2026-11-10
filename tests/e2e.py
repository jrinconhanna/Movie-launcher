"""Launcher integration test: every V2.3 piece together + V2/V2.2 regression,
on phone and desktop sizes, with the ?v23 preview on and off.
Run: python3 tests/e2e.py   (serves the repo on a local port, Trakt calls blocked)"""
import http.server, os, socketserver, sys, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}/index.html"
R = []
def rec(n, ok, d=""): R.append(ok); print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  " + str(d)[:300]))
def page(b, vp, q=""):
    ctx = b.new_context(viewport=vp, permissions=["clipboard-read", "clipboard-write"])
    pg = ctx.new_page(); pg.errs = []; pg.on("pageerror", lambda e: pg.errs.append(str(e)))
    pg.route("**/api.trakt.tv/**", lambda r: r.abort())
    pg.add_init_script("window.__went=[]; window.__go=function(u){window.__went.push(u)};")
    pg.goto(BASE + q); pg.wait_for_timeout(1200); return pg
def tab(pg, name): pg.evaluate("n=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim().startsWith(n)).click()", name); pg.wait_for_timeout(300)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    for size, vp in [("desktop", {"width": 1280, "height": 900}), ("phone", {"width": 390, "height": 844})]:
        # --- regression: V2 / V2.2, preview off ---
        pg = page(b, vp)
        rec(f"R1 [{size}] Watching shows posters", pg.evaluate("document.querySelectorAll('#grid .card .poster img').length") > 0)
        rec(f"R2 [{size}] no Learn without ?v23", pg.evaluate("document.querySelectorAll('#grid .lcard').length") == 0)
        tab(pg, "Next")
        hs = pg.evaluate("[...document.querySelectorAll('#grid .sech')].map(x=>x.textContent.split(' ')[0])")
        rec(f"R3 [{size}] Next shows Parked then Backlog", hs == ["Parked", "Backlog"], hs)
        tab(pg, "Discover")
        rec(f"R4 [{size}] Discover shows posters", pg.evaluate("document.querySelectorAll('#grid .card .poster img').length") > 20)
        rec(f"R5 [{size}] Discover poster links open Infuse by TMDB id", pg.evaluate("[...document.querySelectorAll('#grid .card a.poster')].every(a=>/^infuse:\\/\\/(movie|series)\\/\\d+$/.test(a.getAttribute('href')))"))
        rec(f"R6 [{size}] no page errors (preview off)", not pg.errs, pg.errs)
        pg.context.close()
        # --- V2.3, preview on ---
        pg = page(b, vp, "?v23")
        hs = pg.evaluate("[...document.querySelectorAll('#grid .sech')].map(x=>x.textContent)")
        rec(f"L1 [{size}] Learn header, then Watch", hs[:2] == ["Learn", "Watch"], hs)
        nums = pg.evaluate("[...document.querySelectorAll('#grid .lcard .ln')].map(x=>x.textContent)")
        rec(f"L2 [{size}] 8 GSP tiles numbered 1..8", nums == [str(i) for i in range(1, 9)], nums)
        order = pg.evaluate("[...document.querySelectorAll('#grid > *')].map(x=>x.classList.contains('lcard')?'L':x.classList.contains('card')?'W':'-').join('')")
        rec(f"L3 [{size}] all Learn tiles before Watch cards", "W" not in order or order.rfind("L") < order.find("W"), order)
        rec(f"L4 [{size}] Watch cards still there under Learn", "W" in order, order)
        # piece 3: tap copies the title and opens Infuse
        title = pg.evaluate("document.querySelectorAll('#grid .lcard .t')[1].textContent")
        pg.click("#grid .lcard >> nth=1"); pg.wait_for_timeout(1300)
        clip = pg.evaluate("navigator.clipboard.readText()")
        rec(f"T1 [{size}] tap copies the video title", clip == title, (clip, title))
        rec(f"T2 [{size}] tap then opens Infuse", pg.evaluate("window.__went") == ["infuse://"], pg.evaluate("window.__went"))
        rec(f"T3 [{size}] toast tells you to paste in Search", "paste" in pg.evaluate("document.getElementById('toast').textContent"))
        tab(pg, "Next")
        rec(f"L5 [{size}] Learn only on Watching (not on Next)", pg.evaluate("document.querySelectorAll('#grid .lcard').length") == 0)
        rec(f"R7 [{size}] no page errors (preview on)", not pg.errs, pg.errs)
        pg.screenshot(path=f"/tmp/e2e_{size}.png")
        pg.context.close()
    b.close()
srv.shutdown()
print(f"{sum(R)}/{len(R)} passed"); sys.exit(0 if all(R) else 1)
