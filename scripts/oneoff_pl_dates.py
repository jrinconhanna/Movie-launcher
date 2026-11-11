# Usage: python3 pl_dates.py "<path to 5- Playlists>" [limit] — folder renames to 'YYYY-MM - Name'; never overwrites
import os, sys
OPS = [
 ("10- Ryan Serhant", "2026-10 - Ryan Serhant"),
 ("4- Alan Mulally", "2026-09 - Alan Mulally"),
 ("8- Exodus Jordan Peterson", "2026-08 - Exodus Jordan Peterson"),
 ("2- Tom Brady", "2026-08 - Tom Brady"),
 ("3- Kanye West", "2026-08 - Kanye West"),
 ("5- Coaching", "2026-08 - Coaching"),
 ("7- Peter Thiel", "2026-08 - Peter Thiel"),
 ("6- Radical Candor - Kim Scott", "2026-08 - Radical Candor - Kim Scott"),
 ("1- Hamel Husein (Evals)", "2025-11 - Hamel Husein (Evals)"),
 ("9- Jim Rohn", "2025-06 - Jim Rohn"),
 ("0- Rincon VCR Videos", "2026-07 - Rincon VCR Videos"),
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
