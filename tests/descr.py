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
        sep = pg.evaluate("""(()=>{const w=document.querySelector('.p2list'); const kids=[...w.children]; const i=kids.findIndex(e=>e.classList.contains('p2sep')&&!e.classList.contains('nwtl')); if(i<0) return null; return {txt:kids[i].textContent, before:kids[i-1].classList.contains('live'), after:!kids[i+1].classList.contains('live'), n:w.querySelectorAll('.p2sep:not(.nwtl)').length}})()""")
        rec(f"D18 [{size}] Next: one WAITING separator between the On Watching rows and the rest", bool(sep) and sep['txt'] == 'Waiting' and sep['before'] and sep['after'] and sep['n'] == 1, sep)
        ow = pg.evaluate("""(()=>{const r=document.querySelector('.p2list .p2n.live'), o=document.querySelectorAll('.p2list .p2n:not(.live)')[0]; const st=r.querySelector('.st'); return {starts:!st.textContent.startsWith('●'), tag:st.querySelector('.ow')?.offsetParent?'shown':'hidden', hc:(()=>{const h=document.querySelector('.p2sep.nwtl');return h?getComputedStyle(h).color+'|'+getComputedStyle(h,'::before').content:''})(), x:Math.abs(st.getBoundingClientRect().left-o.querySelector('.st').getBoundingClientRect().left)}})()""")
        rec(f"D19 [{size}] Next: On Watching rows keep the count first, no per-row tag (staging 25 Nov), red ● On Watching heading", ow['starts'] and ow['tag'] == 'hidden' and ow['x'] < 2 and ow['hc'].startswith('rgb(214, 60, 60)') and '●' in ow['hc'], ow)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(250)
        stk = pg.evaluate("""(()=>{const c=document.querySelector('.p2chips'), r=c.getBoundingClientRect(), h=document.querySelector('header'), hb=h?Math.max(0,h.getBoundingClientRect().bottom):0; const b=[...c.querySelectorAll('button')].find(x=>x.textContent.startsWith('Series')); const br=b.getBoundingClientRect(); const hit=document.elementFromPoint(br.x+br.width/2, br.y+br.height/2); return {sy:scrollY, top:r.top, hb:hb, hit:!!hit && b.contains(hit)}})()""")
        rec(f"D20 [{size}] Next: chips stay at the top after scrolling down, and tappable", stk['sy'] > 100 and abs(stk['top'] - stk['hb']) < 12 and stk['hit'], stk)
        # D21 (staging 24 Nov, phone): Next's chips sit exactly like Discover's: same height at rest and stuck, same gap, run to the screen edge
        G = "s=>{const b=[...document.querySelectorAll(s)].filter(e=>e.offsetParent); const r=b.map(e=>e.getBoundingClientRect()); const c=b[0].parentElement.getBoundingClientRect(); return {top:Math.round(r[0].top), left:Math.round(r[0].left), gap:Math.round(r[1].left-r[0].right), edge:Math.round(c.right)}}"
        stuck = pg.evaluate(G, ".p2chips button") if size == "phone" else None
        if size == "phone":
          pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(150); rest = pg.evaluate(G, ".p2chips button")
          pg.evaluate("[...document.querySelectorAll('#top button')].find(b=>b.textContent.includes('Discover')).click()"); pg.wait_for_timeout(400); dsc = pg.evaluate(G, "#tabs button")
          W = vp["width"]
          rec(f"D21 [{size}] Next chips line up with Discover's (height at rest and stuck, gap, screen edge)", rest['top'] == dsc['top'] == stuck['top'] and rest['left'] == dsc['left'] and rest['gap'] == dsc['gap'] and rest['edge'] >= W - 1, {"next": rest, "stuck": stuck, "discover": dsc})
        # D22 (staging 25 Nov): section titles: 'Now watching' above the card on Watching (badge gone), 'On Watching' above the top rows on Next
        pg.evaluate("[...document.querySelectorAll('#top button')].find(b=>b.textContent.includes('Watching')).click()"); pg.wait_for_timeout(400)
        w = pg.evaluate("(()=>{const l=document.querySelector('.nowlbl.nwtl'), c=document.querySelector('.nowc'), b=c&&c.querySelector('.lb'); return {txt:l&&l.offsetParent?l.textContent:'', above:!!(l&&c)&&l.getBoundingClientRect().bottom<=c.getBoundingClientRect().top, badge:!!(b&&b.offsetParent)}})()")
        pg.evaluate("[...document.querySelectorAll('#top button')].find(b=>b.textContent.includes('Next')).click()"); pg.wait_for_timeout(400)
        n = pg.evaluate("(()=>{const h=document.querySelector('.p2sep.nwtl'), r=document.querySelector('.p2list .p2n.live'); return {txt:h&&h.offsetParent?h.textContent:'', above:!!(h&&r)&&h.getBoundingClientRect().bottom<=r.getBoundingClientRect().top, pill:!!document.getElementById('nwtpill')}})()")
        rec(f"D22 [{size}] titles: Now watching above the card (no badge), On Watching above Next's top rows, no mockup pill", w['txt']=='Now watching' and w['above'] and not w['badge'] and n['txt']=='On Watching' and n['above'] and not n['pill'], {"watching": w, "next": n})
        # D23 (staging 25 Nov): Watching + Next keep the same tight spacing on first open and after Discover (Tech's 'tbig' used to leak in)
        TOPS = "()=>{const g=document.getElementById('grid');const y0=g.getBoundingClientRect().top;return [...g.children].filter(e=>e.offsetParent).slice(0,4).map(e=>Math.round(e.getBoundingClientRect().top-y0))}"
        tab = lambda t: (pg.evaluate("t=>[...document.querySelectorAll('#top button')].find(b=>b.textContent.includes(t)).click()", t), pg.wait_for_timeout(400))
        pg.reload(); pg.wait_for_timeout(800); tab("Watching"); w1 = pg.evaluate(TOPS); tab("Next"); n1 = pg.evaluate(TOPS)
        tab("Discover"); pg.evaluate("document.getElementById('grid').classList.add('tbig')"); tab("Watching"); w2 = pg.evaluate(TOPS); tab("Discover"); pg.evaluate("document.getElementById('grid').classList.add('tbig')"); tab("Next"); n2 = pg.evaluate(TOPS)
        rec(f"D23 [{size}] Watching + Next spacing is the same on first open and after Discover", w1 == w2 and n1 == n2 and len(w1) > 2, {"watching": [w1, w2], "next": [n1, n2]})
        pg.screenshot(path=f"/tmp/descr-{size}.png")
        rec(f"D11 [{size}] no page errors", not errs, errs); pg.close()
    # live (no ?staging): same as staging since V2.4.2 went live (18 Nov)
    pg = b.new_page(viewport={"width": 390, "height": 844}); pg.route("**/api.trakt.tv/**", lambda r: r.abort())
    pg.goto(f"http://127.0.0.1:{P}/index.html"); pg.wait_for_selector("#grid, .p2list", timeout=8000); pg.wait_for_timeout(500)
    rec("D12 [live] titles are tappable (V2.4.2 live)", pg.evaluate("document.querySelectorAll('.dtap').length") > 0)
    pg.evaluate("[...document.querySelectorAll('#top button')].find(b=>b.textContent.includes('Watching')).click()"); pg.wait_for_timeout(400)
    lw = pg.evaluate("(()=>{const l=document.querySelector('.nowlbl.nwtl');return l&&l.offsetParent?getComputedStyle(l).color+'|'+l.textContent:''})()")
    pg.evaluate("[...document.querySelectorAll('#top button')].find(b=>b.textContent.includes('Next')).click()"); pg.wait_for_timeout(400)
    ln = pg.evaluate("(()=>{const h=document.querySelector('.p2sep.nwtl'), o=document.querySelector('.p2n .st .ow'), c=document.querySelectorAll('.p2chips button'); return {h:h&&h.offsetParent?h.textContent:'', tag:!!(o&&o.offsetParent), gap:Math.round(c[1].getBoundingClientRect().left-c[0].getBoundingClientRect().right), pill:!!document.getElementById('nwtpill'), grid:document.getElementById('grid').className}})()")
    rec("D24 [live] 25 Nov tweaks live: red Now watching / On Watching headings, no per-row tag, chips gap 6, tight spacing, no mockup pill", lw.startswith('rgb(214, 60, 60)|Now watching') and ln['h'] == 'On Watching' and not ln['tag'] and ln['gap'] == 6 and not ln['pill'] and 'p2g' in ln['grid'], {"watching": lw, "next": ln}); pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
