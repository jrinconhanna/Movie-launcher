"""V2.4 piece 1: Steve Jobs from the real Whatbox list. Run: python3 tests/test_tech.py"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tech
from tech import tech_items, split_date
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail)); fails += 0 if ok else 1
FIRST = tech_items(open(os.path.join(ROOT, "data", "tech-files.txt"), encoding="utf-8").readlines())
check("S0 piece 1: only the first era (6 videos)", len(FIRST) == 6 and {t["course"] for t in FIRST} == {"1976-1984 (Apple I & Mac)"}, str(len(FIRST)))
lib_ids = {t["id"] for t in FIRST}
tech.ONLY = []  # the rules below run on the whole Steve Jobs folder
T = tech_items(open(os.path.join(ROOT, "data", "tech-files.txt"), encoding="utf-8").readlines())
sj = [t for t in T if t["category"] == "Steve Jobs"]
by = lambda c: [t for t in sj if t["course"] == c]
courses = list(dict.fromkeys(t["course"] for t in sj))
check("S1 Steve Jobs: 173 videos", len(sj) == 173, str(len(sj)))
check("S2 eight folders in order, eras first, then Other, Apple ads", courses == ["1976-1984 (Apple I & Mac)", "1985-1995 (Next & Pixar)", "1996-1999 (Apple Comeback)", "2000-2004 (iPod & Digital Hub)", "2005-2007 (iPhone)", "2008-2011 (iPad & Final)", "Other", "Apple ads"], str(courses))
check("S3 date order inside an era (Expo Paris Sept 2002 after Macworld SF Jan 2002)", [t["title"] for t in by("2000-2004 (iPod & Digital Hub)")].index("Apple Expo Paris") > [t["title"] for t in by("2000-2004 (iPod & Digital Hub)")].index("Macworld SF"))
check("S4 title without the date, year kept", split_date("1997-01-07 - Macworld (Return, NeXT, OpenStep)") == (1997, 1, 7, "Macworld (Return, NeXT, OpenStep)"))
check("S5 odd dates read: 2002 (09-10), 2010 Oct, 1999-07-", [split_date(x)[:2] for x in ["2002 (09-10) - Apple Expo Paris", "2010 Oct - Apple Special Event", "1999-07- Steve Jobs Apple HQ"]] == [(2002, 9), (2010, 10), (1999, 7)])
ads = by("Apple ads")
check("S6 Apple ads: 72, year chip on each, no (360p…) junk", len(ads) == 72 and all(a["sub"] and a["sub"].isdigit() for a in ads) and not any("fps" in a["title"] for a in ads))
check("S7 every era video has its cover except 3 with none on Whatbox", sum(1 for t in sj if t["course"] not in ("Other", "Apple ads") and not t.get("cover")) == 3)
check("S8 every era has its folder cover", all(by(c)[0].get("folder") for c in courses[:6]))
check("S9 ids unique and stable (t: + hash of the path)", len({t["id"] for t in T}) == len(T) and all(t["id"].startswith("t:") for t in T))
check("S10 numbered 1..n inside each folder", all([t["n"] for t in by(c)] == list(range(1, len(by(c)) + 1)) for c in courses))
lib = json.load(open(os.path.join(ROOT, "library.json"), encoding="utf-8"))
check("S11 library.json carries them, flagged v24", {x["id"] for x in lib.get("learn", []) if x.get("v24")} == lib_ids)
print("%d failed" % fails); sys.exit(1 if fails else 0)
