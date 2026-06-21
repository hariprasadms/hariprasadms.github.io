#!/usr/bin/env python3
"""Build a clean EPUB 3 of "From Bugs to Brilliance" from the chapter sources.

Reads _chapters/*.html, strips web-only markup (player/nav) and the interactive
feedback widget, rewrites the HTML into well-formed XHTML, bundles the cover and
the chapter illustration, and writes dist/from-bugs-to-brilliance.epub.
"""
import os, re, html, zipfile, glob
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dist", "from-bugs-to-brilliance.epub")

META = {
    "title": "From Bugs to Brilliance",
    "subtitle": "A Story of Software Testing",
    "author": "Hariprasad Srinivas",
    "lang": "en",
    "desc": ("A story-driven book that teaches software testing from first "
             "principles to the age of AI. Follow Arun from breaking production "
             "to mastering quality."),
    "modified": "2026-06-16T00:00:00Z",
    "id": "urn:uuid:fbtb-hariprasadms-2026-06",
}

DISCLAIMER = ("This book is a work of fiction. The names, characters, companies, places, and events are "
              "either products of the author's imagination or used in a fictitious way. Any resemblance to "
              "actual people — living or dead — real companies, or real events is entirely coincidental.")
BIO_PARAS = [
    "Hariprasad is a writer, software architect, and mentor who believes that the most powerful ideas "
    "are the ones explained in the simplest way. With nearly two decades of experience in the IT industry "
    "since 2006, he has worked with a wide range of technologies, tools, and teams while helping "
    "organizations build quality software and helping individuals build successful careers.",
    "A passionate learner and teacher, Hariprasad has guided many students and professionals in the field "
    "of software testing and technology. Over the years, he has read extensively across technical subjects, "
    "personal development, and storytelling, developing a deep appreciation for books that educate, inspire, "
    "and leave a lasting impact on readers.",
    "Through his writing, Hariprasad aims to turn complex ideas into engaging stories that anyone can "
    "understand. Whether writing technical guides, fiction, or motivational books, his goal remains the "
    "same — to teach something meaningful, spark new thinking, and create stories that stay with readers "
    "long after the final page.",
]
BIO_TAGLINE = "Author • Software Architect • Mentor • Storyteller"
BIO = BIO_PARAS[0]   # short single-paragraph form, kept for any back-compat use
CONNECT = "Connect on LinkedIn: linkedin.com/in/hariprasadms"

VOID = {"br", "img", "hr", "meta", "link", "col", "source", "track", "wbr", "area", "base", "input"}
EXCLUDE_CLASS = {"feedback"}          # interactive widget — drop from the book
DROP_ATTRS = {"loading", "style", "contenteditable", "tabindex"}

