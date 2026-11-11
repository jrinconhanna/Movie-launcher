# Usage: python3 rename.py <R&E course folder> [limit]   — renames Reforge odd names to 'CODE - Title' (mv refuses to overwrite)
import os, re, sys
def words(t):
    t = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=\d)", " ", t)
    t = re.sub(r"(?<=[a-z])(to|of) (?=[A-Z])", r" \1 ", t)
    return " ".join(w[:1].upper() + w[1:] for w in t.split())
def new_name(f):
    b, ext = os.path.splitext(f)
    m = re.match(r"^M(\d+)-L(\d+)-(\S+)$", b) or re.match(r"^R&amp;E-M(\d+)-L(\d+)-(\S+)$", b)
    if m: return "M%s-L%s - %s%s" % (m.group(1), m.group(2), words(m.group(3)), ext)
    m = re.match(r"^ICEDTheoryS(\d+)L(\d+)-(\S+)$", b)
    if m: return "S%s-L%s - %s%s" % (m.group(1), m.group(2), words(m.group(3)), ext)
    return None
root, lim = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 999
done = 0
for d in sorted(os.listdir(root)):
    p = os.path.join(root, d)
    if not os.path.isdir(p): continue
    for f in sorted(os.listdir(p)):
        n = new_name(f)
        if not n or done >= lim: continue
        if os.path.exists(os.path.join(p, n)): print("SKIP (exists)", d, n); continue
        os.rename(os.path.join(p, f), os.path.join(p, n)); done += 1
        print(d[:3], "|", f, "->", n)
print("renamed", done)
