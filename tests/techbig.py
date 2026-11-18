# Fast area test (18 Nov): Tech folders in the series-page style (staging)
import http.server, socketserver, threading, os, time
from playwright.sync_api import sync_playwright
T0 = time.time(); ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); P = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
R = []
def rec(n, ok, d=""): R.append(ok); print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  " + str(d)))
def btn(pg, l): pg.evaluate("l=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim().startsWith(l))?.click()", l)
import json
DESC = json.load(open(os.path.join(ROOT, "data/descriptions.json")))
def addov(r):  # same merge build.py does, so the test needn't wait for the build
    j = json.load(open(os.path.join(ROOT, "library.json")))
    for x in j.get("learn", []):
        if x.get("id") in DESC: x["ov"] = DESC[x["id"]]
    r.fulfill(status=200, content_type="application/json", body=json.dumps(j))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for WANT in ["Steve Jobs", "Reforge"]:
     for size, vp in [("desktop", {"width": 1280, "height": 900}), ("phone", {"width": 390, "height": 844})]:
         for q in ["?staging", ""]:
             pg = b.new_page(viewport=vp); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.route("**/api.trakt.tv/**", lambda r: r.abort()); pg.route("**/library.json*", addov)
             pg.goto(f"http://127.0.0.1:{P}/index.html{q}"); pg.wait_for_timeout(900)
             btn(pg, "Discover"); pg.wait_for_timeout(200); pg.evaluate("[...document.querySelectorAll('#tabs button')].find(b=>b.firstChild.textContent==='Tech').click()"); pg.wait_for_timeout(200)
             for _ in range(4):
                 if pg.evaluate("document.querySelectorAll('#grid .lcard:not(.ccard)').length"): break
                 pg.evaluate("w=>[...document.querySelectorAll('#grid .ccard .poster')].find(x=>x.closest('.ccard').textContent.includes(w))?.click() || document.querySelector('#grid .ccard .poster')?.click()", WANT); pg.wait_for_timeout(300)
             if q:
                 rec(f"T1 [{size}] staging: videos inside a folder are one big column", pg.evaluate("document.getElementById('grid').classList.contains('tbig') && getComputedStyle(document.getElementById('grid')).gridTemplateColumns.split(' ').length===1"))
                 rec(f"T2 [{size}] staging: number chip leads the title", pg.evaluate("!!document.querySelector('#grid .lcard .t .sp-en')"))
                 rec(f"T3 [{size}] staging: date sits on the picture bottom-right", pg.evaluate("(()=>{const d=document.querySelector('#grid .lcard .poster .sp-inf'); if(!d) return !document.querySelector('#grid .lcard .y')||[...document.querySelectorAll('#grid .lcard .y')].every(y=>!/\\d{4}/.test(y.textContent)); const p=d.closest('.poster').getBoundingClientRect(); return Math.abs(d.getBoundingClientRect().right-(p.right-8))<2})()"))
                 if pg.evaluate("!document.getElementById('wkrow').hidden"):
                    pg.evaluate("window.scrollTo(0, 800)"); pg.wait_for_timeout(100)
                    rec(f"T8 [{size}] staging: a gap of ~10px between the chips and the top bar's edge", pg.evaluate("(()=>{const h=document.querySelector('header').getBoundingClientRect(), c=document.querySelector('#wkrow button').getBoundingClientRect(); return h.bottom - c.bottom >= 9})()"), pg.evaluate("(()=>{const h=document.querySelector('header').getBoundingClientRect(), c=document.querySelector('#wkrow button').getBoundingClientRect(); return h.bottom - c.bottom})()"))
                    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(100)
                    rec(f"T7 [{size}] staging: week chips are small outlined chips on one row", pg.evaluate("(()=>{const r=document.getElementById('wkrow'), b=r.querySelector('button'); return getComputedStyle(r).flexWrap==='nowrap' && getComputedStyle(b).borderRadius==='8px'})()"))
                 if WANT == "Steve Jobs":
                    o = pg.evaluate("(()=>{const e=document.querySelector('#grid .lcard .sp-ov'); if(!e) return null; const fits=e.scrollHeight<=e.clientHeight+1, h1=e.getBoundingClientRect().height, lh=parseFloat(getComputedStyle(e).lineHeight)||17; e.click(); const h2=e.getBoundingClientRect().height; return {n:document.querySelectorAll('#grid .lcard .sp-ov').length, two:h1<=lh*2+2, opens:fits||h2>h1, grid:document.getElementById('grid').classList.contains('tbig')}})()")
                    rec(f"T9 [{size}] staging: 1976-1984 videos show a 2-line description that opens on tap", bool(o) and o["n"]==6 and o["two"] and o["opens"], o)
                 pg.evaluate("window.scrollTo(0, 1500)"); pg.wait_for_timeout(150)
                 rec(f"T4 [{size}] staging: back chip row stays on top while scrolling", pg.evaluate("(()=>{const c=document.getElementById('crow').getBoundingClientRect(); return window.scrollY>300 && c.top>=0 && c.bottom<220})()"))
             else:
                 rec(f"T5 [{size}] live: big rows too (V2.4.2 live)", pg.evaluate("document.getElementById('grid').classList.contains('tbig')"))
             rec(f"T6 [{size}] no page errors ({q or 'live'})", not errs, errs)
             if q and size == "phone" and WANT=="Steve Jobs": pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(100); pg.screenshot(path="/tmp/tbig.png",clip={"x":0,"y":0,"width":390,"height":420})
             pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
