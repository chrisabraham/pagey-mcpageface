#!/usr/bin/env python3
"""PageyMcPageface — a whole-site page hygiene audit.

Audits a static site directory, individual HTML files, or a list of URLs and
reports the page-level problems that quietly cost a site its search traffic:

  * page titles that are missing, too short, or too long
  * titles and meta descriptions containing separator characters
    (pipes, em/en dashes, free-standing hyphens)
  * meta descriptions that are missing, too short, or too long
  * duplicate titles, descriptions, or H1 text shared by more than one page
  * pages with zero H1s or more than one H1
  * internal links that point at pages which do not exist
  * orphaned pages: published pages no other page links to
  * repeated phrasing: page pairs that share too much of their wording, and
    long sentences repeated verbatim on more than one page
  * optional: forbidden terms appearing anywhere on a page (brand rules,
    competitor names, a former company name, anything you define)

Usage:
    python3 page_audit.py path/to/site/
    python3 page_audit.py page1.html page2.html
    python3 page_audit.py https://example.com/ https://example.com/about/
    python3 page_audit.py site/ --json
    python3 page_audit.py site/ --forbid "Old Brand" --forbid "competitor.com"

Exit status: 0 when no problems are found, 1 when problems are found,
2 on a usage error. Standard library only; no dependencies.

Notes on inputs:
  * Directory mode reads every .html/.htm file under the directory. A file
    named index.html is treated as its folder's page (about/index.html is
    the page /about/).
  * URL mode checks exactly the URLs given. Link, orphan, and duplication
    checks then apply within that set, so pass every page you want judged
    against the others.
"""
import argparse, fnmatch, html, json, os, re, sys
import urllib.parse, urllib.request
from html.parser import HTMLParser

TITLE_MIN, TITLE_MAX = 50, 60
DESC_MIN, DESC_MAX = 140, 160
DUP_THRESHOLD = 0.15          # max share of six-word phrases between two pages
SHINGLE_N = 6                 # phrase length used for duplication checks
MIN_SHINGLES = 10             # pages smaller than this skip the pairwise check
SENTENCE_MIN_WORDS = 10       # sentences this long may not repeat across pages
# A pipe, an em or en dash, or a hyphen used as a separator (hyphens inside a
# word, like "back-of-the-book", are fine).
BANNED = re.compile(r"\||[\u2013\u2014]|(?<!\w)-|-(?!\w)")
SKIP_TAGS = {"script", "style", "pre", "code", "noscript", "template"}
BOILER_TAGS = {"header", "nav", "footer", "aside"}   # excluded from phrasing checks, not from links
BOILER_ROLES = {"navigation", "banner", "contentinfo", "complementary"}


def clean_text(fragment):
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


