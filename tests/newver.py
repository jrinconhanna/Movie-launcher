# Fast area test (17 Nov): staging "New version · tap to reload" pill + build time in footer
import http.server, socketserver, threading, re
from playwright.sync_api import sync_playwright
ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); P = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
R = []
def rec(n, ok, d=""): R.append(ok); print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  " + str(d)))
src = open(ROOT + "/index.html", encoding="utf-8").read(); built = re.search(r"var BUILT = '([^']+)'", src).group(1)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for size, vp in [("desktop", {"width": 1280, "height": 900}), ("phone", {"width": 390, "height": 844})]:
        for newer in [False, True]:
            pg = b.new_page(viewport=vp); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.route("**/api.trakt.tv/**", lambda r: r.abort())
            if newer: pg.route("**/index.html?nv=*", lambda r: r.fulfill(status=200, content_type="text/html", body=src.replace("var BUILT = '" + built + "'", "var BUILT = '2099-01-01 00:00'")))
            pg.goto(f"http://127.0.0.1:{P}/index.html?staging"); pg.wait_for_timeout(4500)
            has = pg.evaluate("!!document.getElementById('newver')")
            if not newer:
                rec(f"V1 [{size}] staging: no pill when nothing newer", not has)
                rec(f"V2 [{size}] staging footer shows build time", (built[5:]) in pg.evaluate("document.getElementById('foot').innerText"), pg.evaluate("document.getElementById('foot').innerText")[:120])
            else:
                rec(f"V3 [{size}] staging: pill shows when a newer version is out", has)
                u0 = pg.url; rec(f"V4 [{size}] staging: no reload by itself", pg.url == u0)
                pg.click("#newver"); pg.wait_for_timeout(1200)
                rec(f"V5 [{size}] tap reloads past the cache, still on staging", "staging" in pg.url and "r=" in pg.url, pg.url)
            rec(f"V6 [{size}] no page errors", not errs, errs); pg.close()
        # 18 Nov: a newer library (data-only change) shows the pill; the same library doesn't
        for libnew in [True, False]:
            pg = b.new_page(viewport=vp); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.route("**/api.trakt.tv/**", lambda r: r.abort())
            if libnew: pg.route("**/library.json?nv=*", lambda r: r.fulfill(status=200, headers={"Last-Modified": "Fri, 01 Jan 2099 00:00:00 GMT"}, body=""))
            pg.goto(f"http://127.0.0.1:{P}/index.html?staging"); pg.wait_for_timeout(4500)
            has = pg.evaluate("!!document.getElementById('newver')")
            if libnew: rec(f"V8 [{size}] staging: pill shows when the library is newer (code unchanged)", has)
            else: rec(f"V9 [{size}] staging: no pill when the library is the same", not has)
            rec(f"V10 [{size}] no page errors", not errs, errs); pg.close()
        pg = b.new_page(viewport=vp); pg.route("**/api.trakt.tv/**", lambda r: r.abort())
        pg.route("**/index.html?nv=*", lambda r: r.fulfill(status=200, content_type="text/html", body=src.replace(built, "2099-01-01 00:00")))
        pg.goto(f"http://127.0.0.1:{P}/index.html"); pg.wait_for_timeout(4500)
        rec(f"V7 [{size}] live: no pill, ever", not pg.evaluate("!!document.getElementById('newver')")); pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed")
