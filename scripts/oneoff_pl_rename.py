# Usage: python3 pl_rename.py "<path to 5- Playlists>" [limit]  — renames only these; never overwrites
import os, sys
K = "3- Kanye West/"
OPS = [
 ("5- Coaching", "7- Coaching"),
]
root, lim = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 999
n = 0
for a, b in OPS:
    if n >= lim: break
    pa, pb = os.path.join(root, a), os.path.join(root, b)
    if not os.path.exists(pa): print("MISSING", a); continue
    if os.path.exists(pb): print("SKIP (exists)", b); continue
    os.rename(pa, pb); n += 1; print("OK", a, "->", b)
print("renamed", n)
