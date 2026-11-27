#!/usr/bin/env python3
"""Generate one shareable page per Inspiration video: insp/<id>.html
Each page has WhatsApp/Open Graph preview tags (title, description, thumbnail)
and a simple player for Chrissi. Run: python3 insp/build.py"""
import json, html, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://jrinconhanna.github.io/Movie-launcher"
videos = json.load(open(os.path.join(ROOT, "data", "inspiration.json")))
tpl = open(os.path.join(ROOT, "insp", "template.html")).read()
for v in videos:
    e = {k: html.escape(str(x), quote=True) for k, x in v.items()}
    page = (tpl.replace("{{TITLE}}", e["title"]).replace("{{DESC}}", e["desc"])
               .replace("{{IMG}}", f"{SITE}/covers/insp/{v['id']}.jpg")
               .replace("{{URL}}", f"{SITE}/insp/{v['id']}.html")
               .replace("{{SRC}}", html.escape(v["link"] + "&raw=1", quote=True))
               .replace("{{POSTER}}", f"../covers/insp/{v['id']}.jpg"))
    open(os.path.join(ROOT, "insp", v["id"] + ".html"), "w").write(page)
    print("wrote insp/%s.html" % v["id"])
