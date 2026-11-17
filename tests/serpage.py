# Fast area test (17 Nov): series page (staging) — Discover › tap a matched series
import http.server, socketserver, threading, os, time, json
from playwright.sync_api import sync_playwright
T0 = time.time(); ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); P = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
R = []
def rec(n, ok, d=""): R.append(ok); print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  " + str(d)))
lib = json.load(open(ROOT + "/library.json", encoding="utf-8"))
ms = [i for i in lib["items"] if i.get("kind") == "tv" and i.get("epm") == "ok" and i.get("group") == "Series" and os.path.exists(f"{ROOT}/eps/{i['tmdb']}.json")][0]
bad = [i for i in lib["items"] if i.get("kind") == "tv" and i.get("epm") not in (None, "ok") and i.get("group") == "Series"][0]
E1 = json.load(open(f"{ROOT}/eps/{ms['tmdb']}.json")); s1 = sorted(E1["seasons"], key=int)[0]; n1 = len(E1["seasons"][s1])
live = {"se": {str(ms["tmdb"]): {s1: [1, 2]}}, "er": {str(ms["tmdb"]): {s1 + "x2": 9}}, "s": {}, "m": [], "a": {}}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for size, vp in [("desktop", {"width": 1280, "height": 900}), ("phone", {"width": 390, "height": 844})]:
        pg = b.new_page(viewport=vp); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.route("**/api.trakt.tv/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{P}/index.html?staging"); pg.evaluate("l=>localStorage.setItem('trakt-live', JSON.stringify(l))", live); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent.trim().startsWith('Discover')).click()"); pg.wait_for_timeout(200)
        pg.evaluate("[...document.querySelectorAll('#tabs button')].find(b=>b.firstChild.textContent==='Series').click()"); pg.wait_for_timeout(200)
        pg.evaluate("document.getElementById('wf') && (document.getElementById('wf').value='all', document.getElementById('wf').dispatchEvent(new Event('change')))"); pg.wait_for_timeout(250)
        pg.evaluate("k=>document.querySelector('#grid .card[data-key=\"'+k+'\"] a.poster').click()", bad["key"]); pg.wait_for_timeout(300)
        rec(f"P1 [{size}] an unmatched series (in To check) doesn't open a page", not pg.evaluate("!!document.querySelector('.serp')"))
        pg.evaluate("k=>document.querySelector('#grid .card[data-key=\"'+k+'\"] a.poster').click()", ms["key"]); pg.wait_for_timeout(1200)
        rec(f"P2 [{size}] a matched series opens its page with its title", pg.evaluate("t=>!!document.querySelector('.serp') && document.querySelector('.sp-top b').textContent===t", ms["title"]), ms["title"])
        pg.evaluate("s=>{const b=[...document.querySelectorAll('.sp-chips button')].find(b=>b.textContent==='S'+s); b&&b.click()}", s1); pg.wait_for_timeout(200)
        rec(f"P3 [{size}] every episode of the season is listed", pg.evaluate("document.querySelectorAll('.sp-row').length") == n1, (pg.evaluate("document.querySelectorAll('.sp-row').length"), n1))
        rec(f"P4 [{size}] watched episodes (E1, E2 from Trakt) get the ✓ badge + grey, others don't", pg.evaluate("[...document.querySelectorAll('.sp-row')].slice(0,3).map(r=>!!r.querySelector('.sp-wk')).join()") == "true,true,false")
        rec(f"P5 [{size}] header counts watched in the season", f"2/{n1} watched" in pg.evaluate("document.querySelector('.sp-top small').textContent"))
        has_ov = pg.evaluate("!!document.querySelector('.sp-ov')")
        if has_ov:
            h0 = pg.evaluate("document.querySelector('.sp-ov').getBoundingClientRect().height"); pg.evaluate("document.querySelector('.sp-ov').click()"); pg.wait_for_timeout(100)
            rec(f"P6 [{size}] tapping a description opens it fully down", pg.evaluate("document.querySelector('.sp-row').classList.contains('full')") and pg.evaluate("document.querySelector('.sp-ov').getBoundingClientRect().height") >= h0)
        metas = pg.evaluate("[...document.querySelectorAll('.sp-row .sp-meta')].slice(0,3).map(m=>m.textContent)")
        rec(f"P9 [{size}] only my own rating shows (★ 9 on E2), no TMDB rating elsewhere", "\u2605 9" in metas[1] and "\u2605" not in metas[0] and "\u2605" not in metas[2], metas)
        rec(f"P10 [{size}] season chips stay on one row (scroll sideways)", pg.evaluate("getComputedStyle(document.querySelector('.sp-chips')||document.body).flexWrap") in ("nowrap",""))
        pg.evaluate("document.querySelectorAll('.sp-row')[2].querySelector('.sp-pic .more').click()"); pg.wait_for_timeout(100)
        rec(f"P11 [{size}] ⋯ on the picture opens ✓ for an unwatched episode", pg.evaluate("document.querySelector('.sp-pic .ic.open .opts button').title") == "Mark watched")
        pg.evaluate("document.querySelector('.sp-pic .ic.open .opts button').click()"); pg.wait_for_timeout(250)
        rec(f"P12 [{size}] ✓ marks it: badge shows, header count goes up, toast says so", pg.evaluate("!!document.querySelectorAll('.sp-row')[2].querySelector('.sp-wk')") and f"3/{n1} watched" in pg.evaluate("document.querySelector('.sp-top small').textContent") and "E3 marked watched" in pg.evaluate("document.getElementById('toast').textContent"))
        pg.evaluate("document.querySelectorAll('.sp-row')[2].querySelector('.sp-pic .more').click()"); pg.wait_for_timeout(100)
        rec(f"P13 [{size}] on a watched episode the button is ✕ Mark not watched", pg.evaluate("document.querySelector('.sp-pic .ic.open .opts button').title") == "Mark not watched")
        pg.evaluate("document.querySelector('.sp-pic .ic.open .opts button').click()"); pg.wait_for_timeout(250)
        rec(f"P14 [{size}] ✕ unmarks it again", not pg.evaluate("!!document.querySelectorAll('.sp-row')[2].querySelector('.sp-wk')"))
        pg.evaluate("document.querySelector('.sp-bk').click()"); pg.wait_for_timeout(300)
        rec(f"P7 [{size}] ‹ goes back to Discover", not pg.evaluate("!!document.querySelector('.serp')") and pg.evaluate("document.querySelectorAll('#grid .card').length") > 0)
        rec(f"P8 [{size}] no page errors", not errs, errs)
        if size == "phone":
            pg.evaluate("k=>document.querySelector('#grid .card[data-key=\"'+k+'\"] a.poster').click()", ms["key"]); pg.wait_for_timeout(600); pg.screenshot(path="/tmp/serp.png")
        pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
