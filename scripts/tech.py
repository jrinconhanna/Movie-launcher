"""V2.4: Tech videos from the real Whatbox file list (data/tech-files.txt).

One rule set per category folder. Piece 1: Steve Jobs.
Each item: key, id (stable mark id), course, cord, category, corder, n, title,
year, sub (year chip inside a folder), src_cover / src_folder (paths on Whatbox,
relative to 1- Tech), cover / folder (paths in this repo once synced), v24.
"""
import hashlib, json, os, re

VIDEO = (".mp4", ".mkv", ".m4v", ".mov", ".avi", ".webm", ".mpeg", ".mpg")
IMG = (".png", ".jpg", ".jpeg")
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
NUM = re.compile(r"^(\d+)\s*[.)\-]\s*")


def h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def clean(name):
    """'1) 1976-1984 (Apple I & Mac)' -> ('1976-1984 (Apple I & Mac)', '001')"""
    m = NUM.match(name)
    return (NUM.sub("", name).strip(), m.group(1).zfill(3)) if m else (name.strip(), "")


def split_date(base):
    """'1997-01-07 - Macworld (Return)' -> (1997, 1, 7, 'Macworld (Return)')."""
    s = base.strip()
    m = re.match(r"^(\d{4})(?!\d)", s)
    if not m:
        t = re.search(r"\s*\((\d{4})\)\s*$", s)  # 'Title (2015)'
        return (int(t.group(1)), None, None, s[:t.start()].strip()) if t else (None, None, None, s)
    y, mo, d, s = int(m.group(1)), None, None, s[4:]
    x = re.match(r"^\s*\((\d{1,2})-(\d{1,2})\)", s)            # 2002 (09-10)
    if x: mo, d, s = int(x.group(1)), int(x.group(2)), s[x.end():]
    else:
        x = re.match(r"^\s*\(-\d+\)", s)                         # 2009 (-7)
        if x: s = s[x.end():]
        else:
            x = re.match(r"^-(\d{1,2})(?:-(\d{1,2}))?(?=\D|$)", s)  # 1981-02-18, 2005-10, 1999-07-
            if x: mo, d, s = int(x.group(1)), int(x.group(2)) if x.group(2) else None, s[x.end():]
    x = re.match(r"^\s*-?\s*([A-Za-z]{3})[a-z]*\b\s*", s)        # 2010 Oct, 2010 - Sep
    if x and x.group(1).lower() in MON: mo, s = MON[x.group(1).lower()], s[x.end():]
    s = re.sub(r"^\s*-\s*", "", s).strip()
    return y, mo, d, s


def strip_junk(t):
    t = re.sub(r"\s*\(\d{3,4}p_[^)]*\)", "", t)  # (360p_24fps_H264-128kbit_AAC)
    return t.strip()


EVENT_MONTH = [("macworld tokyo", 2), ("macworld ny", 7), ("macworld boston", 8), ("macworld", 1), ("wwdc", 6), ("apple expo", 9)]
_DATES = None


def month_for(fname, title):
    global _DATES
    if _DATES is None:
        try:
            _DATES = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tech-dates.json"), encoding="utf-8"))
        except Exception:
            _DATES = {}
    if fname in _DATES:
        return int(_DATES[fname][5:7])
    tl = title.lower()
    return next((m for k, m in EVENT_MONTH if k in tl), None)


def steve_jobs(rel, parts, base):
    """rel = '1- Steve Jobs/...'; parts = folders under the category; base = file name without extension."""
    title = strip_junk(base)
    top = rel.split("/")[0]
    if parts[0].startswith("99"):
        if len(parts) >= 3 and parts[1] == "Ads":
            course, cord, sub = "Apple ads", "099", re.match(r"^(\d{4})", parts[2]).group(1) if re.match(r"^\d{4}", parts[2]) else parts[2]
            cdir = "/".join([top] + parts[:2]); ydir = "/".join([top] + parts[:3])  # one folder per year inside Apple ads
        else:
            course, cord, sub = "Other", "098", None
            cdir = "/".join([top] + parts[:1])
    else:
        course, cord = clean(parts[0]); sub = None
        cdir = "/".join([top] + parts[:1])
    y, mo, d, t = split_date(title)
    shown_mo = mo  # only a month written in the file name is shown; a guessed one only sorts
    if y and not mo:  # only a year in the name: month from the event, or from data/tech-dates.json
        mo = month_for(rel.split("/")[-1], t)
    if course == "Apple ads":
        y = y or int(sub) if sub and sub.isdigit() else y
    # one parent folder 'Steve Jobs' holding the eras, Other and Apple ads (11 Nov)
    return {"course": course, "cord": cord, "sub": sub, "title": t or title, "year": y,
            "trail": ["Steve Jobs", course] + ([sub] if course == "Apple ads" else []),
            "tdirs": [top, cdir] + ([ydir] if course == "Apple ads" else []), "mon": shown_mo,
            "sort": (y or 9999, mo or 0, d or 0, (t or title).lower())}



