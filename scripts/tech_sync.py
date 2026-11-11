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


def wide(im, left=False):
    """Trim black borders baked into the image, then cut to 16:9 (keeps the upper part on tall images, where faces are)."""
    box = im.convert("L").point(lambda v: 255 if v > 28 else 0).getbbox()
    if box and (box[2] - box[0]) * (box[3] - box[1]) > 0.15 * im.width * im.height:
        im = im.crop(box)
    w, hh = im.size
    if w / hh > 16 / 9:
        nw = int(hh * 16 / 9); x = 0 if left else (w - nw) // 2; im = im.crop((x, 0, x + nw, hh))
    else:
        nh = int(w * 9 / 16); y = int((hh - nh) * (0.25 if hh > w else 0.5)); im = im.crop((0, y, w, y + nh))
    return im.resize((640, 360))


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
        for src, dst in [(it.get("src_cover"), it.get("cover"))] + list(zip(it.get("src_fcov", []), it.get("fcov", []))):
            if src and not os.path.exists(os.path.join(ROOT, dst)):
                need[src] = dst
    print("%d files listed, %d covers to copy" % (len(lines), len(need)))
    frames(tech_items(lines))
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
        if dst.endswith("w.jpg"):
            im = wide(im)  # video: same 16:9 tile for every cover
        else:
            im.thumbnail((320, 480))  # folder: portrait poster, as is
        im.save(os.path.join(ROOT, dst), "JPEG", quality=72, optimize=True, progressive=True)
    print("covers copied")


def frames(items):
    """Grab one frame per listed video (at its second) on Whatbox, copy it back and cut it to the 16:9 tile."""
    need = [it for it in items if it.get("src_frame") and not os.path.exists(os.path.join(ROOT, it["frame"]))]
    print("%d frames to grab" % len(need))
    if not need:
        return
    from PIL import Image
    import shlex
    cmds = ["mkdir -p /tmp/lf && rm -f /tmp/lf/*"]
    for it in need:
        src, out = shlex.quote(BASE + "/" + it["src_frame"]), os.path.basename(it["frame"])[:-4]
        if it["frame_at"] == "nb":  # first non-black: 5 frames a second over the first 3 s, picked here
            cmds.append("ffmpeg -nostdin -v error -y -t 3 -i %s -vf fps=5 -q:v 3 /tmp/lf/%s_s%%02d.jpg || true" % (src, out))
        else:
            cmds.append("ffmpeg -nostdin -v error -y -ss %d -i %s -frames:v 1 -q:v 3 /tmp/lf/%s.jpg || true" % (it["frame_at"], src, out))
    r = subprocess.run(SSH + [HOST, " ; ".join(cmds)], capture_output=True, text=True, timeout=1800)
    tmp = tempfile.mkdtemp()
    subprocess.run(["scp", "-i", os.path.expanduser("~/.ssh/whatbox"), "-o", "BatchMode=yes", HOST + ":/tmp/lf/*.jpg", tmp + "/"], timeout=1200)
    subprocess.run(SSH + [HOST, "rm -rf /tmp/lf"], timeout=60)
    os.makedirs(os.path.join(ROOT, "covers", "t"), exist_ok=True)
    n = 0
    for it in need:
        base = os.path.basename(it["frame"])[:-4]
        if it["frame_at"] == "nb":
            p = first_lit(sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith(base + "_s")), Image)
        else:
            p = os.path.join(tmp, base + ".jpg")
        if not p or not os.path.exists(p): continue
        wide(Image.open(p).convert("RGB"), left=True).save(os.path.join(ROOT, it["frame"]), "JPEG", quality=72, optimize=True, progressive=True); n += 1
    print("frames saved: %d" % n)


def first_lit(paths, Image):
    """First frame that isn't black (bright enough and not flat); the last one if all are dark."""
    from PIL import ImageStat
    for p in paths:
        st = ImageStat.Stat(Image.open(p).convert("L"))
        if st.mean[0] > 25 and st.stddev[0] > 12: return p
    return paths[-1] if paths else None


if __name__ == "__main__":
    main()
