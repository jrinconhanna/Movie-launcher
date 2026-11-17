# Fast area test (17 Nov): "Series to check" in the To check fold (staging)
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
tv = [i for i in lib["items"] if i.get("kind") == "tv"]
tv[0]["epm"] = "0/47 episodes match TMDB"; tv[1]["epm"] = "ok"; body = json.dumps(lib)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for q, stg in [("?staging", True), ("", False)]:
        pg = b.new_page(viewport={"width": 390, "height": 844}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/api.trakt.tv/**", lambda r: r.abort()); pg.route("**/library.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=body))
        pg.goto(f"http://127.0.0.1:{P}/index.html{q}"); pg.wait_for_timeout(1200)
        txt = pg.evaluate("(document.querySelector('.tocheck')||{}).innerText||''")
        if stg:
            rec("C1 staging: To check counts the series", "1 series" in txt, txt[:120])
            pg.evaluate("document.querySelectorAll('.tocheck, .tocheck details').forEach(d=>d.open=true)"); pg.wait_for_timeout(150)
            t2 = pg.evaluate("document.querySelector('.tocheck').innerText")
            rec("C2 staging: the series is listed with its reason; matched ones aren't", (tv[0]["title"] + " — 0/47 episodes match TMDB") in t2 and (tv[1]["title"] + " —") not in t2, t2[:300])
        else:
            rec("C3 live: no series section yet", "series" not in txt.lower(), txt[:120])
        rec(f"C4 no page errors ({q or 'live'})", not errs, errs); pg.close()
    b.close()
print(f"{sum(R)}/{len(R)} passed · {time.time()-T0:.0f}s")
