#!/usr/bin/env python3
"""Extract the love-story ODT into _book_three/ chapter files (no audio).

Splits at "Chapter N" headings, treats the first short line of each chapter as
its POV/byline (subtitle), keeps the front matter (dedication, author's note,
playlist) as the intro, and preserves inline italic/bold. Run:
    .venv-docx/bin/python .tools/odt_to_book.py
"""
import os, re, html, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ODT = os.path.join(ROOT, "story", "book-three", "It all comes back to us final draft.odt")
OUTDIR = os.path.join(ROOT, "_book_three")
AUDIO = ""  # no audio for this book yet

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
}
def q(p): return "{%s}%s" % (NS[p.split(":")[0]], p.split(":")[1])
def local(el): return el.tag.split("}")[-1]

POVS = {"hari", "smruthi", "sanskriti"}
CHAP_RE = re.compile(r"^\s*chapter\s*[-–—]?\s*(\d+)\s*$", re.I)

# character renames (whole-word, applied to all extracted text + POV bylines)
NAME_MAP = {"Hari": "Krish", "Smruthi": "Radhe", "Srinivas": "Kiran", "Divya": "Soumya", "Prachiti": "Pallavi"}
_NAME_RE = re.compile(r"\b(" + "|".join(map(re.escape, NAME_MAP)) + r")\b")
def apply_names(s): return _NAME_RE.sub(lambda m: NAME_MAP[m.group(1)], s)

def load():
    z = zipfile.ZipFile(ODT)
    root = ET.fromstring(z.read("content.xml").decode("utf-8"))
    # map automatic text styles -> (italic, bold)
    italic, bold = set(), set()
    for st in root.iter(q("style:style")):
        if st.get(q("style:family")) != "text":
            continue
        name = st.get(q("style:name"))
        tp = st.find(q("style:text-properties"))
        if tp is None:
            continue
        if tp.get(q("fo:font-style")) == "italic":
            italic.add(name)
        w = tp.get(q("fo:font-weight"))
        if w and w not in ("normal",):
            bold.add(name)
    body = root.find(q("office:body"))
    return body, italic, bold

def render_para(el, italic, bold):
    out = []
    def esc(t, it, bo):
        t = html.escape(t)
        if bo: t = "<strong>%s</strong>" % t
        if it: t = "<em>%s</em>" % t
        return t
    def walk(node, it, bo):
        if node.text:
            out.append(esc(node.text, it, bo))
        for ch in node:
            tag = local(ch)
            if tag == "span":
                stn = ch.get(q("text:style-name"))
                walk(ch, it or stn in italic, bo or stn in bold)
            elif tag == "line-break":
                out.append("<br/>")
            elif tag == "s":
                out.append(" " * int(ch.get(q("text:c"), "1")))
            elif tag == "tab":
                out.append(" ")
            else:
                walk(ch, it, bo)
            if ch.tail:
                out.append(esc(ch.tail, it, bo))
    walk(el, False, False)
    return re.sub(r"\s+", " ", "".join(out)).strip()

def main():
    body, italic, bold = load()
    # ordered list of (plain, html) for each paragraph/heading
    paras = []
    for el in body.iter():
        if local(el) in ("p", "h"):
            h = render_para(el, italic, bold)
            plain = re.sub(r"<[^>]+>", "", h)
            if plain.strip():
                paras.append((plain.strip(), h))

    # split into front matter + chapters
    chapters = []          # list of dict(num, pov, paras=[html])
    front = []
    cur = None
    for plain, h in paras:
        m = CHAP_RE.match(plain)
        if m:
            cur = {"num": int(m.group(1)), "pov": "", "body": [], "tag": ""}
            chapters.append(cur)
            continue
        if cur is None:
            front.append((plain, h))
            continue
        # first short line after the heading = POV/byline
        if not cur["body"] and not cur["pov"] and plain.lower() in POVS:
            cur["pov"] = plain
            continue
        cur["body"].append((plain, h))

    # "Seventeen Years Ago" sits at the end of the front matter -> ch1 time tag
    if front and front[-1][0].lower().startswith("seventeen years ago"):
        if chapters:
            chapters[0]["tag"] = front[-1][0]
        front = front[:-1]

    os.makedirs(OUTDIR, exist_ok=True)
    def write(path, fm, body_html):
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n" + fm + "\n---\n" + body_html + "\n")

    # intro (front matter: dedication, note, playlist)
    disclaimer = (
        "This book is a work of fiction. The names, characters, places, and events are products "
        "of the author's imagination or used in a fictitious way. Any resemblance to actual persons, "
        "living or dead, or to real events, is purely coincidental.")
    intro_body = ("<section class=\"page\">\n" + "\n".join(
        ("<p class=\"drop\">%s</p>" % apply_names(h) if i == 0 else "<p>%s</p>" % apply_names(h))
        for i, (plain, h) in enumerate(front)) + "\n</section>\n"
        + '<div class="disclaimer" role="note"><span class="dlabel">A note on this story</span>'
        + '<p>%s</p></div>' % html.escape(disclaimer))
    intro_audio = ("/story/book-three/audio/intro.mp3"
                   if os.path.exists(os.path.join(ROOT, "story", "book-three", "audio", "intro.mp3")) else "")
    write(os.path.join(OUTDIR, "00-intro.html"),
          'order: 0\ncid: intro\nnum: ""\ntitle: "Before We Begin"\n'
          'subtitle: "A dedication, a note, and the songs of this story."\naudio: "%s"' % intro_audio,
          intro_body)

    skipped = [c["num"] for c in chapters if not c["body"]]
    chapters = [c for c in chapters if c["body"]]   # drop empty (unwritten) chapters
    for ch in chapters:
        n = ch["num"]
        pov = apply_names(ch["pov"]) or "Chapter %d" % n
        sub = ch["tag"] or (("%s's chapter" % apply_names(ch["pov"])) if ch["pov"] else "")
        lines = []
        for i, (plain, h) in enumerate(ch["body"]):
            cls = ' class="drop"' if i == 0 else ""
            lines.append("<p%s>%s</p>" % (cls, apply_names(h)))
        body_html = '<section class="page">\n' + "\n".join(lines) + "\n</section>"
        # auto-wire audio if a recorded file exists for this chapter
        afile = os.path.join(ROOT, "story", "book-three", "audio", "ch%d.mp3" % n)
        audio = ("/story/book-three/audio/ch%d.mp3" % n) if os.path.exists(afile) else ""
        fm = ('order: %d\ncid: ch%d\nnum: "%02d"\ntitle: "%s"\nsubtitle: "%s"\naudio: "%s"'
              % (n, n, n, pov.replace('"', "'"), sub.replace('"', "'"), audio))
        write(os.path.join(OUTDIR, "%02d-ch%d.html" % (n, n)), fm, body_html)

    print("wrote intro + %d chapters to %s" % (len(chapters), OUTDIR))
    print("POVs:", [ (c["num"], c["pov"]) for c in chapters ])
    if skipped:
        print("skipped empty chapters:", skipped)

if __name__ == "__main__":
    main()