def toc(rel, parts, base):
    """'2- TOC/1- GSP Series/1. Operations ...' : one level of course folders under the TOC chip.
    Numbered videos keep their number order; loose talks go by title."""
    course, cord = clean(parts[0])
    title = strip_junk(base).replace("\u2705", "").strip()
    m = NUM.match(title)
    num = int(m.group(1)) if m else None
    t = NUM.sub("", title).strip() if m else title
    it = {"course": course, "cord": cord, "sub": None, "title": t, "year": None,
          "trail": ["TOC", course], "tdirs": [rel.split("/")[0], rel.split("/")[0] + "/" + parts[0]],  # one TOC folder in Tech › All, like Steve Jobs
          "sort": (num if num is not None else 9999, 0, 0, t.lower())}
    if course == "GSP Series" and num is not None:
        it["legacy_id"] = "GSP Series:%d" % num  # V2.3 marks used this id: keeps your watched GSP videos watched
    return it

FIX_NAME = {"Toyota Virtual Plan": "Toyota Virtual Plant"}  # folder name typo on Whatbox: shown right until it's renamed


def lean(rel, parts, base):
    """'3- Lean/1- Joseph Juran/1- Juran on Quality Planning/...' : Lean chip opens into its folders;
    Juran and Toyota open again into their courses/series. Sessions/episodes go by number,
    series name dropped from the title; loose talks (Lean Videos) by title. V2.4.1, live 11 Nov."""
    names, cord = [], ""
    for f in parts:
        n, o = clean(f); names.append(FIX_NAME.get(n, n)); cord += o or "999"
    title = re.sub(r"\.mp4$", "", strip_junk(base), flags=re.I).replace("\u2705", "").replace("\uff1a", ":").strip()
    m = re.search(r"\b(Session|Episode)\s+0*(\d+)\b\s*(?:[-:]\s*)?(.*)$", title, re.I)
    if m:
        num, t = int(m.group(2)), m.group(1).capitalize() + " " + m.group(2).lstrip("0") + (" - " + m.group(3).strip() if m.group(3).strip() else "")
    else:
        m = re.match(r"^.*?\s-\s0*(\d+)\s-\s(.+)$", title)  # '21st Century Jet - 1 - The Big Gamble'
        num, t = (int(m.group(1)), "Episode %s - %s" % (m.group(1).lstrip("0"), m.group(2).strip())) if m else (None, title)
    top = rel.split("/")[0]
    it = {"course": names[-1], "cord": cord, "sub": None, "title": t, "year": None,  # live 11 Nov (was behind ?next)
            "trail": ["Lean"] + names, "tdirs": [top] + [top + "/" + "/".join(parts[:i + 1]) for i in range(len(parts))],
            "sort": (num if num is not None else 9999, 0, 0, t.lower())}
    if num is not None: it["num"] = num  # big number on a tile without a cover
    return it


def camel(t):
    """'RetentionMakesCompanies' -> 'Retention Makes Companies' (only for names with no spaces)."""
    if " " in t.strip(): return t
    t = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=\d)", " ", t)  # ICEDTheory, The4
    return re.sub(r"(?<=[a-z])(to|of) (?=[A-Z])", r" \1 ", t)  # Introductionto Managing, Degreeof Engagement


def reforge_dir(name):
    """'Week 1 - The Strategic Landscape' / 'W2-Activation. …' / 'W0- How …' -> 'W1 - …' (shorter, same everywhere)."""
    n, o = clean(name)
    m = re.match(r"^(?:Week\s*|W)(\d+)\s*-\s*(.*)$", n)
    if m: return "W%s - %s" % (m.group(1), m.group(2).strip()), m.group(1).zfill(3)
    m = re.match(r"^Module\s+(\d+)", n)
    return n, (m.group(1).zfill(3) if m else o)


