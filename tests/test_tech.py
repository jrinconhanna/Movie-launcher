"""V2.4 piece 1: Steve Jobs from the real Whatbox list. Run: python3 tests/test_tech.py"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tech
from tech import tech_items, split_date
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail)); fails += 0 if ok else 1
ALL = tech_items(open(os.path.join(ROOT, "data", "tech-files.txt"), encoding="utf-8").readlines())
FIRST = [t for t in ALL if t["category"] == "Steve Jobs"]
check("S0 all of Steve Jobs: 6 eras (98) + Other (3) + Apple ads (72)", len(FIRST) == 173 and {t["course"] for t in FIRST} == {"1976-1984 (Apple I & Mac)", "1985-1995 (Next & Pixar)", "1996-1999 (Apple Comeback)", "2000-2004 (iPod & Digital Hub)", "2005-2007 (iPhone)", "2008-2011 (iPad & Final)", "Other", "Apple ads"}, str(len(FIRST)))
lib_ids = {t["id"] for t in ALL}
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
check("S7 every era video has its cover has its cover", sum(1 for t in sj if t["course"] not in ("Other", "Apple ads") and not t.get("cover")) == 0)
check("S8 every era has its folder cover", all(by(c)[0].get("folder") for c in courses[:6]))
check("S9 ids unique and stable (t: + hash of the path)", len({t["id"] for t in T}) == len(T) and all(t["id"].startswith("t:") or (t["course"] == "GSP Series" and t["id"].startswith("GSP Series:")) for t in T))
check("S10 numbered 1..n inside each folder", all([t["n"] for t in by(c)] == list(range(1, len(by(c)) + 1)) for c in courses))
lib = json.load(open(os.path.join(ROOT, "library.json"), encoding="utf-8"))
check("S11 library.json carries them, flagged v24", {x["id"] for x in lib.get("learn", []) if x.get("v24")} == lib_ids)
e4 = [t["title"] for t in T if t["course"] == "2000-2004 (iPod & Digital Hub)"]
check("S12 year-only names ordered by event month (2002: Macworld SF Jan, Xserve May, WWDC, Macworld NY, Apple Expo Paris Sep)", e4[11:16] == ["Macworld SF", "Apple Special Event (Xserve)", "WWDC (Death of OS 9)", "Macworld NY", "Apple Expo Paris"], str(e4[11:16]))
check("S13 original iPod event (Oct 2001) after Macworld NY (Jul 2001)", e4.index("Apple Special Event Town Hall (Original iPod)") > e4.index("Macworld NY"))
ads = [t for t in FIRST if t["course"] == "Apple ads"]
check("S14 Apple ads: one folder per year inside it (10 years, in order)", [t["trail"] for t in ads][0] == ["Steve Jobs", "Apple ads", "1984"] and sorted({t["trail"][2] for t in ads}) == ["1984", "1985", "1997", "1998", "1999", "2000", "2001", "2002", "2004", "2007"] and [t["trail"][2] for t in ads] == sorted(t["trail"][2] for t in ads), str({t["trail"][2] for t in ads}))
check("S15 Other and Apple ads sit next to the eras, after them", [t["trail"][:2] for t in FIRST if t["course"] == "Other"] == [["Steve Jobs", "Other"]] * 3 and FIRST.index(next(t for t in FIRST if t["course"] == "Other")) > FIRST.index(next(t for t in FIRST if t["course"] == "2008-2011 (iPad & Final)")))
toc = [t for t in ALL if t["category"] == "TOC"]
check("T1 TOC: one TOC folder holding 3 courses (GSP 8, Case Studies 14, Videos 23)", [t["trail"] for t in toc][0] == ["TOC", "GSP Series"] and {(t["course"], sum(1 for x in toc if x["course"] == t["course"])) for t in toc} == {("GSP Series", 8), ("TOC Case Studies", 14), ("TOC Videos", 23)}, str({t["course"] for t in toc}))
check("T2 GSP keeps its V2.3 ids, so watched marks stay", [t["id"] for t in toc if t["course"] == "GSP Series"] == ["GSP Series:%d" % i for i in range(1, 9)])
check("T3 GSP in number order, number gone from the title; loose talks by title", [t["title"] for t in toc][0] == "Operations - DBR and Buffer Management" and [t["title"] for t in toc if t["course"] == "TOC Videos"] == sorted([t["title"] for t in toc if t["course"] == "TOC Videos"], key=str.lower))
check("T4 the duplicate talk shows once", sum(1 for t in toc if t["title"] == "Strategy Tactic Implementation Audit Process") == 1)
lean = [t for t in ALL if t["category"] == "Lean"]
lc = lambda c: [t for t in lean if t["course"] == c]
check("N1 Lean: one Lean folder holding 4 folders, in folder order", list(dict.fromkeys(t["trail"][1] for t in lean)) == ["Joseph Juran", "21st Century Jet - Building the Boeing 777", "Lean Videos", "Toyota Virtual Plant"], str({t["trail"][1] for t in lean}))
check("N2 Juran and Toyota open into their courses/series", list(dict.fromkeys(tuple(t["trail"]) for t in lean if len(t["trail"]) == 3)) == [("Lean", "Joseph Juran", "Juran on Quality Planning"), ("Lean", "Joseph Juran", "Juran on Quality Improvement"), ("Lean", "Toyota Virtual Plant", "How Toyota Cars are made"), ("Lean", "Toyota Virtual Plant", "The Toyota Production System as Taught by Toyota")])
qp, qi = lc("Juran on Quality Planning"), lc("Juran on Quality Improvement")
check("N3 Quality Planning: 15 sessions in number order (not by name), series name dropped", len(qp) == 15 and [t["num"] for t in qp] == list(range(1, 16)) and qp[0]["title"] == "Session 1 - Introduction" and qp[9]["title"] == "Session 10 - Optimize Product Design: Methods", str([t["title"] for t in qp[:2]]))
check("N4 Quality Improvement: sessions by number, missing ones slot in when added", len(qi) >= 8 and [t["num"] for t in qi] == sorted(t["num"] for t in qi) and qi[0]["title"] == "Session 1 - Proof of the Need" and not any(t["title"].endswith(" ") for t in qi))
jet = lc("21st Century Jet - Building the Boeing 777")
check("N5 21st Century Jet: 5 episodes, 'Episode 1 - The Big Gamble'", [t["title"] for t in jet][:1] == ["Episode 1 - The Big Gamble"] and len(jet) == 5)
lv = [t["title"] for t in lc("Lean Videos")]
check("N6 Lean Videos: loose talks alphabetical, no ticks or .mp4", lv == sorted(lv, key=str.lower) and not any("\u2705" in x or x.lower().endswith(".mp4") for x in lv) and len(lv) >= 16, str(len(lv)))
check("N7 Toyota series: 'Episode 1' .. in order (14 + 5)", [t["title"] for t in lc("How Toyota Cars are made")] == ["Episode %d" % i for i in range(1, 15)] and len(lc("The Toyota Production System as Taught by Toyota")) == 5)
check("N8 every Lean folder level has a cover (Folder.jpg any case; Toyota top borrows its first series')", all(all(t["fcov"]) for t in lean))
check("N9 Lean is live (no ?next flag)", lean and not any(t.get("next") for t in lean))
rf = [t for t in ALL if t["category"] == "Reforge"]
rc = lambda c: [t["title"] for t in rf if t["course"] == c]
check("R1 Reforge: 97 videos in 2 courses, live", len(rf) >= 97 and list(dict.fromkeys(t["trail"][1] for t in rf)) == ["AI Strategy", "Retention & Engagement"] and not any(t.get("next") for t in rf), str(len(rf)))
check("R2 weeks named 'W1 - …' in both courses, in order", list(dict.fromkeys(t["trail"][2] for t in rf if t["trail"][1] == "AI Strategy")) == ["W1 - The Strategic Landscape", "W2 - Market Strategy", "W3 - Product Strategy", "W4 - Execution Strategy"] and list(dict.fromkeys(t["trail"][2] for t in rf if t["trail"][1] != "AI Strategy"))[:3] == ["W0 - How Retention Determines The Top 1%", "W1 - Retention", "W2 - Activation. Defining, Measuring, And Analyzing"])
w1 = rc("W1 - The Strategic Landscape")
check("R3 AI Strategy: lessons by code (1a…2c), code dropped, live session last as 'W1 Live'", w1[0] == "AI Tech Shift - How AI Is Creating More Red Ocean vs Blue Ocean" and w1[-1] == "W1 Live" and len(w1) == 8, str(w1[:1] + w1[-1:]))
r2 = rc("W2 - Activation. Defining, Measuring, And Analyzing")
check("R4 R&E: numbered lessons, then BONUS (BONU fixed), event last", r2[0] == "Introduction To Activation" and r2[-1] == "W2 Event" and "BONUS. Venn Diagram Analysis" in r2 and r2.index("BONUS. Venn Diagram Analysis") > r2.index("Analyzing Your Activation Flow"), str(r2))
check("R5 renamed files (11 Nov) show 'CODE - Title' and keep their order", rc("W0 - How Retention Determines The Top 1%") == ["M0-L1 - Retention Makes Companies", "M0-L2 - Retention Breaks Companies", "M0-L3 - Retention Is Getting Harder", "M0-L4 - Program Preview"] and rc("W7 - ICED Theory (Bonus)")[:2] == ["S0-L1 - Introduction To Managing Infrequent Products", "S1-L1 - The 4 Dimensions Of Infrequent Products"])
check("R6 W6 is one flat week (defining 1-5, then strategies, then the event); ICED Theory is its own W7", rc("W6 - Resurrection. Defining, Measuring, And Analyzing") == ["Introduction To Resurrection", "When You Should Focus On Resurrection", "Defining At Risk Users For Churn Prediction", "Defining Dormant Engagement State", "Defining Churned Engagement State", "M7-L0 - Introduction To Resurrection Strategies", "M7-L1 - Strategies For At Risk Users", "M7-L2 - Involuntary Dormant Strategies", "M7-L3 - Resurrecting Voluntary Dormant Users", "W6 Event"] and len(rc("W7 - ICED Theory (Bonus)")) == 9 and not any(len(t["trail"]) > 3 for t in rf), str(rc("W6 - Resurrection. Defining, Measuring, And Analyzing")))
check("R7 every Reforge folder level has a cover (W0 and modules use their parent's)", all(all(t["fcov"]) for t in rf))
check("R8 the Reforge folder uses its own folder.jpg (not AI Strategy's)", all(t["src_fcov"][0] == "4- Reforge/folder.jpg" for t in rf) and rf[0]["src_fcov"][1] == "4- Reforge/1- AI Strategy/folder.jpg")
pl = [t for t in ALL if t["category"] == "Playlists"]
pc = lambda c: [t["title"] for t in pl if t["course"] == c]
order = list(dict.fromkeys(t["course"] for t in pl))
check("P1 Playlists live; folders 'YYYY-MM - Name' newest first (same month by name), Backlog last", not any(t.get("next") for t in pl) and order[:2] == ["Ryan Serhant", "Alan Mulally"] and order[2:8] == sorted(order[2:8], key=str.lower) and order[9:] == ["Hamel Husein (Evals)", "Arnold", "Jeff Bezos", "Jim Rohn"] and order.index("Rincon VCR Videos") == 8, str(order))
check("P2 family tapes in Playlists at 2026-07, by year", len(pc("Rincon VCR Videos")) == 47 and sum(1 for t in pl if t["course"] == "Rincon VCR Videos" and t["year"]) >= 45)
k = [t for t in pl if t["course"] == "Kanye West"]
check("P3 Kanye by date, year under the title, month where known", [t["year"] for t in k] == sorted(t["year"] for t in k) and k[0]["title"] == "Kanye West Classic Before The Wire! Interview Before He Flipped His BMW! DJ Whoo Kid Exclusive! RadioPlanet tv Where Hip Hop Meets Hollywood" and any(t.get("mon") == 8 for t in k), str([t["title"] for t in k[:2]]))
check("P4 Exodus by episode: 'Episode 1 - Faith as an Adventure' … 11", pc("Exodus Jordan Peterson")[0] == "Episode 1 - Faith as an Adventure" and len(pc("Exodus Jordan Peterson")) == 11)
check("P5 odd characters cleaned, no ticks", not any(re.search("[\uff1a\uff5c\u29f8\uff1f\uff02\u2705]", t["title"]) for t in pl) and "AI Eng vs. PMs: Who Should Drive Evals?" in pc("Hamel Husein (Evals)"))
check("P6 Backlog shows its folders (names without 'z- '): Arnold, Jeff Bezos, Jim Rohn", sorted({t["trail"][2] for t in pl if t["trail"][1] == "Backlog"}) == ["Arnold", "Jeff Bezos", "Jim Rohn"] and all(len(t["trail"]) == 3 for t in pl if t["trail"][1] == "Backlog"))
check("P7 every Playlists folder has a cover (Backlog borrows)", all(all(t["fcov"]) for t in pl))
fr = [t for t in ALL if t.get("frame")]
check("F1 frame covers: Reforge AI Strategy W1 + W2 (8 + 7 videos, at 3 s); no frame where a .png exists", len(fr) == 15 and all(t["trail"][2] in ("W1 - The Strategic Landscape", "W2 - Market Strategy") and t["frame_at"] == 3 and not t.get("cover") for t in fr), str(len(fr)))
print("%d failed" % fails); sys.exit(1 if fails else 0)