class PageParser(HTMLParser):
    """Collects title, meta description, H1s, links, and visible body text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts, self.h1_texts, self.links = [], [], []
        self.description = None
        self.h1_count = 0
        self.text_parts = []          # body copy only (boilerplate excluded)
        self.all_text_parts = []      # everything visible (for --forbid)
        self._in_title = False
        self._h1_parts = None
        self._skip = 0                # depth inside script/style/pre/code
        self._stack = []              # (tag, is_boilerplate) for open elements
        self._boiler = 0              # depth inside header/nav/footer/aside

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP_TAGS:
            self._skip += 1
        if tag not in ("meta", "link", "br", "img", "hr", "input", "source", "wbr"):
            boiler = tag in BOILER_TAGS or a.get("role", "").lower() in BOILER_ROLES
            self._stack.append((tag, boiler))
            if boiler:
                self._boiler += 1
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and a.get("name", "").lower() == "description":
            self.description = a.get("content", "")
        elif tag == "h1":
            self.h1_count += 1
            self._h1_parts = []
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                for _, boiler in self._stack[i:]:
                    if boiler and self._boiler:
                        self._boiler -= 1
                del self._stack[i:]
                break
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1_parts is not None:
            self.h1_texts.append(clean_text(" ".join(self._h1_parts)))
            self._h1_parts = None

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if self._h1_parts is not None:
            self._h1_parts.append(data)
        if not self._skip:
            self.all_text_parts.append(data)
            if not self._boiler:
                self.text_parts.append(data)


def canon(path):
    """Canonical page key: /about/index.html, /about and /about/ are one page."""
    path = urllib.parse.unquote(path or "/")
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    elif path.endswith("/index.htm"):
        path = path[: -len("index.htm")]
    if not path.startswith("/"):
        path = "/" + path
    if "." not in path.rsplit("/", 1)[-1] and not path.endswith("/"):
        path += "/"
    return path


class Page:
    def __init__(self, key, source, raw):
        p = PageParser()
        p.feed(raw)
        p.close()
        self.key, self.source = key, source
        self.title = clean_text(" ".join(p.title_parts))
        self.description = clean_text(p.description) if p.description is not None else None
        self.h1_count, self.h1_texts = p.h1_count, p.h1_texts
        self.links = p.links
        body = clean_text(" ".join(p.text_parts))
        self.all_text = clean_text(" ".join(p.all_text_parts))
        words = re.findall(r"[a-z0-9']+", body.lower())
        self.word_count = len(words)
        self.shingles = {" ".join(words[i:i + SHINGLE_N]) for i in range(len(words) - SHINGLE_N + 1)}
        self.sentences = {}
        for s in re.split(r"(?<=[.!?])\s+", body):
            s = s.strip()
            if len(s.split()) >= SENTENCE_MIN_WORDS:
                self.sentences[s] = True


def load_targets(targets, excludes):
    """Returns (pages, file_exists, hosts): hosts are the site hosts seen in
    URL targets, used to tell internal absolute links from external ones."""
    pages, disk_root, hosts = {}, None, set()

    def wanted(rel):
        return not any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch("/" + rel, pat) for pat in excludes)

    for target in targets:
        if target.startswith(("http://", "https://")):
            req = urllib.request.Request(target, headers={"User-Agent": "PageyMcPageface/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8", "replace")
                final = r.geturl()
            fp = urllib.parse.urlparse(final)
            hosts.add(fp.netloc.lower())
            pages[canon(fp.path)] = Page(canon(fp.path), target, raw)
        elif os.path.isdir(target):
            disk_root = os.path.abspath(target)
            for root, dirs, names in os.walk(target):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for name in names:
                    if not name.lower().endswith((".html", ".htm")):
                        continue
                    full = os.path.join(root, name)
                    rel = os.path.relpath(full, target).replace(os.sep, "/")
                    if not wanted(rel):
                        continue
                    raw = open(full, encoding="utf-8", errors="replace").read()
                    key = canon("/" + rel)
                    pages[key] = Page(key, rel, raw)
        elif os.path.isfile(target):
            raw = open(target, encoding="utf-8", errors="replace").read()
            key = canon("/" + os.path.basename(target))
            pages[key] = Page(key, target, raw)
        else:
            raise SystemExit(f"error: no such file, directory, or URL: {target}")

    def file_exists(path):
        if disk_root is None:
            return False
        return os.path.isfile(os.path.join(disk_root, urllib.parse.unquote(path).lstrip("/")))

    return pages, file_exists, hosts


def looks_like_page(path):
    last = path.rsplit("/", 1)[-1]
    return "." not in last or last.lower().endswith((".html", ".htm"))


def audit(pages, file_exists, hosts, args):
    problems = []   # (section, message)
    add = problems.append

    for key in sorted(pages):
        pg = pages[key]
        t, d = pg.title, pg.description
        if not t:
            add(("Titles", f"{key}: no <title>"))
        else:
            if not args.title_min <= len(t) <= args.title_max:
                add(("Titles", f"{key}: title is {len(t)} chars (want {args.title_min}-{args.title_max}): {t}"))
            if BANNED.search(t):
                add(("Titles", f"{key}: pipe or separator dash in title: {t}"))
        if d is None or d == "":
            add(("Descriptions", f"{key}: no meta description"))
        else:
            if not args.desc_min <= len(d) <= args.desc_max:
                add(("Descriptions", f"{key}: description is {len(d)} chars (want {args.desc_min}-{args.desc_max}): {d}"))
            if BANNED.search(d):
                add(("Descriptions", f"{key}: pipe or separator dash in description: {d}"))
        if pg.h1_count != 1:
            add(("Headings", f"{key}: {pg.h1_count} H1 elements (want exactly 1)"))
        for term in args.forbid:
            if re.search(re.escape(term), pg.all_text + " " + pg.title + " " + (d or ""), re.I):
                add(("Forbidden terms", f"{key}: contains forbidden term {term!r}"))

    for label, pick in (("title", lambda p: p.title),
                        ("description", lambda p: p.description),
                        ("H1", lambda p: p.h1_texts[0] if p.h1_texts else "")):
        seen = {}
        for key in sorted(pages):
            val = pick(pages[key])
            if val:
                seen.setdefault(val, []).append(key)
        for val, keys in seen.items():
            if len(keys) > 1:
                add(("Duplicates", f"duplicate {label} on {', '.join(keys)}: {val[:90]}"))

    # Link graph: missing targets and orphans.
    inbound = {key: set() for key in pages}
    for key in sorted(pages):
        pg = pages[key]
        base = key if key.endswith("/") else key.rsplit("/", 1)[0] + "/"
        for href in pg.links:
            href = href.strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                continue
            parts = urllib.parse.urlparse(href)
            if parts.netloc:
                # Absolute or protocol-relative URL: internal only when its
                # host is one of the audited site's hosts (URL mode). In file
                # and directory mode there is no host to match, so absolute
                # links are treated as external and left alone.
                if parts.netloc.lower() not in hosts:
                    continue
                target = canon(parts.path)
            else:
                joined = urllib.parse.urljoin(base, href)
                target = canon(urllib.parse.urlparse(joined).path)
            if target == key:
                continue
            if target in pages:
                inbound[target].add(key)
            elif looks_like_page(target) and not file_exists(target):
                # In URL mode a same-site link outside the fetched set is
                # reported too: the set defines what "exists".
                add(("Missing pages", f"{key}: links to missing page {target}"))
    for key in sorted(pages):
        if key != "/" and not inbound[key]:
            add(("Orphans", f"{key}: no inbound internal links (orphaned page)"))

    keys = sorted(pages)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            sa, sb = pages[a].shingles, pages[b].shingles
            small = min(len(sa), len(sb))
            if small < MIN_SHINGLES:
                continue
            share = len(sa & sb) / small
            if share > args.dup_threshold:
                add(("Repeated phrasing",
                     f"{a} and {b} share {share:.0%} of their six-word phrases (limit {args.dup_threshold:.0%})"))
    sent = {}
    for key in keys:
        for s in pages[key].sentences:
            sent.setdefault(s, []).append(key)
    for s, where in sent.items():
        if len(where) > 1:
            add(("Repeated phrasing", f"sentence repeated on {', '.join(where)}: {s[:80]}"))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit a site's pages for title, description, "
                                                 "heading, link, orphan, and duplication problems.")
    ap.add_argument("targets", nargs="+", help="site directory, HTML files, or page URLs")
    ap.add_argument("--title-min", type=int, default=TITLE_MIN)
    ap.add_argument("--title-max", type=int, default=TITLE_MAX)
    ap.add_argument("--desc-min", type=int, default=DESC_MIN)
    ap.add_argument("--desc-max", type=int, default=DESC_MAX)
    ap.add_argument("--dup-threshold", type=float, default=DUP_THRESHOLD,
                    help="max share of six-word phrases allowed between two pages (default 0.15)")
    ap.add_argument("--forbid", action="append", default=[], metavar="TERM",
                    help="forbidden term (brand rule); may be repeated")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                    help="path glob to skip in directory mode, e.g. '404.html'; may be repeated")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        pages, file_exists, hosts = load_targets(args.targets, args.exclude)
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not pages:
        print("error: no pages found in the given targets", file=sys.stderr)
        return 2

    problems = audit(pages, file_exists, hosts, args)
    if args.json:
        out = {"pages": len(pages), "problem_count": len(problems),
               "problems": [{"section": s, "message": m} for s, m in problems]}
        print(json.dumps(out, indent=2))
    else:
        print(f"PageyMcPageface audit: {len(pages)} pages, {len(problems)} problems")
        order = ["Titles", "Descriptions", "Headings", "Duplicates", "Forbidden terms",
                 "Missing pages", "Orphans", "Repeated phrasing"]
        grouped = {}
        for s, m in problems:
            grouped.setdefault(s, []).append(m)
        for s in order + [k for k in grouped if k not in order]:
            if s in grouped:
                print(f"\n{s} ({len(grouped[s])}):")
                for m in grouped[s]:
                    print(f"  - {m}")
        if not problems:
            print("\nNo problems found. Every page passes.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
