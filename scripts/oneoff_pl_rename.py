# Usage: python3 pl_rename.py "<path to 5- Playlists>" [limit]  — renames only these; never overwrites
import os, sys
K = "3- Kanye West/"
OPS = [
 (K + "(2002) - Kanye West Interview .mp4", K + "2002 - Kanye West Interview.mp4"),
 (K + "(2002) Kanye West Classic  Before The Wire! Interview Before He Flipped His BMW! DJ Whoo Kid Exclusive!   RadioPlanet tv   Where Hip Hop Meets Hollywood.mp4", K + "2002 - Kanye West Classic  Before The Wire! Interview Before He Flipped His BMW! DJ Whoo Kid Exclusive!   RadioPlanet tv   Where Hip Hop Meets Hollywood.mp4"),
 (K + "(2003 Aug. 15) Kanye West - Interview & Freestyle Before He Was A Rap Star.mp4", K + "2003-08-15 - Kanye West - Interview & Freestyle Before He Was A Rap Star.mp4"),
 (K + "(2003) In The Streets- Exclusive Kanye West Interview.mp4", K + "2003 - In The Streets- Exclusive Kanye West Interview.mp4"),
 (K + "(2004) - Diary Of Kanye West - On Tour in Europe .mp4", K + "2004 - Diary Of Kanye West - On Tour in Europe.mp4"),
 (K + "(2004) - Kanye West First 106 & Park Interview.mp4", K + "2004 - Kanye West First 106 & Park Interview.mp4"),
 (K + "(2004) Kanye West - first ever UK interview #TBT.mp4", K + "2004 - Kanye West - first ever UK interview #TBT.mp4"),
 (K + "(2004) Kanye West Interview - Right After College Dropout.mp4", K + "2004 - Kanye West Interview - Right After College Dropout.mp4"),
 (K + "(2005) - Kanye West in - Charlie Rose Interview.mp4", K + "2005 - Kanye West in - Charlie Rose Interview.mp4"),
 (K + "(2005) Kanye West At 28 Said That God Saved Him To Be A Vessel.mp4", K + "2005 - Kanye West At 28 Said That God Saved Him To Be A Vessel.mp4"),
 (K + "(2006) Kayne West in .mp4", K + "2006 - Kayne West in.mp4"),
 (K + "(2007) - Spike Jonze Spends Saturday with Kanye West.mp4", K + "2007 - Spike Jonze Spends Saturday with Kanye West.mp4"),
 (K + "(2008 11⧸25) Kanye West on Late Night with Conan O'Brien.mp4", K + "2008-11-25 - Kanye West on Late Night with Conan O'Brien.mp4"),
 (K + "(2013) Kanye West. Zane Lowe. Full Interview.mp4", K + "2013 - Kanye West. Zane Lowe. Full Interview.mp4"),
 ("1- Hamel Husein (Evals)/✅ From Noob to Automated Evals In A Week (as a PM) w⧸Teresa Torres.mp4", "1- Hamel Husein (Evals)/From Noob to Automated Evals In A Week (as a PM) w⧸Teresa Torres.mp4"),
 ("5- Peter Thiel", "7- Peter Thiel"),
 ("10 - Ryan Serhant", "10- Ryan Serhant"),
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
