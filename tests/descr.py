# Fast area test (18 Nov): tap a title on Watching (card + rows) or Next to read its description (staging)
import http.server, socketserver, threading, os, time
from playwright.sync_api import sync_playwright
T0 = time.time()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); P = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
R = []
def rec(n, ok, d=""): R.append(ok); print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  " + str(d)))
TNG, FILM, SJ = "i:tv|Star Trek TNG", "i:movie|1- Making it/Antitrust (2001).mp4", "f:Steve Jobs/2000-2004 (iPod & Digital Hub)"
SEED = """([t,m,s])=>{const d=JSON.parse(localStorage.getItem('proto2')); const put=(k,id)=>{d.lists[k]=[id].concat(d.lists[k].filter(x=>x!==id))};
  d.lists.Tech=[]; put('Playlists',s); put('Series',t); put('Movies',m); localStorage.setItem('proto2', JSON.stringify(d)); localStorage.removeItem('lastplay');}"""
def btn(pg, label): return pg.evaluate("l=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim().startsWith(l))?.click()", label)
def row(sel, text): return f"[...document.querySelectorAll('{sel}')].find(e=>e.textContent.includes({text!r}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for size, vp in [("desktop", {"width": 1280, "height": 900}), ("phone", {"width": 390, "height": 844})]:
        pg = b.new_page(viewport=vp); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/api.trakt.tv/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{P}/index.html?staging"); pg.wait_for_selector("#grid, .p2list", timeout=8000)
        pg.evaluate(SEED, [TNG, FILM, SJ]); pg.reload(); pg.wait_for_timeout(600)
        pg.evaluate("window.__plays=0; window.__go=()=>{window.__plays++}; 0")
        # Watching row (series): title shows the episode text under the progress bar, again hides it, picture still plays
        tr = row(".p2list .p2r", "Star Trek")
        pg.evaluate(f"{tr}.querySelector('.t').click()"); pg.wait_for_timeout(400)
        txt = pg.evaluate(f"{tr}.querySelector('.tdsc')?.textContent||''")
        rec(f"D1 [{size}] Watching row: tap the title shows the episode description", len(txt) > 30 and 'No description' not in txt, txt[:60])
        rec(f"D2 [{size}] it sits under the progress bar and nothing played", pg.evaluate(f"(()=>{{const r={tr}; const c=r.querySelector('.p2cp'), d=r.querySelector('.tdsc'); return !!c && c.getBoundingClientRect().bottom <= d.getBoundingClientRect().top}})()") and pg.evaluate("window.__plays") == 0)
        pg.evaluate(f"{tr}.querySelector('.t').click()"); pg.wait_for_timeout(150)
        rec(f"D3 [{size}] tap the title again hides it", pg.evaluate(f"!{tr}.querySelector('.tdsc')"))
        pg.evaluate(f"{tr}.querySelector('.p2v').click()"); pg.wait_for_timeout(150)
        rec(f"D4 [{size}] tapping the picture still plays", pg.evaluate("window.__plays") == 1, pg.evaluate("window.__plays"))
        # Now watching card (Steve Jobs channel): title shows the next video's description
        pg.evaluate("document.querySelector('.nowc .bd b').click()"); pg.wait_for_timeout(200)
        ct = pg.evaluate("document.querySelector('.nowc .tdsc')?.textContent||''")
        rec(f"D5 [{size}] Now watching card: tap the title shows the description under the bar", len(ct) > 30 and pg.evaluate("(()=>{const c=document.querySelector('.nowc'); return c.querySelector('.pg') ? c.querySelector('.pg').getBoundingClientRect().bottom <= c.querySelector('.tdsc').getBoundingClientRect().top : true})()"), ct[:60])
        pg.evaluate("document.querySelector('.nowc .tdsc').click()"); pg.wait_for_timeout(150)
        rec(f"D6 [{size}] tapping the description hides it, nothing played", pg.evaluate("!document.querySelector('.nowc .tdsc')") and pg.evaluate("window.__plays") == 1)
        # Next: every chip
        btn(pg, "Next"); pg.wait_for_timeout(150)
        for chip, text, n in [("Series", "Star Trek", "D7"), ("Movies", "Antitrust", "D8"), ("Playlists", "2000-2004", "D9")]:
            btn(pg, chip); pg.wait_for_timeout(150); nr = row(".p2list .p2n", text)
            pg.evaluate(f"{nr}.querySelector('.nm').click()"); pg.wait_for_timeout(400)
            t = pg.evaluate(f"{nr}.querySelector('.tdsc')?.textContent||''")
            rec(f"{n} [{size}] Next › {chip}: tap the title shows the description, no menu", len(t) > 30 and pg.evaluate("!document.getElementById('p2menu')"), t[:60])
        btn(pg, "Movies"); pg.wait_for_timeout(150); pg.evaluate(f"{row('.p2list .p2n', 'Antitrust')}.querySelector('.th').click()"); pg.wait_for_timeout(150)
        rec(f"D10 [{size}] Next: tapping the picture still opens the menu", pg.evaluate("!!document.getElementById('p2menu')"))
        pg.screenshot(path=f"/tmp/descr-{size}.png")
        rec(f"D11 [{size}] no page errors", not errs, errs); pg.close()
    # live (no ?staging): unchanged
    pg = b.new_page(viewport={"width": 390, "height": 844}); pg.route("**/api.trakt.tv/**", lambda r: r.abort())
    pg.goto(f"http://127.0.0.1:{P}/index.html"); pg.wait_for_selector("#grid, .p2list", timeout=8000); pg.wait_for_timeout(500)
    rec("D12 [live] no tappable titles until the go", pg.evaluate("document.querySelectorAll('.dtap').length") == 0); pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