def load_chapter(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    fm, body = (m.group(1), m.group(2)) if m else ("", raw)
    def field(name):
        mm = re.search(r'^%s:\s*"?(.*?)"?\s*$' % name, fm, re.M)
        return (mm.group(1) if mm else "").replace('\\"', '"')
    order = field("order")
    return {
        "order": int(order) if order.strip() else 999,
        "cid": field("cid"), "num": field("num"),
        "title": field("title"), "subtitle": field("subtitle"),
        "body": body,
    }

class XHTML(HTMLParser):
    """Re-emit an HTML fragment as well-formed XHTML, dropping excluded subtrees."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.stack, self.skip_depth, self.images = [], [], None, set()
    def _attrs(self, tag, attrs):
        s = ""
        for k, v in attrs:
            if k in DROP_ATTRS or k.startswith("data-"):
                continue
            if v is None:
                s += " " + k; continue
            if tag == "img" and k == "src":
                base = os.path.basename(v); v = "images/" + base; self.images.add(base)
            s += ' %s="%s"' % (k, html.escape(v, quote=True))
        return s
    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if self.skip_depth is None:
                self.out.append("<%s%s/>" % (tag, self._attrs(tag, attrs)))
            return
        cls = dict(attrs).get("class", "")
        start_skip = self.skip_depth is None and bool(set(cls.split()) & EXCLUDE_CLASS)
        self.stack.append(tag)
        if self.skip_depth is not None:
            return
        if start_skip:
            self.skip_depth = len(self.stack); return
        self.out.append("<%s%s>" % (tag, self._attrs(tag, attrs)))
    def handle_startendtag(self, tag, attrs):
        if self.skip_depth is None and tag in VOID:
            self.out.append("<%s%s/>" % (tag, self._attrs(tag, attrs)))
    def handle_endtag(self, tag):
        if tag in VOID:
            return
        depth = len(self.stack)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif self.stack:
            self.stack.pop()
        if self.skip_depth is not None:
            if depth == self.skip_depth:
                self.skip_depth = None
            return
        self.out.append("</%s>" % tag)
    def handle_data(self, d):
        if self.skip_depth is None:
            self.out.append(html.escape(d, quote=False))

def convert(body):
    p = XHTML(); p.feed(body); p.close()
    return "".join(p.out), p.images

XHTML_HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n'
              '<!DOCTYPE html>\n'
              '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n'
              '<head><meta charset="utf-8"/><title>%s</title>'
              '<link rel="stylesheet" type="text/css" href="style.css"/></head>\n<body>\n')

def chapter_xhtml(ch):
    frag, imgs = convert(ch["body"])
    head = '<header class="chapter-head">'
    if ch["num"]:
        head += '<p class="cb-num">Chapter %s</p>' % html.escape(ch["num"])
    head += '<h1 class="cb-title">%s</h1>' % html.escape(ch["title"])
    if ch["subtitle"]:
        head += '<p class="cb-sub">%s</p>' % html.escape(ch["subtitle"])
    head += "</header>\n"
    doc = (XHTML_HEAD % html.escape(ch["title"])) + head + frag + "\n</body></html>\n"
    return doc, imgs

STYLE = """\
body{font-family:Georgia,'Spectral',serif;line-height:1.62;margin:1em;color:#1c2430;}
h1.cb-title{font-size:1.7em;line-height:1.12;margin:.1em 0 .3em;}
.chapter-head{margin-bottom:1.4em;border-bottom:1px solid #e1e4ea;padding-bottom:1em;}
.cb-num{font-family:'Courier New',monospace;font-size:.72em;letter-spacing:.16em;text-transform:uppercase;color:#1F8A5B;margin:0;}
.cb-sub{font-style:italic;color:#566;margin:.2em 0 0;}
p{margin:.75em 0;}
.page-marker{font-family:'Courier New',monospace;font-size:.68em;letter-spacing:.12em;text-transform:uppercase;color:#8a93a0;margin:1.6em 0 .3em;}
.drop::first-letter{font-size:2.6em;font-weight:bold;line-height:.78;float:left;padding:.05em .08em 0 0;color:#1F8A5B;}
.big-quote{font-size:1.18em;font-style:italic;text-align:center;margin:1.1em 1em;color:#243;}
.say{font-style:italic;}
.incident,.boundary{font-family:'Courier New',monospace;font-size:.8em;background:#f4f5f7;border:1px solid #dde;border-radius:6px;padding:.6em .8em;margin:1.1em 0;}
.incident .ln{display:block;white-space:pre-wrap;}
.incident .t{color:#667}.incident .err{color:#C2453A;font-weight:700}.incident .warn{color:#9A6B00}
.incident .ok2{color:#1F8A5B;font-weight:700}.incident .key{color:#2F6FD0;font-weight:700}.incident .purp{color:#7A3FD0;font-weight:700}
.keyidea{display:flex;gap:.7em;align-items:flex-start;border:1px solid #1F8A5B;background:#E7F4EE;border-radius:6px;padding:.7em 1em;margin:1.1em 0;color:#23503C;}
.keyidea .ki-label{font-family:'Courier New',monospace;font-size:.7em;letter-spacing:.1em;text-transform:uppercase;color:#1F8A5B;font-weight:700;white-space:nowrap;}
.keyidea p{margin:0;}
.boundary .blabel{display:block;font-size:.85em;color:#667;margin-bottom:.4em;}
.boundary .bline{display:block;}
.boundary .bcell{display:inline-block;border:1px solid #ccd;border-radius:4px;padding:.15em .5em;margin:.1em;}
.bcap{font-size:.85em;color:#667;font-style:italic;margin-top:.5em;}
.note{border-left:3px solid #1F8A5B;background:#E7F4EE;border-radius:0 6px 6px 0;padding:.7em 1em;margin:1.1em 0;color:#23503C;}
.note .nlabel{display:block;font-family:'Courier New',monospace;font-size:.68em;letter-spacing:.12em;text-transform:uppercase;color:#1F8A5B;margin-bottom:.25em;}
.cast-row{border-left:3px solid #C98A2D;background:#fbf4e8;border-radius:0 6px 6px 0;padding:.6em .9em;margin:.6em 0;}
.tease{border-left:3px solid #5F8CDC;background:#eef2fb;border-radius:0 6px 6px 0;padding:.6em .9em;margin:.6em 0;}
.tease strong,.cast-row strong{display:block;}
.suite{border:1px solid #dde;border-radius:6px;padding:.5em .8em;margin:1.1em 0;font-size:.92em;}
.suite-head{display:flex;justify-content:space-between;font-family:'Courier New',monospace;font-size:.8em;color:#667;border-bottom:1px solid #eee;padding-bottom:.3em;margin-bottom:.4em;}
.case{margin:.35em 0;}
.badge{font-family:'Courier New',monospace;font-size:.7em;color:#1F8A5B;margin-right:.4em;}
.next{border-top:1px solid #e1e4ea;margin-top:1.4em;padding-top:.9em;color:#566;}
.nk{font-family:'Courier New',monospace;font-size:.72em;letter-spacing:.12em;text-transform:uppercase;color:#1F8A5B;}
.theend{text-align:center;border:1px solid #dde;border-radius:8px;padding:1.6em;margin-top:2.2em;background:#fafbfc;}
.theend .tk{font-family:'Courier New',monospace;font-size:.72em;letter-spacing:.16em;text-transform:uppercase;color:#1F8A5B;display:block;margin-bottom:.6em;}
.disclaimer{border:1px dashed #ccd;border-radius:6px;padding:.8em 1em;margin-top:1.6em;}
.disclaimer .dlabel{display:block;font-family:'Courier New',monospace;font-size:.66em;letter-spacing:.12em;text-transform:uppercase;color:#889;margin-bottom:.3em;}
.disclaimer p{font-style:italic;color:#566;font-size:.9em;margin:0;}
.ch-illus{margin:1.4em 0;}
.ch-illus img,img{max-width:100%;height:auto;}
.ch-illus img{display:block;margin:0 auto;border-radius:8px;}
.ch-illus.wide img{max-width:100%;}
.titlepage{text-align:center;margin-top:22%;}
.tp-title{font-size:2.1em;line-height:1.1;margin:0;}
.tp-sub{font-style:italic;color:#566;margin:.6em 0 2.4em;}
.tp-author{font-family:'Courier New',monospace;letter-spacing:.06em;color:#243;}
.copyright{font-size:.86em;color:#445;margin-top:12%;line-height:1.7;}
.copyright .cr-title{font-weight:bold;}
.copyright .cr-disc{font-style:italic;color:#566;}
.about h2{font-size:1.4em;}
.about p{text-align:left;}
.about .bio-tag{text-align:center;font-style:italic;color:#566;margin-top:1.2em;}
.about-links{font-family:'Courier New',monospace;font-size:.82em;color:#1F8A5B;margin-top:0.6em;text-align:center;}
"""

COVER_XHTML = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
               '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"><head>'
               '<meta charset="utf-8"/><title>Cover</title>'
               '<style>html,body{margin:0;padding:0;}img{max-width:100%;height:auto;display:block;margin:0 auto;}</style>'
               '</head><body><img src="images/cover.jpg" alt="From Bugs to Brilliance"/></body></html>\n')

def page(title, body):
    return (XHTML_HEAD % html.escape(title)) + body + "\n</body></html>\n"

def front_back_pages():
    e = html.escape
    title_pg = page("Title", (
        '<div class="titlepage">'
        '<h1 class="tp-title">%s</h1>'
        '<p class="tp-sub">%s</p>'
        '<p class="tp-author">%s</p>'
        '</div>') % (e(META["title"]), e(META["subtitle"]), e(META["author"])))
    copyright_pg = page("Copyright", (
        '<div class="copyright">'
        '<p class="cr-title">%s</p>'
        '<p>Copyright © 2026 %s. All rights reserved.</p>'
        '<p>First edition, 2026.</p>'
        '<p class="cr-disc">%s</p>'
        '<p>No part of this book may be reproduced or used in any manner without the prior written '
        'permission of the author, except for brief quotations in a review.</p>'
        '</div>') % (e(META["title"]), e(META["author"]), e(DISCLAIMER)))
    bio_html = "".join("<p>%s</p>" % e(p) for p in BIO_PARAS)
    about_pg = page("About the Author", (
        '<div class="about">'
        '<h2>About the Author</h2>'
        '%s'
        '<p class="bio-tag">%s</p>'
        '<p class="about-links">%s</p>'
        '</div>') % (bio_html, e(BIO_TAGLINE), e(CONNECT)))
    return title_pg, copyright_pg, about_pg

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "_chapters", "*.html")))
    chapters = sorted((load_chapter(f) for f in files), key=lambda c: c["order"])

    docs, all_imgs = [], set()
    for ch in chapters:
        doc, imgs = chapter_xhtml(ch)
        # validate well-formedness (parse body, ignoring the DOCTYPE line)
        frag = doc.split("<!DOCTYPE html>\n", 1)[1]
        ET.fromstring(frag)
        docs.append((ch, doc)); all_imgs |= imgs
    print("chapters: %d | embedded images: %s" % (len(docs), sorted(all_imgs)))

    title_pg, copyright_pg, about_pg = front_back_pages()
    for d in (title_pg, copyright_pg, about_pg):
        ET.fromstring(d.split("<!DOCTYPE html>\n", 1)[1])   # validate

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    manifest, spine, navlis, navpoints = [], [], [], []

    # front matter: cover, title page, copyright
    manifest.append('<item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
    manifest.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
    manifest.append('<item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/>')
    manifest.append('<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml"/>')
    spine.append('<itemref idref="cover" linear="yes"/>')
    spine.append('<itemref idref="titlepage"/>')
    spine.append('<itemref idref="copyright"/>')

    for i, (ch, _) in enumerate(docs):
        iid = "chap-" + ch["cid"]
        manifest.append('<item id="%s" href="%s.xhtml" media-type="application/xhtml+xml"/>' % (iid, iid))
        spine.append('<itemref idref="%s"/>' % iid)
        label = html.escape((("Chapter " + ch["num"] + " · ") if ch["num"] else "") + ch["title"])
        navlis.append('<li><a href="%s.xhtml">%s</a></li>' % (iid, label))
        navpoints.append('<navPoint id="np%d" playOrder="%d"><navLabel><text>%s</text></navLabel>'
                         '<content src="%s.xhtml"/></navPoint>' % (i + 1, i + 1, label, iid))

    # back matter: about the author
    manifest.append('<item id="about" href="about.xhtml" media-type="application/xhtml+xml"/>')
    spine.append('<itemref idref="about"/>')
    navlis.append('<li><a href="about.xhtml">About the Author</a></li>')
    navpoints.append('<navPoint id="np-about" playOrder="%d"><navLabel><text>About the Author</text>'
                     '</navLabel><content src="about.xhtml"/></navPoint>' % (len(docs) + 1))

    # extra (non-cover) images
    for img in sorted(all_imgs):
        if img == "cover.jpg":
            continue
        mt = "image/jpeg" if img.lower().endswith((".jpg", ".jpeg")) else "image/png"
        manifest.append('<item id="img-%s" href="images/%s" media-type="%s"/>'
                        % (re.sub(r"\W", "_", img), img, mt))

    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
           '<dc:identifier id="bookid">%(id)s</dc:identifier>\n'
           '<dc:title>%(title)s</dc:title>\n'
           '<dc:creator>%(author)s</dc:creator>\n'
           '<dc:language>%(lang)s</dc:language>\n'
           '<dc:description>%(desc)s</dc:description>\n'
           '<meta property="dcterms:modified">%(modified)s</meta>\n'
           '<meta name="cover" content="cover-img"/>\n'
           '</metadata>\n<manifest>\n'
           '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
           '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
           '<item id="css" href="style.css" media-type="text/css"/>\n'
           + "\n".join(manifest) +
           '\n</manifest>\n<spine toc="ncx">\n' + "\n".join(spine) +
           '\n</spine>\n<guide><reference type="cover" title="Cover" href="cover.xhtml"/></guide>\n</package>\n'
           ) % {k: html.escape(v) for k, v in META.items()}

    nav = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
           '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">\n'
           '<head><meta charset="utf-8"/><title>Contents</title></head><body>\n'
           '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>\n' + "\n".join(navlis) +
           '\n</ol></nav>\n'
           '<nav epub:type="landmarks" id="landmarks" hidden="hidden"><h2>Guide</h2><ol>\n'
           '<li><a epub:type="cover" href="cover.xhtml">Cover</a></li>\n'
           '<li><a epub:type="toc" href="nav.xhtml">Table of Contents</a></li>\n'
           '<li><a epub:type="bodymatter" href="chap-intro.xhtml">Begin Reading</a></li>\n'
           '</ol></nav>\n</body></html>\n')

    ncx = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
           '<head><meta name="dtb:uid" content="%s"/></head>\n'
           '<docTitle><text>%s</text></docTitle>\n<navMap>\n'
           % (html.escape(META["id"]), html.escape(META["title"]))
           + "\n".join(navpoints) + '\n</navMap>\n</ncx>\n')

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?>\n<container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                   '<rootfiles><rootfile full-path="OEBPS/content.opf" '
                   'media-type="application/oebps-package+xml"/></rootfiles>\n</container>\n')
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/toc.ncx", ncx)
        z.writestr("OEBPS/style.css", STYLE)
        z.writestr("OEBPS/cover.xhtml", COVER_XHTML)
        z.writestr("OEBPS/titlepage.xhtml", title_pg)
        z.writestr("OEBPS/copyright.xhtml", copyright_pg)
        z.writestr("OEBPS/about.xhtml", about_pg)
        for ch, doc in docs:
            z.writestr("OEBPS/chap-%s.xhtml" % ch["cid"], doc)
        for img in sorted(all_imgs | {"cover.jpg"}):   # always include the cover
            src = None
            for root, _, files in os.walk(os.path.join(ROOT, "story")):  # handles subfolders
                if img in files:
                    src = os.path.join(root, img); break
            if src:
                z.write(src, "OEBPS/images/" + img)
            else:
                print("WARNING: image not found, skipped:", img)

    print("wrote %s (%d KB)" % (OUT, os.path.getsize(OUT) // 1024))

if __name__ == "__main__":
    main()
