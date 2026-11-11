"""Build library.json for the launcher.

Reads data/library.txt (one file path per line, as listed on Whatbox),
groups files into titles, matches each title to TMDB (cached in
data/matches.json, overridable in data/overrides.json), reads watched
status from Trakt, and writes library.json at the repo root.

Needs env vars TMDB_TOKEN (API Read Access Token) and TRAKT_CLIENT_ID.
"""
import datetime
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TRAKT_USER = os.environ.get("TRAKT_USER", "javierrincon")
VIDEO = (".mp4", ".mkv", ".avi", ".m4v", ".mov")
CAT_RE = re.compile(r"^\d+-\s*")
EP_RE = re.compile(r"S(\d{1,2})E(\d{1,3})|(?<!\d)(\d{1,2})x(\d{2,3})(?!\d)", re.I)


def load(name, default):
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return default


def save(name, obj, root=False):
    p = os.path.join(ROOT if root else DATA, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def cat_num(s):
    m = re.match(r"^(\d+)-", s)
    return f"{int(m.group(1)):03d}" if m else "999"


def clean_cat(s):
    return CAT_RE.sub("", s).replace(":", " / ").strip()


def title_year(name):
    """'Back to the future (1985).mp4' -> ('Back to the future', 1985)."""
    base = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", name)
    base = re.sub(r"^[^\w(]+", "", base).replace("_", " ").strip()
    m = re.match(r"^(.*?)[\s(\-]*((?:19|20)\d{2})\)?\s*$", base)
    if m and m.group(1).strip():
        return m.group(1).strip(" -"), int(m.group(2))
    m = re.match(r"^(.*?)\s*\(((?:19|20)\d{2})\)", base)
    if m:
        return m.group(1).strip(" -"), int(m.group(2))
    return base.strip(" -"), None


def episode(name):
    m = EP_RE.search(name)
    if not m:
        return None
    s, e = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    return int(s), int(e)


def group_items(lines):
    """Return dict key -> item skeleton."""
    items = {}

    def add(key, **kw):
        it = items.setdefault(key, dict(key=key, files=0, eps=set(), **kw))
        return it

    for raw in lines:
        path = raw.strip()
        if not path.lower().endswith(VIDEO):
            continue
        parts = path.lstrip("./").split("/")
        fname = parts[-1]
        if parts[:2] == ["z- Other", "1- Movies"] and len(parts) >= 4:
            cat = clean_cat(parts[2])
            t, y = title_year(fname)
            it = add("movie|" + "/".join(parts[2:]), group="Movies", category=cat,
                     order=cat_num(parts[2]), name=t, year=y, prefer="movie")
        elif parts[:2] == ["z- Other", "2- TV Series"] and len(parts) >= 4:
            show = parts[2]
            if show.lower().startswith("z-"):
                continue
            t, y = title_year(show)
            it = add("tv|" + show, group="Series", category="TV series",
                     order="000", name=t, year=y, prefer="tv")
        elif parts[0] == "2- Docu-series" and len(parts) >= 3:
            rest, cat, order = parts[1:], "Docs", []
            while len(rest) > 1 and CAT_RE.match(rest[0]):
                cat = clean_cat(rest[0])
                order.append(cat_num(rest[0]))
                rest = rest[1:]
            if len(rest) == 1:
                t, y = title_year(rest[0])
                key, prefer = "doc|" + "/".join(parts[1:]), "movie"
            elif rest[0].startswith("(") or rest[0].lower().startswith("z-"):
                if len(rest) >= 3 and not rest[1].startswith("("):
                    t, y = title_year(rest[1])
                    key, prefer = "doc|" + "/".join(parts[1:-1]), "tv"
                else:
                    t, y = title_year(rest[-1])
                    key, prefer = "doc|" + "/".join(parts[1:]), "movie"
            else:
                t, y = title_year(rest[0])
                idx = parts.index(rest[0])
                key, prefer = "doc|" + "/".join(parts[1:idx + 1]), "tv"
            it = add(key, group="Docs", category=cat, order=".".join(order) or "999",
                     name=t, year=y, prefer=prefer)
        else:
            continue  # talks (1- Tech) and anything else: not in the MVP
        it["files"] += 1
        ep = episode(fname)
        if ep:
            it["eps"].add(ep)
    return items


LEARN_DIRS = [("1- Tech/2- TOC/1- GSP Series", "GSP Series")]  # V2.3: start with the TOC GSP course only
LEARN_NUM_RE = re.compile(r"^(\d+)[.)\-]\s*")


def learn_items(lines):
    """Other videos for the Learn section: one entry per file, in course order (V2.3)."""
    out = []
    for raw in lines:
        path = raw.strip().lstrip("./")
        if not path.lower().endswith(VIDEO):
            continue
        for folder, course in LEARN_DIRS:
            if path.startswith(folder + "/") and "/" not in path[len(folder) + 1:]:
                fname = path.rsplit("/", 1)[1]
                base = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", fname)
                base = re.sub(r"^[^\w(]+", "", base).strip()  # drops marks like the green tick
                m = LEARN_NUM_RE.match(base)
                n = int(m.group(1)) if m else None
                title = LEARN_NUM_RE.sub("", base).strip() if m else base
                item = {"key": "learn|" + path, "course": course, "n": n, "title": title, "file": fname}
                parts = folder.split("/")
                if len(parts) >= 2:  # e.g. "2- TOC" → category TOC, order 2
                    cm = re.match(r"^(\d+)[-.)]\s*(.*)$", parts[-2])
                    item["category"] = cm.group(2) if cm else parts[-2]
                    item["corder"] = cm.group(1).zfill(3) if cm else ""
                cover = "covers/learn/%s/%s.jpg" % (re.sub(r"[^a-z0-9]+", "-", course.lower()).strip("-"), n)
                if n is not None and os.path.exists(os.path.join(ROOT, cover)):
                    item["cover"] = cover  # V2.3: added by hand; Better: synced from Whatbox
                folder_cover = os.path.dirname(cover) + "/folder.jpg"
                if os.path.exists(os.path.join(ROOT, folder_cover)):
                    item["folder"] = folder_cover
                out.append(item)
    try:
        meta = json.load(open(os.path.join(DATA, "courses.json"), encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    for item in out:
        if meta.get(item["course"], {}).get("year"):
            item["year"] = meta[item["course"]]["year"]  # course facts kept by hand in data/courses.json
    out.sort(key=lambda x: (x["course"], x["n"] is None, x["n"] or 0, x["title"].lower()))
    return out


def tmdb_get(path, params, token):
    url = "https://api.themoviedb.org/3" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token,
                                               "accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + attempt * 2)
                continue
            raise
    return {}


def tmdb_match(it, token):
    order = ["movie", "tv"] if it["prefer"] == "movie" else ["tv", "movie"]
    for kind in order:
        params = {"query": it["name"], "include_adult": "false"}
        if it["year"]:
            params["year" if kind == "movie" else "first_air_date_year"] = it["year"]
        res = tmdb_get("/search/" + kind, params, token).get("results") or []
        if not res and it["year"]:
            params.pop("year", None); params.pop("first_air_date_year", None)
            res = tmdb_get("/search/" + kind, params, token).get("results") or []
        time.sleep(0.05)
        if res:
            r = res[0]
            return {"kind": kind, "tmdb": r["id"],
                    "title": r.get("title") or r.get("name"),
                    "date": r.get("release_date") or r.get("first_air_date") or "",
                    "poster": r.get("poster_path"),
                    "overview": (r.get("overview") or "")[:400]}
        if it["group"] == "Series":
            break  # TV series folders are never movies
    return None


PREFIX_RE = re.compile(r"^(G4|PBS|BBC|HM|K&G|NFL|NBA|ESPN|HBO|CNN|SI)\b[\s:-]*", re.I)
NOISE_RE = re.compile(r"\[[^\]]*\]|\([^)]*\)|\b(all parts|full|\d+ hour|documentary|doc|vose|subtitulado.*|op-doc)\b|[^\w\s'&.,!-]", re.I)


def clean_variants(name):
    """Looser search strings for a title the exact search missed."""
    base = re.sub(r"\s+", " ", NOISE_RE.sub(" ", name)).strip(" -")
    out = [base, PREFIX_RE.sub("", base).strip()]
    if " - " in base:
        a, b = base.split(" - ", 1)
        out += [a.strip(), b.strip()]
    seen, res = set(), []
    for v in out:
        if len(v) >= 3 and v.lower() not in seen:
            seen.add(v.lower()); res.append(v)
    return res


def suggest(it, token):
    """Best loose TMDB candidate for an unmatched title, with a similarity score. Never applied automatically."""
    from difflib import SequenceMatcher
    best, vs = None, clean_variants(it["name"])
    ref = PREFIX_RE.sub("", vs[0]).strip().lower() if vs else it["name"].lower()
    for q in vs:
        for kind in ("movie", "tv"):
            for r in (tmdb_get("/search/" + kind, {"query": q, "include_adult": "false"}, token).get("results") or [])[:3]:
                title = r.get("title") or r.get("name") or ""
                score = SequenceMatcher(None, ref, title.lower()).ratio()  # whole name, not the fragment searched
                date = r.get("release_date") or r.get("first_air_date") or ""
                if it["year"] and date[:4] == str(it["year"]):
                    score += 0.15
                if not best or score > best["score"]:
                    best = {"kind": kind, "tmdb": r["id"], "title": title, "date": date, "score": round(min(score, 1), 2)}
            time.sleep(0.05)
    return best


def trakt_get(path, client_id):
    """GET a Trakt list, following pagination (Trakt caps pages at 100 items)."""
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        req = urllib.request.Request(f"https://api.trakt.tv{path}{sep}page={page}&limit=100", headers={
            "Content-Type": "application/json", "trakt-api-version": "2",
            "trakt-api-key": client_id, "User-Agent": "movie-launcher/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
            pages = int(r.headers.get("X-Pagination-Page-Count") or 1)
        out.extend(data)
        if page >= pages or not data:
            return out
        page += 1
        time.sleep(0.3)


def main():
    token, client = os.environ.get("TMDB_TOKEN"), os.environ.get("TRAKT_CLIENT_ID")
    if not token:
        sys.exit("TMDB_TOKEN is not set")
    with open(os.path.join(DATA, "library.txt"), encoding="utf-8") as f:
        lines = f.readlines()
    items = group_items(lines)
    learn = learn_items(lines)
    tf = os.path.join(DATA, "tech-files.txt")
    if os.path.exists(tf):  # V2.4: real list from Whatbox (tech_sync.py); shown behind ?v24 for now
        from tech import tech_items
        for it in tech_items(open(tf, encoding="utf-8").readlines()):
            it.pop("src_cover", None); it.pop("src_folder", None); it.pop("src_fcov", None); it.pop("src_frame", None); it.pop("frame_at", None)
            if it.get("frame") and not os.path.exists(os.path.join(ROOT, it["frame"])): it.pop("frame")
            it["fcov"] = [c if c and os.path.exists(os.path.join(ROOT, c)) else None for c in it.get("fcov", [])]
            if it.get("cover") and not os.path.exists(os.path.join(ROOT, it["cover"])): it.pop("cover")
            if it.get("folder") and not os.path.exists(os.path.join(ROOT, it["folder"])): it.pop("folder")
            learn.append(it)
        newc = {x["course"] for x in learn if x.get("v24")}
        for x in learn:  # V2.3 course now read from Whatbox (GSP Series): the old entry only shows in ?v23
            if not x.get("v24") and x["course"] in newc: x["old"] = True
        learn.sort(key=lambda x: (x.get("corder", ""), x.get("cord", "")))  # stable: keeps each course's own order
    cache, overrides = load("matches.json", {}), load("overrides.json", {})
    videos = set(load("videos.json", []))  # unmatched keys that are videos, not TMDB titles
    # overrides only need {"kind": "movie"|"tv", "tmdb": id}; fill in title, poster etc. from TMDB
    for key, ov in overrides.items():
        if ov and "title" not in ov:
            r = tmdb_get(f"/{ov['kind']}/{ov['tmdb']}", {}, token)
            ov.update({"title": r.get("title") or r.get("name") or key,
                       "date": r.get("release_date") or r.get("first_air_date") or "",
                       "poster": r.get("poster_path"), "overview": (r.get("overview") or "")[:400]})

    looked_up = 0
    for key, it in items.items():
        if key in overrides:
            continue
        if key not in cache or cache[key] is None and it.get("retry"):
            cache[key] = tmdb_match(it, token)
            looked_up += 1
    # forget cached matches for files that are gone
    cache = {k: v for k, v in cache.items() if k in items}
    save("matches.json", cache)
    print(f"{len(items)} titles, {looked_up} looked up on TMDB")

    watched_movies, watched_eps, watched_shows = set(), {}, set()
    if client:
        try:
            for m in trakt_get(f"/users/{TRAKT_USER}/watched/movies", client):
                tid = (m.get("movie") or {}).get("ids", {}).get("tmdb")
                if tid:
                    watched_movies.add(tid)
            for s in trakt_get(f"/users/{TRAKT_USER}/watched/shows", client):
                tid = (s.get("show") or {}).get("ids", {}).get("tmdb")
                if not tid:
                    continue
                watched_shows.add(tid)
                watched_eps[tid] = {(se["number"], ep["number"])
                                    for se in s.get("seasons", []) for ep in se.get("episodes", [])}
            for h in trakt_get(f"/users/{TRAKT_USER}/history/movies", client):
                tid = (h.get("movie") or {}).get("ids", {}).get("tmdb")
                if tid:
                    watched_movies.add(tid)
            for h in trakt_get(f"/users/{TRAKT_USER}/history/episodes", client):
                tid = (h.get("show") or {}).get("ids", {}).get("tmdb")
                ep = h.get("episode") or {}
                if tid and ep.get("season") is not None:
                    watched_shows.add(tid)
                    watched_eps.setdefault(tid, set()).add((ep["season"], ep["number"]))
            print(f"Trakt: {len(watched_movies)} films, {len(watched_shows)} shows, "
                  f"{sum(len(v) for v in watched_eps.values())} episodes watched")
        except Exception as e:  # keep building without watched status
            print("Trakt failed:", e)

    epc = load("epcounts.json", {})
    def ep_total(tid):
        c = epc.get(str(tid))
        if c and c.get("at", "") > (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat():
            return c["n"]
        try:
            r = tmdb_get(f"/tv/{tid}", {}, token)
            n = sum(s.get("episode_count", 0) for s in r.get("seasons", []) if s.get("season_number", 0) > 0)
            epc[str(tid)] = {"n": n, "at": datetime.datetime.utcnow().isoformat()}
            return n
        except Exception as e:
            print("TMDB episode count failed:", tid, e)
            return c["n"] if c else None

    out, unmatched = [], []
    sugg = load("suggestions.json", {})  # cached loose-search candidates, checked by hand before use
    for key, it in sorted(items.items()):
        m = overrides.get(key, cache.get(key))
        if not m:
            if key not in sugg:
                sugg[key] = suggest(it, token)
            s = sugg[key] if sugg[key] and sugg[key]["score"] >= 0.75 else None
            unmatched.append({"key": key, "group": it["group"], "category": it["category"],
                              "name": it["name"], "year": it["year"], "video": key in videos and not s,
                              "suggest": s})
            continue
        status, prog = "unwatched", None
        if m["kind"] == "movie":
            if m["tmdb"] in watched_movies:
                status = "watched"
        else:
            seen = watched_eps.get(m["tmdb"], set())
            if it["eps"]:
                done = len(it["eps"] & seen)
                prog = [done, len(it["eps"])]
                status = "watched" if done == len(it["eps"]) else ("progress" if done else "unwatched")
            elif m["tmdb"] in watched_shows:
                # no episode files listed: compare with TMDB's episode count (specials left out)
                total = ep_total(m["tmdb"])
                done = len({e for e in seen if e[0] > 0})
                if total:
                    prog = [min(done, total), total]
                    status = "watched" if done >= total else "progress"
                else:
                    status = "progress"
        out.append({"key": key, "group": it["group"], "category": it["category"], "order": it["order"],
                    "kind": m["kind"], "tmdb": m["tmdb"], "title": m["title"],
                    "date": m["date"], "poster": m["poster"], "overview": m["overview"],
                    "status": status, "progress": prog, "files": it["files"]})

    save("epcounts.json", epc)
    save("suggestions.json", {k: v for k, v in sugg.items() if k in items})
    save("library.json", {"updated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
                          "items": out, "unmatched": unmatched, "learn": learn}, root=True)
    print(f"{len(out)} matched, {len(unmatched)} unmatched, {len(learn)} learn videos")


if __name__ == "__main__":
    main()
