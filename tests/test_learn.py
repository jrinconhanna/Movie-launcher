"""V2.3 piece 1: the Learn list. Run: python3 tests/test_learn.py"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build import learn_items

R = []
def check(name, ok, detail=""):
    R.append(ok); print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + str(detail)))

lines = open(os.path.join(ROOT, "data", "library.txt"), encoding="utf-8").readlines()
L = learn_items(lines)
check("L1 exactly 8 GSP videos", len(L) == 8, len(L))
check("L2 numbered 1..8 in order", [x["n"] for x in L] == list(range(1, 9)), [x["n"] for x in L])
check("L3 no tick marks or numbers left in titles", all(not x["title"][0].isdigit() and "✅" not in x["title"] for x in L), [x["title"] for x in L])
check("L4 no file extension in titles", all(not x["title"].lower().endswith(".mp4") for x in L))
check("L5 only the GSP folder (no case studies, no other TOC videos)", all("1- GSP Series/" in x["key"] for x in L))
check("L6 keys unique", len({x["key"] for x in L}) == len(L))
fake = ["./1- Tech/2- TOC/1- GSP Series/✅ 3. Some Title.mp4\n", "./1- Tech/2- TOC/1- GSP Series/sub/9. Nested.mp4\n", "./1- Tech/2- TOC/1- GSP Series/notes.txt\n"]
F = learn_items(fake)
check("L7 tick stripped, nested folders and non-videos ignored", [(x["n"], x["title"]) for x in F] == [(3, "Some Title")], F)
lib = json.load(open(os.path.join(ROOT, "library.json"), encoding="utf-8"))
check("L8 library.json carries the same Learn list", lib.get("learn") == L, "run build or patch library.json")
for x in L: print("   ", x["n"], x["title"])
print(f"{sum(R)}/{len(R)} passed"); sys.exit(0 if all(R) else 1)