def reforge(rel, parts, base):
    """'4- Reforge/2- Retention & Engagement/W1- Retention/1-Introduction To Retention.mp4'
    Reforge chip opens into its 2 courses › W folders › (modules) › videos. Behind ?next (V2.4.1)."""
    names, cord = [], ""
    for f in parts:
        n, o = reforge_dir(f); names.append(n); cord += o or "999"
    t = strip_junk(base).replace("&amp;", "&").replace("BONU.", "BONUS.").strip()
    k1, k2, k3 = 50, 0, ""  # order: numbered/coded lessons, then BONUS, then the live/event session
    m = re.match(r"^(\d+)([a-z])?\s*-\s*(.+)$", t)                      # '1a - …', '2b- …', '1-…'
    live = re.search(r"\b(Live|Event)$", t)
    if m:
        k1, k2, t = int(m.group(1)), ord(m.group(2)) if m.group(2) else 0, m.group(3).strip()
    elif re.match(r"^(M\d+-L\d+|S\d+-L\d+) - ", t):                       # renamed 11 Nov: 'M0-L1 - Retention Makes Companies', 'M7-L0 - …', 'S1-L2 - …' (code kept in the title)
        x = re.match(r"^[MS](\d+)-L(\d+) - ", t); k1, k2 = (20 + int(x.group(2)), 0) if t.startswith("M7") else (int(x.group(1)), int(x.group(2)))
    elif re.match(r"^M\d+-L\d+-", t):                                    # 'M0-L1-RetentionMakesCompanies'
        x = re.match(r"^M\d+-L(\d+)-(.+)$", t); k1, t = int(x.group(1)), camel(x.group(2))
    elif re.match(r"^ICEDTheoryS\d+L\d+-", t):                           # 'ICEDTheoryS1L2-ManagingInfrequency'
        x = re.match(r"^ICEDTheoryS(\d+)L(\d+)-(.+)$", t); k1, k2, t = int(x.group(1)), int(x.group(2)), camel(x.group(3))
    elif re.match(r"^R&E-M\d+-L\d+-", t):                                # Module 8: keep 'R&E-M7-L0' as asked
        x = re.match(r"^(R&E-M\d+-L(\d+))-(.+)$", t); k1, t = 20 + int(x.group(2)), x.group(1) + " - " + camel(x.group(3))  # after W6's own 1-5 (strategies follow defining)
    elif live:
        k1 = 99
        w = re.search(r"Week\s*(\d+)\s+Live", t); t = ("W%s Live" % w.group(1)) if w else t
    elif t.upper().startswith("BONUS"):
        k1 = 60
    t = re.sub(r"\s{2,}", " ", t)
    return {"course": names[-1], "cord": cord, "sub": None, "title": t, "year": None,  # live 11 Nov (was behind ?next)
            "trail": ["Reforge"] + names, "tdirs": [rel.split("/")[0]] + [rel.split("/")[0] + "/" + "/".join(parts[:i + 1]) for i in range(len(parts))],
            "sort": (k1, k2, 0, t.lower())}


ODD = {"\uff1a": ":", "\uff5c": "|", "\u29f8": "/", "\uff1f": "?", "\uff02": '"', "\u2705": ""}


def playlists(rel, parts, base):
    """'5- Playlists/3- Kanye West/2003-08-15 - Kanye West - Interview …' : Playlists chip opens into its folders
    (your numbers; same number -> by name); 'z - Backlog' sub-folders shown as one Backlog folder; family tapes left out.
    Dated videos by date (year/month shown under the title), series by episode, the rest by title. Behind ?next (V2.4.1)."""
    m = re.match(r"^(\d{4})-(\d{2})\s*-\s*(.+)$", parts[0])               # '2026-10 - Ryan Serhant': month added (11 Nov), newest first
    sub = None
    if parts[0].lower().startswith("z"):                                      # Backlog keeps its person folders (11 Nov): Backlog › Arnold › videos
        name, cord = "Backlog", "9"
        if len(parts) > 1: sub = re.sub(r"^z\s*-\s*", "", parts[1]).strip(); cord += sub.lower()
    elif m: name, cord = m.group(3).strip(), "1%06d" % (999999 - int(m.group(1) + m.group(2))) + m.group(3).strip().lower()
    else:
        name, o = clean(parts[0]); cord = "5" + (o or "998") + name.lower()
    t = strip_junk(base)
    for k, v in ODD.items(): t = t.replace(k, v)
    t = re.sub(r"\s{2,}", " ", t).strip()
    m = re.search(r"\b(\d{2})x(\d{2})\s*-\s*(.+)$", t)                     # 'Exodus (2022) - 01x03 - Chaos and Order'
    y = mo = d = None
    if m: num, t = int(m.group(2)), "Episode %d - %s" % (int(m.group(2)), m.group(3).strip()); key = (num, 0, 0, "")
    else:
        x = re.match(r"^\((\d{4})\)\s*(.+)$", t)                          # family tapes: '(1989) N CINTA 2ª …'
        if x: t = x.group(1) + " - " + x.group(2)
        y, mo, d, tt = split_date(t) if re.match(r"^\d{4}", t) else (None, None, None, t)
        t = tt or t; key = (y or 9999, mo or 0, d or 0, t.lower())
    top = rel.split("/")[0]
    it = {"course": sub or name, "cord": cord, "sub": None, "title": t, "year": y, "next": True,
          "trail": ["Playlists", name] + ([sub] if sub else []), "tdirs": [top, top + "/" + parts[0]] + ([top + "/" + parts[0] + "/" + parts[1]] if sub else []), "sort": key}
    if mo: it["mon"] = mo
    if "Rincon VCR" in parts[0]: it["ychip"] = True                           # family tapes: year chips (All · 1989 … · ?) (11 Nov)
    return it


