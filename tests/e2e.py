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
        rec(f"R8 [{size}] no Tech shelf without ?v23", "Tech" not in pg.evaluate("[...document.querySelectorAll('#tabs button')].map(b=>b.firstChild.textContent)"))
        rec(f"R4 [{size}] Discover shows posters", pg.evaluate("document.querySelectorAll('#grid .card .poster img').length") > 20)
        rec(f"R5 [{size}] Discover poster links open Infuse by TMDB id", pg.evaluate("[...document.querySelectorAll('#grid .card a.poster')].every(a=>/^infuse:\\/\\/(movie|series)\\/\\d+$/.test(a.getAttribute('href')))"))
        rec(f"R6 [{size}] no page errors (preview off)", not pg.errs, pg.errs)
        pg.context.close()
        # --- V2.3, preview on ---
        pg = page(b, vp, "?v23")
        def learn_y(): return pg.evaluate("[...document.querySelectorAll('#grid .lcard .y')].map(x=>x.textContent)")
        def tech():
            tab(pg, "Discover"); pg.evaluate("[...document.querySelectorAll('#tabs button')].find(b=>b.firstChild.textContent==='Tech').click()"); pg.wait_for_timeout(300)
        def menu(i, sym):
            sel = f"#grid .lcard >> nth={i}"; pg.hover(sel); pg.click(sel + " >> button.more")
            pg.evaluate("([i,s])=>[...document.querySelectorAll('#grid .lcard')[i].querySelectorAll('.opts button')].find(b=>b.textContent===s).click()", [i, sym]); pg.wait_for_timeout(300)
        def opts(i): return pg.evaluate("i=>[...document.querySelectorAll('#grid .lcard')[i].querySelectorAll('.opts button')].map(b=>b.textContent)", i)
        hs = pg.evaluate("[...document.querySelectorAll('#grid .sech')].map(x=>x.textContent)")
        rec(f"L1 [{size}] Watching: Learn header, then Watch", hs[:2] == ["Learn", "Watch"], hs)
        rec(f"L2 [{size}] Learn starts empty, with a hint to add from Tech", learn_y() == [] and "Tech" in pg.evaluate("document.querySelector('#grid .empty').textContent"))
        rec(f"L3 [{size}] Watch cards still there", pg.evaluate("document.querySelectorAll('#grid .card:not(.lcard)').length") > 0)
        # Tech shelf (piece 6) + covers (piece 7)
        tech()
        tabs = pg.evaluate("[...document.querySelectorAll('#tabs button')].map(b=>b.firstChild.textContent)")
        rec(f"D1 [{size}] Discover shelves start with Tech", tabs[:1] == ["Tech"], tabs)
        rec(f"D2 [{size}] Tech shows the 8 GSP videos in course order", learn_y() == [f"{k} of 8" for k in range(1, 9)], learn_y())
        rec(f"D3 [{size}] Tech chip shows the course", "GSP Series 8" in pg.evaluate("[...document.querySelectorAll('#chips button')].map(b=>b.textContent)"))
        rec(f"C1 [{size}] every tile shows its real cover", pg.evaluate("[...document.querySelectorAll('#grid .lcard .ltile img')].filter(i=>i.complete&&i.naturalWidth>0).length") == 8)
        # piece 5: ⋯ ▶ adds to Watching
        rec(f"A1 [{size}] Tech ⋯ offers ▶ Watching and ✓", opts(1) == ["▶", "✓"], opts(1))
        menu(1, "▶"); menu(3, "▶")
        rec(f"A2 [{size}] added video gets a Watching tag in Tech", pg.evaluate("document.querySelectorAll('#grid .lcard')[1].querySelector('.where')?.textContent") == "Watching")
        rec(f"A3 [{size}] once added, ⋯ offers ✕ remove and ✓", opts(1) == ["✕", "✓"], opts(1))
        rec(f"A4 [{size}] added list goes into the Trakt snapshot", pg.evaluate("window.__snapshot().LW") == ["GSP Series:2", "GSP Series:4"], pg.evaluate("window.__snapshot().LW"))
        tab(pg, "Watching")
        rec(f"A5 [{size}] Learn on Watching shows only the added videos", learn_y() == ["2 of 8", "4 of 8"], learn_y())
        order = pg.evaluate("[...document.querySelectorAll('#grid > *')].map(x=>x.classList.contains('lcard')?'L':x.classList.contains('card')?'W':'-').join('')")
        rec(f"A6 [{size}] Learn tiles before Watch cards", order.rfind("L") < order.find("W"), order)
        # piece 3: tap copies the title and opens Infuse
        pg.evaluate("window.__went=[]")
        title = pg.evaluate("document.querySelectorAll('#grid .lcard .t')[0].textContent")
        pg.click("#grid .lcard >> nth=0"); pg.wait_for_timeout(1300)
        clip = pg.evaluate("navigator.clipboard.readText()")
        rec(f"T1 [{size}] tap copies the video title", clip == title, (clip, title))
        rec(f"T2 [{size}] tap then opens Infuse", pg.evaluate("window.__went") == ["infuse://"], pg.evaluate("window.__went"))
        rec(f"T3 [{size}] toast tells you to paste in Search", "paste" in pg.evaluate("document.getElementById('toast').textContent"))
        # ✕ removes from Watching (Undo brings back)
        pg.evaluate("window.__went=[]"); menu(1, "✕")
        rec(f"A7 [{size}] ✕ takes it off Watching", learn_y() == ["2 of 8"], learn_y())
        rec(f"A8 [{size}] ⋯ actions never open Infuse", pg.evaluate("window.__went") == [])
        pg.click("#toast .undo"); pg.wait_for_timeout(300)
        rec(f"A9 [{size}] Undo puts it back", learn_y() == ["2 of 8", "4 of 8"], learn_y())
        # piece 4: ✓ marks watched → leaves Watching, saved, synced
        menu(0, "✓")
        rec(f"M1 [{size}] ✓ marks watched and it leaves Learn", learn_y() == ["4 of 8"], learn_y())
        rec(f"M2 [{size}] saved on the device + in the Trakt snapshot", pg.evaluate("JSON.parse(localStorage.getItem('learndone'))") == ["GSP Series:2"] and pg.evaluate("window.__snapshot().L") == ["GSP Series:2"])
        rec(f"M3 [{size}] watched also drops it from the added list", pg.evaluate("window.__snapshot().LW") == ["GSP Series:4"], pg.evaluate("window.__snapshot().LW"))
        snap_other = pg.evaluate("JSON.stringify(Object.assign({}, window.__snapshot(), {L: undefined, LW: undefined}))")
        pg.reload(); pg.wait_for_timeout(1200)
        rec(f"M4 [{size}] still right after reload", learn_y() == ["4 of 8"], learn_y())
        ok = pg.evaluate("window.__applyRemote('Movie Launcher\\n' + JSON.stringify(Object.assign(window.__snapshot(), {L: ['GSP Series:5'], LW: ['GSP Series:1', 'GSP Series:5']})))")
        rec(f"M5 [{size}] marks and adds from another device (Trakt) apply here", ok and learn_y() == ["1 of 8"], learn_y())
        rec(f"M6 [{size}] other lists untouched by Learn changes", pg.evaluate("JSON.stringify(Object.assign({}, window.__snapshot(), {L: undefined, LW: undefined}))") == snap_other)
        # Tech: watched filter + un-mark
        tech()
        rec(f"D4 [{size}] Tech Unwatched hides watched videos", "5 of 8" not in learn_y() and len(learn_y()) == 7, learn_y())
        pg.select_option("#wf", "watched"); pg.wait_for_timeout(300)
        rec(f"D5 [{size}] Tech Watched lists them, ⋯ offers ↺", learn_y() == ["5 of 8"] and opts(0) == ["↺"], (learn_y(), opts(0)))
        menu(0, "↺")
        rec(f"D6 [{size}] ↺ un-marks it", pg.evaluate("window.__snapshot().L") == [] and learn_y() == [])
        pg.select_option("#wf", "unwatched")
        # fix: a movie added to Watching by hand leaves once it's watched (marked in Infuse → Trakt)
        km = pg.evaluate("fetch('library.json').then(x=>x.json()).then(d=>d.items.find(i=>i.kind==='movie'&&i.status==='watched').key)")
        pg.evaluate("k=>{localStorage.setItem('watch', JSON.stringify([k])); localStorage.removeItem('done'); localStorage.removeItem('undone');}", km); pg.reload(); pg.wait_for_timeout(1200)
        tab(pg, "Watching")
        rec(f"W1 [{size}] a watched movie doesn't stay in Watching", not pg.evaluate("k=>!!document.querySelector('#grid .card[data-key=\"'+CSS.escape(k)+'\"]')", km))
        tab(pg, "Next")
        rec(f"L5 [{size}] Learn only on Watching (not on Next)", pg.evaluate("document.querySelectorAll('#grid .lcard').length") == 0)
        rec(f"R7 [{size}] no page errors (preview on)", not pg.errs, pg.errs)
        pg.screenshot(path=f"/tmp/e2e_{size}.png")
        pg.context.close()
    b.close()
srv.shutdown()
print(f"{sum(R)}/{len(R)} passed"); sys.exit(0 if all(R) else 1)
