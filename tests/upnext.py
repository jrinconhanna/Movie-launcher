# Fast area test (17 Nov): "Up next" pin on a channel (staging)
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
F = "f:Steve Jobs/1976-1984 (Apple I & Mac)"
def btn(pg, label): return pg.evaluate("l=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim().startsWith(l))?.click()", label)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for size, vp in [("desktop", {"width": 1280, "height": 900}), ("phone", {"width": 390, "height": 844})]:
        pg = b.new_page(viewport=vp); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/api.trakt.tv/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{P}/index.html?staging"); pg.wait_for_selector("#grid, .p2list", timeout=8000)
        pg.evaluate("f=>{const d=JSON.parse(localStorage.getItem('proto2')); d.lists.Playlists=[f].concat(d.lists.Playlists.filter(x=>x!==f)); localStorage.setItem('proto2', JSON.stringify(d));}", F)
        pg.reload(); pg.wait_for_timeout(600)
        def chan_next(): return pg.evaluate("f=>{const r=[...document.querySelectorAll('.nowc, .p2list > *')].find(e=>e.textContent.includes('1976-1984')); return r ? r.querySelector('b')?.textContent : null}", F)
        first = chan_next()
        # open the folder from Next › Playlists
        btn(pg, "Next"); pg.wait_for_timeout(150); btn(pg, "Playlists"); pg.wait_for_timeout(150)
        r = pg.evaluate("(()=>{const e=[...document.querySelectorAll('.gr')].map(g=>g.parentElement).find(d=>d.textContent.includes('1976-1984')); const b=e.getBoundingClientRect(); return [b.x+b.width/2,b.y+b.height/2]})()")
        pg.mouse.click(r[0], r[1], button="right"); pg.wait_for_timeout(150)
        pg.evaluate("[...document.querySelectorAll('#p2menu button')].find(b=>b.textContent==='↗ Open folder').click()"); pg.wait_for_timeout(300)
        n_up = pg.evaluate("document.querySelectorAll('#grid .lcard:not(.seen) .opts button[aria-label=\"Up next\"]').length")
        rec(f"U1 [{size}] unwatched videos in a channel's folder offer Up next", n_up > 1, n_up)
        title = pg.evaluate("(()=>{const c=[...document.querySelectorAll('#grid .lcard:not(.seen)')].filter(c=>c.querySelector('.opts button[aria-label=\"Up next\"]'))[2]; c.querySelector('.opts button[aria-label=\"Up next\"]').click(); return c.querySelector('.poster').getAttribute('aria-label')})()")
        pg.wait_for_timeout(300)
        rec(f"U2 [{size}] the picked video is tagged Up next and no longer offers it", pg.evaluate("t=>{const c=[...document.querySelectorAll('#grid .lcard')].find(c=>c.querySelector('.poster').getAttribute('aria-label')===t); return c.querySelector('.where')?.textContent==='Up next' && !c.querySelector('.opts button[aria-label=\"Up next\"]')}", title), title)
        rec(f"U3 [{size}] nothing was marked watched", pg.evaluate("JSON.parse(localStorage.getItem('learndone')||'[]').length") == 0)
        btn(pg, "Watching"); pg.wait_for_timeout(300)
        rec(f"U4 [{size}] on Watching the channel's next video is the picked one", chan_next() == title, (first, chan_next(), title))
        # watch it: mark watched in Discover, then the channel falls back to the first unwatched
        btn(pg, "Discover"); pg.wait_for_timeout(200)
        pg.evaluate("t=>[...document.querySelectorAll('#grid .lcard')].find(c=>c.querySelector('.poster').getAttribute('aria-label')===t).querySelector('.opts button[aria-label=\"Mark watched\"]').click()", title); pg.wait_for_timeout(300)
        btn(pg, "Watching"); pg.wait_for_timeout(300)
        rec(f"U5 [{size}] once it's watched, the channel goes back to the first unwatched", chan_next() == first and first != title, (chan_next(), first))
        rec(f"U6 [{size}] pin cleared and synced state carries pins", pg.evaluate("f=>!(JSON.parse(localStorage.getItem('proto2')).pin||{})[f]", F))
        # U8-U10: a watched video can be pinned (re-watch); ✓ on the channel row clears it
        btn(pg, "Discover"); pg.wait_for_timeout(200)
        pg.evaluate("(()=>{const w=document.getElementById('wf'); w.value=[...w.options].find(o=>/all/i.test(o.value)||/all/i.test(o.text)).value; w.dispatchEvent(new Event('change'))})()"); pg.wait_for_timeout(250)
        rec(f"U8 [{size}] a watched video offers Up next too", pg.evaluate("t=>!![...document.querySelectorAll('#grid .lcard')].find(c=>c.querySelector('.poster').getAttribute('aria-label')===t).querySelector('.opts button[aria-label=\"Up next\"]')", title))
        pg.evaluate("t=>[...document.querySelectorAll('#grid .lcard')].find(c=>c.querySelector('.poster').getAttribute('aria-label')===t).querySelector('.opts button[aria-label=\"Up next\"]').click()", title); pg.wait_for_timeout(250)
        btn(pg, "Watching"); pg.wait_for_timeout(300)
        rec(f"U9 [{size}] the watched video becomes the channel's next one", chan_next() == title, (chan_next(), title))
        r = pg.evaluate("(()=>{const e=[...document.querySelectorAll('.nowc, .p2list > *')].find(e=>e.textContent.includes('1976-1984')); const b=e.getBoundingClientRect(); return [b.x+b.width*0.7,b.y+b.height/2]})()")
        pg.mouse.click(r[0], r[1], button="right"); pg.wait_for_timeout(200)
        pg.evaluate("[...document.querySelectorAll('#p2menu button')].find(b=>b.textContent.startsWith('✓ Watched this video')).click()"); pg.wait_for_timeout(300)
        rec(f"U10 [{size}] ✓ Watched this video on the channel clears the pin; back to the first unwatched", chan_next() == first and not pg.evaluate("f=>(JSON.parse(localStorage.getItem('proto2')).pin||{})[f]", F), (chan_next(), first))
        rec(f"U7 [{size}] no page errors", not errs, errs); pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