RULES = {"1- Steve Jobs": steve_jobs, "2- TOC": toc, "3- Lean": lean, "4- Reforge": reforge, "5- Playlists": playlists}
# Piece 1 (11 Nov): first era only, to prove list → covers → tiles → tap → marks end to end. Empty = everything.
ONLY = ["1- Steve Jobs/1) 1976-1984 (Apple I & Mac)/", "1- Steve Jobs/2) 1985-1995 (Next & Pixar)/", "1- Steve Jobs/3) 1996-1999 (Apple Comeback)/", "1- Steve Jobs/4) 2000-2004 (iPod & Digital Hub)/", "1- Steve Jobs/5) 2005-2007 (iPhone)/", "1- Steve Jobs/6) 2008-2011 (iPad & Final)/", "1- Steve Jobs/99- Other/", "2- TOC/", "3- Lean/", "4- Reforge/", "5- Playlists/"]  # eras added one at a time (11 Nov)


def tech_items(lines):
    files = [l.strip().lstrip("./") for l in lines if l.strip()]
    have = set(files)
    low = {f.lower(): f for f in files}  # folder covers: folder.jpg or Folder.jpg
    out = []
    for rel in files:
        if not rel.lower().endswith(VIDEO):
            continue
        p = rel.split("/")
        if p[0] not in RULES or len(p) < 3 or (ONLY and not any(rel.startswith(o) for o in ONLY)):
            continue
        cat, corder = clean(p[0])
        base = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", p[-1])
        it = RULES[p[0]](rel, p[1:-1], base)
        if it is None: continue
        d = os.path.dirname(rel)
        it.update({"key": "learn|1- Tech/" + rel, "id": "t:" + h(rel), "category": cat, "corder": corder, "file": p[-1], "v24": True})
        for ext in IMG:
            if d + "/" + base + ext in have:
                it["src_cover"] = d + "/" + base + ext; it["cover"] = "covers/t/%sw.jpg" % h(it["src_cover"]); break  # 'w' = wide 16:9 version
        # a cover for each folder on the way down (folder.jpg in that folder on Whatbox)
        it["src_fcov"], it["fcov"] = [], []
        for dd in it.pop("tdirs"):
            src = next((low[(dd + "/" + fn).lower()] for fn in ("folder.jpg", "folder.jpeg", "folder.png") if (dd + "/" + fn).lower() in low), None)
            it["src_fcov"].append(src); it["fcov"].append("covers/t/%s.jpg" % h(src) if src else None)
        if cat in ("Lean", "Reforge", "Playlists"):  # a folder without its own cover borrows the first one below it (Toyota Virtual Plant)…
            for i in range(len(it["fcov"]) - 2, -1, -1):
                if not it["fcov"][i]: it["src_fcov"][i], it["fcov"][i] = it["src_fcov"][i + 1], it["fcov"][i + 1]
            for i in range(1, len(it["fcov"])):  # …or, with none below, its parent's (Reforge W0, Week 6 modules)
                if not it["fcov"][i]: it["src_fcov"][i], it["fcov"][i] = it["src_fcov"][i - 1], it["fcov"][i - 1]
        if it.get("legacy_id"): it["id"] = it.pop("legacy_id")
        if it["fcov"][-1]:
            it["src_folder"], it["folder"] = it["src_fcov"][-1], it["fcov"][-1]
        out.append(it)
    out.sort(key=lambda x: (x["corder"], x["cord"], x["sub"] or "", x["sort"]))
    seen = set()  # TOC: the same talk twice in a folder shows once (e.g. a copy with a space at the end of its name)
    out = [x for x in out if x["category"] != "TOC" or not ((x["course"], x["title"].lower()) in seen or seen.add((x["course"], x["title"].lower())))]
    n = {}
    for it in out:
        n[it["course"]] = n.get(it["course"], 0) + 1; it["n"] = n[it["course"]]
        del it["sort"]
        if not it.get("mon"): it.pop("mon", None)
    return out
