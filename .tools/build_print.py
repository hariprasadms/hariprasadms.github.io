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

# --- editable front/back matter copy ---
DEDICATION = ("For everyone who has ever whispered “but it works on my machine” — "
              "and stayed to find out why it didn’t.")
ACK = [
    "This book grew out of years of questions, mistakes, and the patient people who turned them into lessons.",
    "My thanks to the mentors who always asked the better question, to the teams who let me break things and learn in the open, and to the testing community whose curiosity never runs dry.",
    "To my family, for the quiet support that made the writing possible — thank you.",
    "And to you, for reading. I hope Arun’s journey leaves you a little more curious than it found you.",
]
GLOSSARY = [
    ("Accessibility", "Making software usable by people with disabilities — for example, those using a screen reader or only a keyboard."),
    ("API", "A direct doorway into a system that other programs use instead of the screen. (“Application Programming Interface.”)"),
    ("Assertion", "The line in a test that decides what counts as a pass. Without it, a test only proves the code didn’t crash."),
    ("Boundary testing", "Checking the values right at a limit — like 0, 1, 50 and 51 — where bugs love to hide."),
    ("Continuous Integration (CI)", "Automatically building and testing every code change as soon as it is added, so problems surface early."),
    ("Flaky test", "A test that passes sometimes and fails other times without the code changing. It quietly destroys trust."),
    ("Functional testing", "Checking whether a feature does what it should — “does it work?”"),
    ("Injection", "An attack that sneaks commands into a form or field to trick the system into doing something it shouldn’t."),
    ("JSON", "A simple text format programs use to send data back and forth."),
    ("Load test", "Checking that software stays fast and stable under a normal busy number of users."),
    ("Negative testing", "Checking that software fails safely when given bad or unexpected input."),
    ("Non-functional testing", "Checking how well software works — speed, scale, security and more — not just whether it works."),
    ("Performance testing", "Making sure software stays fast and steady under real-world use (includes load and stress tests)."),
    ("Positive testing", "Checking that software behaves correctly when given good, expected input."),
    ("Race condition", "A bug that appears only when two things happen at the same moment, in the wrong order."),
    ("Regression testing", "Re-checking that features which used to work still work after a change."),
    ("Reliability", "Staying usable even when a part it depends on breaks — failing gently instead of badly."),
    ("Scalability", "The ability to keep working smoothly as the number of users grows."),
    ("Screen reader", "Software that reads the screen aloud for people who cannot see it."),
    ("Security testing", "Testing software the way an attacker would, to find ways it can be misused."),
    ("Smoke test", "A small, quick set of checks for the most important things. If it fails, stop — the building is on fire."),
    ("Stress test", "Pushing software past its normal limits to learn where it breaks."),
    ("Test automation", "A program that runs the checks for you, instead of a person clicking by hand."),
    ("Test case", "One single check."),
    ("Test suite", "A group of test cases run together."),
]

def find_in_story(base):
    """Find an image by basename anywhere under story/ (handles subfolders like book1_images/)."""
    for root, _, files in os.walk(os.path.join(ROOT, "story")):
        if base in files:
            return os.path.join(root, base)
    return None

def embed_images(frag):
    def repl(m):
        path = find_in_story(os.path.basename(m.group(1)))
        if not path:
            return m.group(0)
        data = base64.b64encode(open(path, "rb").read()).decode()
        return 'src="data:image/jpeg;base64,%s"' % data
    return re.sub(r'src="images/([^"]+)"', repl, frag)

