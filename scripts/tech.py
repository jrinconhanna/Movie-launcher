"""V2.4: Tech videos from the real Whatbox file list (data/tech-files.txt).

One rule set per category folder. Piece 1: Steve Jobs.
Each item: key, id (stable mark id), course, cord, category, corder, n, title,
year, sub (year chip inside a folder), src_cover / src_folder (paths on Whatbox,
relative to 1- Tech), cover / folder (paths in this repo once synced), v24.
"""
import hashlib, os, re

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


def steve_jobs(rel, parts, base):
    """rel = '1- Steve Jobs/...'; parts = folders under the category; base = file name without extension."""
    title = strip_junk(base)
    if parts[0].startswith("99"):
        if len(parts) >= 3 and parts[1] == "Ads":
            course, cord, sub = "Apple ads", "099", re.match(r"^(\d{4})", parts[2]).group(1) if re.match(r"^\d{4}", parts[2]) else parts[2]
        else:
            course, cord, sub = "Other", "098", None
    else:
        course, cord = clean(parts[0]); sub = None
    y, mo, d, t = split_date(title)
    if course == "Apple ads":
        y = y or int(sub) if sub and sub.isdigit() else y
    return {"course": course, "cord": cord, "sub": sub, "title": t or title, "year": y,
            "sort": (y or 9999, mo or 0, d or 0, (t or title).lower())}


RULES = {"1- Steve Jobs": steve_jobs}
# Piece 1 (11 Nov): first era only, to prove list → covers → tiles → tap → marks end to end. Empty = everything.
ONLY = ["1- Steve Jobs/1) 1976-1984 (Apple I & Mac)/"]


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
                it["src_cover"] = d + "/" + base + ext; it["cover"] = "covers/t/%s.jpg" % h(it["src_cover"]); break
        # course folder cover: the era's own folder.jpg (not deeper folders like Ads/1998)
        cdir = "/".join(p[:2]) if not it["course"] in ("Apple ads", "Other") else None
        for fn in ("folder.jpg", "folder.jpeg", "folder.png"):
            if cdir and cdir + "/" + fn in have:
                it["src_folder"] = cdir + "/" + fn; it["folder"] = "covers/t/%s.jpg" % h(it["src_folder"]); break
        out.append(it)
    out.sort(key=lambda x: (x["corder"], x["cord"], x["sub"] or "", x["sort"]))
    n = {}
    for it in out:
        n[it["course"]] = n.get(it["course"], 0) + 1; it["n"] = n[it["course"]]
        del it["sort"]
    return out
