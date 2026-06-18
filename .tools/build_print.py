#!/usr/bin/env python3
"""Build a print-ready interior (single HTML) for the KDP paperback.

Reuses the EPUB chapter parsing, lays the book out for a 5.5 x 8.5in trim with
book margins, chapter page-breaks, a running header and page numbers (via
Paged.js), and front matter. Open the output in Chrome and Save as PDF.
Images are embedded (base64) so the file is self-contained.
"""
import os, sys, re, glob, html, base64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_epub import load_chapter, convert, META, DISCLAIMER   # reuse parsing

OUT = os.path.join(ROOT, "dist", "from-bugs-to-brilliance-print.html")
TRIM = ("5.5in", "8.5in")   # KDP trim size

def embed_images(frag):
    def repl(m):
        base = os.path.basename(m.group(1))
        path = os.path.join(ROOT, "story", base)
        if not os.path.exists(path):
            return m.group(0)
        data = base64.b64encode(open(path, "rb").read()).decode()
        return 'src="data:image/jpeg;base64,%s"' % data
    return re.sub(r'src="images/([^"]+)"', repl, frag)

PRINT_CSS = """
@page {
  size: 5.5in 8.5in;
  margin: 0.75in 0.65in 0.8in 0.65in;
  @top-center { content: "From Bugs to Brilliance"; font-family: Georgia, serif; font-style: italic; font-size: 8.5pt; color: #888; }
  @bottom-center { content: counter(page); font-family: Georgia, serif; font-size: 9.5pt; color: #555; }
}
@page :first { @top-center { content: none; } @bottom-center { content: none; } }
@page chapter:first { @top-center { content: none; } }
html { font-size: 11.2pt; }
body { font-family: 'Spectral', Georgia, 'Times New Roman', serif; line-height: 1.55; text-align: left; color: #16181d; margin: 0; }
p { margin: 0 0 0.6em; orphans: 2; widows: 2; }
em { font-style: italic; }
.frontmatter, .chapter { break-before: page; }
/* title + copyright pages */
.titlepage { text-align: center; margin-top: 28%; }
.titlepage h1 { font-size: 26pt; line-height: 1.1; margin: 0; font-family: Georgia, serif; }
.titlepage .sub { font-style: italic; color: #555; margin: 0.7em 0 3em; }
.titlepage .author { font-variant: small-caps; letter-spacing: 0.05em; }
.copyright { margin-top: 38%; font-size: 9.5pt; color: #333; line-height: 1.65; }
.copyright .disc { font-style: italic; color: #555; }
/* chapter head */
.chapter-head { text-align: center; margin: 8% 0 2em; }
.cb-num { font-variant: small-caps; letter-spacing: 0.12em; font-size: 10pt; color: #2a6f4e; }
.cb-title { font-family: Georgia, serif; font-size: 19pt; line-height: 1.15; margin: 0.3em 0; }
.cb-sub { font-style: italic; color: #555; font-size: 11pt; }
.page-marker { display: none; }   /* web scene labels ("Page N · ...") clash with real page numbers in print */
.drop::first-letter { font-size: 3em; font-weight: bold; float: left; line-height: 0.8; padding: 0.06em 0.08em 0 0; color: #2a6f4e; }
.big-quote { font-style: italic; text-align: center; font-size: 13pt; margin: 1.1em 1.2em; }
.incident, .boundary { font-family: 'Courier New', monospace; font-size: 8.6pt; background: #f3f4f6; border: 0.5pt solid #ccd; border-radius: 4pt; padding: 0.5em 0.7em; margin: 1em 0; break-inside: avoid; text-align: left; }
.incident .ln { display: block; white-space: pre-wrap; }
.boundary .bcell { display: inline-block; border: 0.5pt solid #ccd; border-radius: 3pt; padding: 0.1em 0.45em; margin: 0.1em; }
.bcap { font-size: 9pt; font-style: italic; color: #555; }
.note { border-left: 2pt solid #2a6f4e; background: #eef6f1; padding: 0.6em 0.9em; margin: 1em 0; font-size: 10pt; break-inside: avoid; text-align: left; }
.note .nlabel { display: block; font-variant: small-caps; letter-spacing: 0.1em; font-size: 8pt; color: #2a6f4e; }
.cast-row { border-left: 2pt solid #b5852a; background: #faf4e8; padding: 0.5em 0.8em; margin: 0.5em 0; break-inside: avoid; text-align: left; }
.tease { border-left: 2pt solid #5F8CDC; background: #eef2fb; padding: 0.5em 0.8em; margin: 0.5em 0; break-inside: avoid; text-align: left; }
.tease strong, .cast-row strong { display: block; }
.suite { border: 0.5pt solid #ccd; border-radius: 4pt; padding: 0.5em 0.8em; margin: 1em 0; font-size: 10pt; break-inside: avoid; text-align: left; }
.suite-head { display: flex; justify-content: space-between; font-family: 'Courier New', monospace; font-size: 8.2pt; color: #667; border-bottom: 0.5pt solid #ddd; padding-bottom: 0.3em; margin-bottom: 0.4em; }
.badge { font-family: 'Courier New', monospace; font-size: 8pt; color: #2a6f4e; margin-right: 0.4em; }
.next { border-top: 0.5pt solid #ddd; margin-top: 1.2em; padding-top: 0.8em; color: #555; text-align: left; }
.nk { font-variant: small-caps; letter-spacing: 0.1em; font-size: 9pt; color: #2a6f4e; }
.theend { text-align: center; margin-top: 2.5em; }
.theend .tk { font-variant: small-caps; letter-spacing: 0.12em; color: #2a6f4e; display: block; margin-bottom: 0.6em; }
.disclaimer { border: 0.5pt dashed #ccd; border-radius: 4pt; padding: 0.7em 0.9em; margin-top: 1.4em; font-size: 9.5pt; text-align: left; }
.disclaimer .dlabel { display: block; font-variant: small-caps; letter-spacing: 0.1em; font-size: 8pt; color: #888; }
.disclaimer p { font-style: italic; color: #555; }
.ch-illus { margin: 1.2em 0; text-align: center; break-inside: avoid; }
.ch-illus img { max-width: 78%; height: auto; }
/* the on-page rating/contact widget is web-only — never print it */
.feedback { display: none !important; }
"""

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "_chapters", "*.html")))
    chapters = sorted((load_chapter(f) for f in files), key=lambda c: c["order"])

    parts = []
    # title page
    parts.append('<section class="frontmatter titlepage"><h1>%s</h1>'
                 '<p class="sub">%s</p><p class="author">%s</p></section>'
                 % (html.escape(META["title"]), html.escape(META["subtitle"]), html.escape(META["author"])))
    # copyright page
    parts.append('<section class="frontmatter copyright">'
                 '<p><strong>%s</strong></p>'
                 '<p>Copyright &copy; 2026 %s. All rights reserved.</p>'
                 '<p>First edition, 2026.</p>'
                 '<p class="disc">%s</p>'
                 '<p>No part of this book may be reproduced or used in any manner without the '
                 'prior written permission of the author, except for brief quotations in a review.</p>'
                 '</section>'
                 % (html.escape(META["title"]), html.escape(META["author"]), html.escape(DISCLAIMER)))
    # chapters
    for ch in chapters:
        frag, _ = convert(ch["body"])
        frag = embed_images(frag)
        head = '<header class="chapter-head">'
        if ch["num"]:
            head += '<p class="cb-num">Chapter %s</p>' % html.escape(ch["num"])
        head += '<h1 class="cb-title">%s</h1>' % html.escape(ch["title"])
        if ch["subtitle"]:
            head += '<p class="cb-sub">%s</p>' % html.escape(ch["subtitle"])
        head += '</header>'
        parts.append('<section class="chapter">%s%s</section>' % (head, frag))

    doc = ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/>\n'
           '<title>%s — print interior</title>\n'
           '<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">\n'
           '<style>%s</style>\n</head>\n<body>\n%s\n'
           '<script src="https://unpkg.com/pagedjs/dist/paged.polyfill.js"></script>\n'
           '</body></html>\n' % (html.escape(META["title"]), PRINT_CSS, "\n".join(parts)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(doc)
    print("wrote %s (%d KB) — open in Chrome, then Print > Save as PDF" % (OUT, len(doc) // 1024))

if __name__ == "__main__":
    main()
