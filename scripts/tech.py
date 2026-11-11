"""V2.4: Tech videos from the real Whatbox file list (data/tech-files.txt).

One rule set per category folder. Piece 1: Steve Jobs.
Each item: key, id (stable mark id), course, cord, category, corder, n, title,
year, sub (year chip inside a folder), src_cover / src_folder (paths on Whatbox,
relative to 1- Tech), cover / folder (paths in this repo once synced), v24.
"""
import hashlib, json, os, re

VIDEO = (".mp4", ".mkv", ".m4v", ".mov", ".avi", ".webm")
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

RULES = {"1- Steve Jobs": steve_jobs, "2- TOC": toc}
# Piece 1 (11 Nov): first era only, to prove list → covers → tiles → tap → marks end to end. Empty = everything.
ONLY = ["1- Steve Jobs/1) 1976-1984 (Apple I & Mac)/", "1- Steve Jobs/2) 1985-1995 (Next & Pixar)/", "1- Steve Jobs/3) 1996-1999 (Apple Comeback)/", "1- Steve Jobs/4) 2000-2004 (iPod & Digital Hub)/", "1- Steve Jobs/5) 2005-2007 (iPhone)/", "1- Steve Jobs/6) 2008-2011 (iPad & Final)/", "1- Steve Jobs/99- Other/", "2- TOC/"]  # eras added one at a time (11 Nov)


def tech_items(lines):
    files = [l.strip().lstrip("./") for l in lines if l.strip()]
    have = set(files)
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
        d = os.path.dirname(rel)
        it.update({"key": "learn|1- Tech/" + rel, "id": "t:" + h(rel), "category": cat, "corder": corder, "file": p[-1], "v24": True})
        for ext in IMG:
            if d + "/" + base + ext in have:
                it["src_cover"] = d + "/" + base + ext; it["cover"] = "covers/t/%sw.jpg" % h(it["src_cover"]); break  # 'w' = wide 16:9 version
        # a cover for each folder on the way down (folder.jpg in that folder on Whatbox)
        it["src_fcov"], it["fcov"] = [], []
        for dd in it.pop("tdirs"):
            src = next((dd + "/" + fn for fn in ("folder.jpg", "folder.jpeg", "folder.png") if dd + "/" + fn in have), None)
            it["src_fcov"].append(src); it["fcov"].append("covers/t/%s.jpg" % h(src) if src else None)
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