PRINT_CSS = """
@page {
  size: 5.5in 8.5in;
  margin: 0.75in 0.65in 0.8in 0.65in;
  @bottom-center { content: counter(page); font-family: Georgia, serif; font-size: 9.5pt; color: #555; }
}
/* alternating running heads: book title on left pages, chapter title on right */
@page :left  { @top-center { content: "From Bugs to Brilliance"; font-family: Georgia, serif; font-style: italic; font-size: 8.5pt; color: #888; } }
@page :right { @top-center { content: string(chaptitle); font-family: Georgia, serif; font-style: italic; font-size: 8.5pt; color: #888; } }
@page :first { @top-center { content: none; } @bottom-center { content: none; } }
html { font-size: 12.75pt; }
body { font-family: 'Spectral', Georgia, 'Times New Roman', serif; line-height: 1.82; text-align: left; color: #16181d; margin: 0; }
p { margin: 0 0 0.7em; orphans: 2; widows: 2; }
em { font-style: italic; }
.frontmatter { break-before: page; }
.chapter { break-before: recto; }   /* chapters open on a right-hand page (adds tidy blank backs) */
/* title + copyright pages */
.halftitle { text-align: center; margin-top: 40%; }
.halftitle h2 { font-family: Georgia, serif; font-weight: 400; font-size: 17pt; letter-spacing: 0.02em; color: #444; }
.aboutpage p { text-align: justify; font-size: 11pt; line-height: 1.5; }
.aboutpage .bio-tag { text-align: center; font-style: italic; color: #555; font-size: 10.5pt; margin-top: 1.1em; }
.aboutpage .about-connect { text-align: center; margin-top: 1.3em; font-style: italic; color: #666; }
.aboutpage .about-links { text-align: center; margin-top: 0.3em; font-family: Georgia, serif; font-size: 11pt; color: #16181d; }
.about-links .li-logo { vertical-align: -2px; margin-right: 0.35em; }
.titlepage { text-align: center; margin-top: 28%; }
.titlepage h1 { font-size: 26pt; line-height: 1.1; margin: 0; font-family: Georgia, serif; }
.titlepage .sub { font-style: italic; color: #555; margin: 0.7em 0 3em; }
.titlepage .author { font-variant: small-caps; letter-spacing: 0.05em; }
.copyright { margin-top: 38%; font-size: 9.5pt; color: #333; line-height: 1.65; }
.copyright .disc { font-style: italic; color: #555; }
/* chapter head */
.chapter-head { text-align: center; margin: 8% 0 2em; }
.cb-num { font-variant: small-caps; letter-spacing: 0.12em; font-size: 10pt; color: #2a6f4e; }
.cb-title { font-family: Georgia, serif; font-size: 19pt; line-height: 1.15; margin: 0.3em 0; string-set: chaptitle content(); }
.cb-sub { font-style: italic; color: #555; font-size: 11pt; }
.page-marker { display: none; }   /* web scene labels ("Page N · ...") clash with real page numbers in print */
.drop::first-letter { font-size: 3em; font-weight: bold; float: left; line-height: 0.8; padding: 0.06em 0.08em 0 0; color: #2a6f4e; }
.big-quote { font-style: italic; text-align: center; font-size: 13pt; margin: 1.1em 1.2em; }
/* incident = dark terminal/log panel, matching the website */
.incident { font-family: 'Courier New', monospace; background: #101826; color: #C6D0DE; border-radius: 6pt; padding: 0.7em 0.6em; margin: 1em 0; font-size: 6.8pt; line-height: 1.6; break-inside: avoid; text-align: left; }
/* sized so the longest log line (~69 chars) fits on one line; pre-wrap + hanging indent is a safety net */
.incident .ln { display: block; white-space: pre-wrap; padding-left: 1.1em; text-indent: -1.1em; }
.incident .t { color: #6E81A0; }
.incident .err { color: #F0908A; font-weight: 700; }
.incident .warn { color: #E5B567; }
.incident .ok2 { color: #7FD6A8; font-weight: 700; }
.incident .key { color: #8FB7E8; font-weight: 700; }
.incident .purp { color: #B48EF0; font-weight: 700; }
.incident .ok2 { font-weight: 700; }
.keyidea { display: flex; gap: 0.7em; align-items: flex-start; border: 0.5pt solid #1F8A5B; background: #E7F4EE; border-radius: 6pt; padding: 0.7em 0.9em; margin: 1em 0; color: #23503C; break-inside: avoid; text-align: left; }
.keyidea .ki-label { font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 0.1em; text-transform: uppercase; color: #1F8A5B; font-weight: 700; white-space: nowrap; }
.keyidea p { margin: 0; font-size: 10.5pt; }
.incident .crit { color: #fff; background: #C2453A; padding: 0 0.3em; border-radius: 2pt; font-weight: 700; }
/* boundary = light comparison box with tinted cells, matching the website */
.boundary { border: 0.5pt solid #DCE0E6; border-radius: 6pt; padding: 0.8em 0.9em; margin: 1em 0; background: #fff; break-inside: avoid; text-align: left; }
.boundary .blabel { display: block; font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 0.1em; text-transform: uppercase; color: #4A5566; margin-bottom: 0.7em; }
.boundary .bline { display: flex; gap: 2pt; font-family: 'Courier New', monospace; font-size: 8pt; }
.boundary .bcell { flex: 1; text-align: center; padding: 0.4em 0.2em; border-radius: 3pt; font-weight: 700; }
.boundary .bcell.fail { background: #FBEEEC; color: #C2453A; }
.boundary .bcell.pass { background: #E7F4EE; color: #1F8A5B; }
.boundary .bcell.mid { background: #F0F2F5; color: #4A5566; font-weight: 400; }
.bcap { margin-top: 0.6em; font-size: 9pt; font-style: italic; color: #4A5566; }
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
.ch-illus.wide img { max-width: 100%; }
/* the on-page rating/contact widget is web-only — never print it */
.feedback { display: none !important; }
/* scene-break divider between page-sections within a chapter */
.page + .page::before { content: "\2042"; display: block; text-align: center; color: #999; font-size: 12pt; letter-spacing: 0.35em; margin: 0.3em 0 1.2em; }
/* dedication */
.dedication { text-align: center; margin-top: 45%; font-style: italic; color: #444; }
.dedication p { font-size: 12.5pt; line-height: 1.7; }
/* table of contents */
.toc h1 { font-family: Georgia, serif; font-size: 17pt; text-align: center; margin: 8% 0 1.8em; }
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0.7em 0; }
.toc a { display: flex; align-items: baseline; text-decoration: none; color: #16181d; font-size: 11.5pt; }
.toc a .ti { flex: 0 1 auto; }
.toc a .lead { flex: 1 1 auto; border-bottom: 1px dotted #c0c0c0; margin: 0 0.4em; transform: translateY(-0.18em); }
.toc a::after { content: target-counter(attr(href url), page); flex: 0 0 auto; color: #555; }
/* glossary */
.glossary dl { margin: 0; }
.glossary dt { font-weight: 700; font-family: Georgia, serif; margin-top: 0.95em; break-after: avoid; }
.glossary dd { margin: 0.1em 0 0; }
/* acknowledgements */
.acknowledgements p { margin: 0 0 0.7em; }
"""

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "_chapters", "*.html")))
    chapters = sorted((load_chapter(f) for f in files), key=lambda c: c["order"])

    parts = []
    # half-title page (title only)
    parts.append('<section class="frontmatter halftitle"><h2>%s</h2></section>'
                 % html.escape(META["title"]))
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
    # dedication
    parts.append('<section class="frontmatter dedication"><p>%s</p></section>' % html.escape(DEDICATION))
    # table of contents (page numbers resolved by Paged.js target-counter)
    toc_items = []
    for ch in chapters:
        label = (("Chapter %s · " % ch["num"]) if ch["num"] else "") + ch["title"]
        toc_items.append('<li><a href="#toc-%s"><span class="ti">%s</span>'
                         '<span class="lead"></span></a></li>'
                         % (html.escape(ch["cid"]), html.escape(label)))
    parts.append('<section class="frontmatter toc"><h1>Contents</h1><ol>%s</ol></section>'
                 % "".join(toc_items))
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
        parts.append('<section class="chapter" id="toc-%s">%s%s</section>'
                     % (html.escape(ch["cid"]), head, frag))

    # back matter: glossary
    gloss = "".join('<dt>%s</dt><dd>%s</dd>' % (html.escape(t), html.escape(d)) for t, d in GLOSSARY)
    parts.append('<section class="chapter glossary"><header class="chapter-head">'
                 '<h1 class="cb-title">The Testing Ideas in This Book</h1>'
                 '<p class="cb-sub">A plain-English glossary, in alphabetical order.</p></header>'
                 '<dl>%s</dl></section>' % gloss)
    # back matter: acknowledgements
    ack = "".join('<p>%s</p>' % html.escape(p) for p in ACK)
    parts.append('<section class="chapter acknowledgements"><header class="chapter-head">'
                 '<h1 class="cb-title">Acknowledgements</h1></header>%s</section>' % ack)

    # back matter: about the author (LinkedIn only, with logo)
    from build_epub import BIO_PARAS, BIO_TAGLINE
    li_svg = ('<svg class="li-logo" viewBox="0 0 24 24" width="13" height="13" fill="#16181d">'
              '<path d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.07 2.07 0 1 1 0-4.14 2.07 2.07 0 0 1 0 4.14zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>')
    bio_html = "".join("<p>%s</p>" % html.escape(p) for p in BIO_PARAS)
    parts.append('<section class="chapter aboutpage"><header class="chapter-head">'
                 '<h1 class="cb-title">About the Author</h1></header>'
                 '%s'
                 '<p class="bio-tag">%s</p>'
                 '<p class="about-connect">Connect with the author</p>'
                 '<p class="about-links">%s LinkedIn &nbsp;&middot;&nbsp; linkedin.com/in/hariprasadms</p>'
                 '</section>' % (bio_html, html.escape(BIO_TAGLINE), li_svg))

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
