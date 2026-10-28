#!/usr/bin/env python3
"""Keep one header and one footer across every page, and the DogwoofAI name consistent.

The header lives in partials/header.html and the footer in
partials/footer.html. The site has no build step, so this script copies them
into each page, marking the current section in the nav.

    python3 scripts/layout.py           write header and footer into every page
    python3 scripts/layout.py --check   fail if any page differs, links break,
                                        an old contact address remains or the
                                        brand is misspelt
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FOOTER = (ROOT / "partials" / "footer.html").read_text().rstrip("\n")
HEADER = (ROOT / "partials" / "header.html").read_text().rstrip("\n")
BLOCK = re.compile(r'    <footer id="contact">.*?</footer>', re.S)
NAV = re.compile(r'    <nav>.*?</nav>', re.S)
# Pages outside the main nav show the section they belong to.
SECTION = {"lab": "about", "impact": "about"}
OLD_CONTACT = ["andywhittaker@gmail.com", "From Andy Whittaker"]
# The brand is DogwoofAI, one word, distinct from the original Dogwoof.
BAD_BRAND = re.compile(r"Dogwoof[ -]+A[Ii]\b|Dogwoof%20AI")


def header_for(page):
    section = SECTION.get(page.stem, page.stem)
    link = f'<a href="/{section}">'
    if link in HEADER:
        return HEADER.replace(link, f'<a href="/{section}" aria-current="page">', 1)
    return HEADER


def pages():
    return sorted(ROOT.glob("*.html"))


def write():
    for page in pages():
        html = page.read_text()
        if len(BLOCK.findall(html)) != 1 or len(NAV.findall(html)) != 1:
            sys.exit(f"{page.name}: expected exactly one header and one footer")
        html = NAV.sub(lambda _: header_for(page), html)
        page.write_text(BLOCK.sub(lambda _: FOOTER, html))


def check():
    problems = []
    for page in pages():
        html = page.read_text()
        found = BLOCK.findall(html)
        if NAV.findall(html) != [header_for(page)]:
            problems.append(f"{page.name}: header differs from partials/header.html")
        if found != [FOOTER]:
            problems.append(f"{page.name}: footer differs from partials/footer.html")
        for old in OLD_CONTACT:
            if old in html:
                problems.append(f"{page.name}: contains {old!r}")
        for bad in BAD_BRAND.findall(html):
            problems.append(f"{page.name}: unapproved brand spelling {bad!r}")
        for href in re.findall(r'href="(/[^"#?]*)', html):
            target = href.strip("/") or "index"
            if not ((ROOT / f"{target}.html").exists() or (ROOT / target).exists()):
                problems.append(f"{page.name}: broken link {href}")
    for p in problems:
        print(p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    check() if "--check" in sys.argv else write()
