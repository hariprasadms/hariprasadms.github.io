#!/usr/bin/env python3
"""Render the print-interior HTML to a KDP-ready PDF via headless Chromium.

KDP does NOT run JavaScript, so the HTML must NOT be uploaded directly — its
Paged.js layout (page size, breaks, headers, page numbers) would be stripped.
This renders the HTML through headless Chrome (which DOES run Paged.js) and
saves a fixed-layout PDF to upload to KDP.

Usage (needs the venv with playwright + chromium):
    .venv-docx/bin/python .tools/build_print.py        # build the HTML
    .venv-docx/bin/python .tools/render_print_pdf.py   # HTML -> PDF
"""
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "dist", "from-bugs-to-brilliance-print.html")
PDF = os.path.join(ROOT, "dist", "from-bugs-to-brilliance-print.pdf")

def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + HTML, wait_until="networkidle", timeout=120000)
        pg.wait_for_function("document.querySelectorAll('.pagedjs_page').length > 50", timeout=120000)
        pg.wait_for_timeout(3000)   # let Paged.js settle running heads / page numbers
        n = pg.evaluate("document.querySelectorAll('.pagedjs_page').length")
        pg.pdf(path=PDF, prefer_css_page_size=True, print_background=True)
        b.close()
    print("wrote %s (%d pages, %d KB)" % (PDF, n, os.path.getsize(PDF) // 1024))

if __name__ == "__main__":
    main()
