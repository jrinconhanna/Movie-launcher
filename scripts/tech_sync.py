"""V2.4: read the Tech file list from Whatbox and copy any covers we don't have yet.

Runs in the hourly GitHub job before build.py, only when the Whatbox key is set up
(~/.ssh/whatbox, from the WHATBOX_SSH_KEY secret). Writes data/tech-files.txt and
covers/t/<id>.jpg (shrunk to ~300 px wide, about 15-30 KB each).
"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from tech import tech_items

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "javierrincon@kiwi.whatbox.ca"
BASE = "files/Javi/1- Tech"
SSH = ["ssh", "-i", os.path.expanduser("~/.ssh/whatbox"), "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]


def main():
    r = subprocess.run(SSH + [HOST, 'cd "%s" && find . -type f | sort' % BASE], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit("Whatbox list failed: " + r.stderr[-300:])
    lines = [l[2:] if l.startswith("./") else l for l in r.stdout.splitlines() if l.strip()]
    if len(lines) < 50:
        sys.exit("Whatbox list looks too short (%d files); keeping the old one" % len(lines))
    with open(os.path.join(ROOT, "data", "tech-files.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    need = {}
    for it in tech_items(lines):
        for src, dst in ((it.get("src_cover"), it.get("cover")), (it.get("src_folder"), it.get("folder"))):
            if src and not os.path.exists(os.path.join(ROOT, dst)):
                need[src] = dst
    print("%d files listed, %d covers to copy" % (len(lines), len(need)))
    if not need:
        return
    from PIL import Image
    tmp = tempfile.mkdtemp()
    with open(os.path.join(tmp, "list.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(need) + "\n")
    subprocess.run(["rsync", "-s", "-e", " ".join(SSH), "--files-from=" + os.path.join(tmp, "list.txt"),
                    HOST + ":" + BASE + "/", os.path.join(tmp, "src") + "/"], check=True, timeout=900)
    os.makedirs(os.path.join(ROOT, "covers", "t"), exist_ok=True)
    for src, dst in need.items():
        p = os.path.join(tmp, "src", src)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((320, 480))
        im.save(os.path.join(ROOT, dst), "JPEG", quality=72, optimize=True, progressive=True)
    print("covers copied")


if __name__ == "__main__":
    main()
