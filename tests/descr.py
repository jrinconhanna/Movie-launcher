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
  d.lists.Tech=[]; d.lists.Playlists=d.lists.Playlists.filter(x=>x!=='f:TOC/GSP Series'); d.lists.Playlists.splice(0,0,'f:TOC/GSP Series'); put('Playlists',s); put('Series',t); put('Movies',m); localStorage.setItem('proto2', JSON.stringify(d)); localStorage.removeItem('lastplay');}"""
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
        btn(pg, "Movies"); pg.wait_for_timeout(150)
        ar = row('.p2list .p2n', 'Antitrust'); pg.evaluate(f"{ar}.querySelector('.tdsc') || {ar}.querySelector('.nm').click()"); pg.wait_for_timeout(300)
        rec(f"D15 [{size}] Next: every row's picture is top-aligned with its title, open or closed", pg.evaluate("[...document.querySelectorAll('.p2list .p2n')].every(r=>Math.abs(r.querySelector('.th').getBoundingClientRect().top-r.querySelector('.nm').getBoundingClientRect().top)<8)") and pg.evaluate(f"!!{ar}.querySelector('.tdsc')"))
        pg.screenshot(path=f"/tmp/descr-top-{size}.png")
        pg.evaluate(f"{ar}.querySelector('.th').click()"); pg.wait_for_timeout(150)
        rec(f"D10 [{size}] Next: tapping the picture still opens the menu", pg.evaluate("!!document.getElementById('p2menu')"))
        # no description: a short toast, nothing else happens
        pg.evaluate("document.getElementById('p2menu')?.remove()"); btn(pg, "Playlists"); pg.wait_for_timeout(150); gr = row(".p2list .p2n", "GSP")
        pg.evaluate(f"{gr}.querySelector('.nm').click()"); pg.wait_for_timeout(200)
        rec(f"D13 [{size}] Next: a title with no description shows 'No description yet', no menu, no text", pg.evaluate("(()=>{const t=document.getElementById('toast'); return !t.hidden && t.textContent.startsWith('No description yet')})()") and pg.evaluate("!document.getElementById('p2menu')") and pg.evaluate(f"!{gr}.querySelector('.tdsc')"))
        btn(pg, "Watching"); pg.wait_for_timeout(250); jr = row(".p2list .p2r", "Japanology"); p0 = pg.evaluate("window.__plays")
        has = pg.evaluate(f"!!{jr}")
        if has:
            pg.evaluate(f"{jr}.querySelector('.t').click()"); pg.wait_for_timeout(400)
        rec(f"D14 [{size}] Watching: an episode with no TMDB text shows the toast and doesn't play", has and pg.evaluate("document.getElementById('toast').textContent.startsWith('No description yet')") and pg.evaluate("window.__plays") == p0 and pg.evaluate(f"!{jr}.querySelector('.tdsc')"), has)
        btn(pg, "Next"); pg.wait_for_timeout(150); btn(pg, "Series"); pg.wait_for_timeout(150); sr = row(".p2list .p2n", "Star Trek")
        rec(f"D16 [{size}] Next › Series: episode name first, then the series", pg.evaluate(f"(()=>{{const r={sr}; return r.querySelector('.nm').textContent.startsWith('Phantasms') && r.querySelector('.sn').textContent==='Star Trek: The Next Generation'}})()"), pg.evaluate(f"{sr}.querySelector('.nm').textContent"))
        btn(pg, "Playlists"); pg.wait_for_timeout(150); fr = row(".p2list .p2n", "2000-2004")
        rec(f"D17 [{size}] Next › Playlists: next video first, then the folder", pg.evaluate(f"(()=>{{const r={fr}; return r.querySelector('.nm').textContent.startsWith('Macworld') && r.querySelector('.sn').textContent.includes('2000-2004')}})()"), pg.evaluate(f"{fr}.querySelector('.nm').textContent"))
        btn(pg, "Series"); pg.wait_for_timeout(150)
        sep = pg.evaluate("""(()=>{const w=document.querySelector('.p2list'); const kids=[...w.children]; const i=kids.findIndex(e=>e.classList.contains('p2sep')); if(i<0) return null; return {txt:kids[i].textContent, before:kids[i-1].classList.contains('live'), after:!kids[i+1].classList.contains('live'), n:w.querySelectorAll('.p2sep').length}})()""")
        rec(f"D18 [{size}] Next: one WAITING separator between the On Watching rows and the rest", bool(sep) and sep['txt'] == 'Waiting' and sep['before'] and sep['after'] and sep['n'] == 1, sep)
        ow = pg.evaluate("""(()=>{const r=document.querySelector('.p2list .p2n.live'), o=document.querySelectorAll('.p2list .p2n:not(.live)')[0]; const st=r.querySelector('.st'); return {starts:!st.textContent.startsWith('●'), tag:st.querySelector('.ow')?.textContent, x:Math.abs(st.getBoundingClientRect().left-o.querySelector('.st').getBoundingClientRect().left)}})()""")
        rec(f"D19 [{size}] Next: On Watching rows keep the count first, tag to its right", ow['starts'] and ow['tag'] == '● On Watching' and ow['x'] < 2, ow)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(250)
        stk = pg.evaluate("""(()=>{const c=document.querySelector('.p2chips'), r=c.getBoundingClientRect(), h=document.querySelector('header'), hb=h?Math.max(0,h.getBoundingClientRect().bottom):0; const b=[...c.querySelectorAll('button')].find(x=>x.textContent.startsWith('Series')); const br=b.getBoundingClientRect(); const hit=document.elementFromPoint(br.x+br.width/2, br.y+br.height/2); return {sy:scrollY, top:r.top, hb:hb, hit:!!hit && b.contains(hit)}})()""")
        rec(f"D20 [{size}] Next: chips stay at the top after scrolling down, and tappable", stk['sy'] > 100 and abs(stk['top'] - stk['hb']) < 12 and stk['hit'], stk)
        pg.screenshot(path=f"/tmp/descr-{size}.png")
        rec(f"D11 [{size}] no page errors", not errs, errs); pg.close()
    # live (no ?staging): unchanged
    pg = b.new_page(viewport={"width": 390, "height": 844}); pg.route("**/api.trakt.tv/**", lambda r: r.abort())
    pg.goto(f"http://127.0.0.1:{P}/index.html"); pg.wait_for_selector("#grid, .p2list", timeout=8000); pg.wait_for_timeout(500)
    rec("D12 [live] no tappable titles until the go", pg.evaluate("document.querySelectorAll('.dtap').length") == 0); pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
