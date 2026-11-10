# Pagey McPageface

![Pagey McPageface, the mascot](pagey-mcpageface-doodle.webp)

**Every page on your site, checked against one rulebook: titles, descriptions, headings, dead links, orphaned pages, and pages saying the same thing twice.**

The people voted, the name stuck, and the audit is deadly serious.

Sites rarely lose search traffic through one big failure. They leak it through a hundred small ones: a title padded with pipes until it clips, the same description pasted onto twelve pages, a good page that nothing anywhere links to, two pages saying the same thing in the same words until a search engine treats them as one. Pagey McPageface is an agent skill that audits **every page on a static site** against a fixed rulebook and reports each violation with the page, the rule, and the evidence.

## The rulebook

- **Titles** at 50–60 characters, **meta descriptions** at 140–160 — long enough to say something, short enough to survive a results page uncut
- **Separators banned** in titles and descriptions: no pipes, no dashes standing in for words (hyphens inside a word are fine)
- **No duplicates**: no two pages may share a title, a description, or an H1
- **Exactly one H1 per page**
- **No internal links to missing pages**
- **No orphaned pages**: every page must be reachable by links from other pages
- **No repeated phrasing**: any two pages sharing more than 15% of their six-word phrases get flagged, and no sentence of ten words or more may appear on two pages
- **Optional forbidden-terms check**: hand it a former brand name or a competitor's and it sweeps every page for them

Every threshold is a command-line flag. If your house style allows 65-character titles, set it once and the audit enforces your rules, not ours.

## Quick start

Requires Python 3.9+, standard library only, nothing to install.

```bash
# Audit a built site directory
python3 scripts/page_audit.py path/to/site/

# Audit specific files, or live URLs
python3 scripts/page_audit.py index.html about.html
python3 scripts/page_audit.py https://example.com/ https://example.com/about/

# House style overrides and brand rules
python3 scripts/page_audit.py site/ --title-min 30 --title-max 65 \
    --forbid "Old Brand Name" --exclude '404.html'

# Machine-readable output for CI
python3 scripts/page_audit.py site/ --json > audit.json
```

Point it at a build output folder (Hugo, Jekyll, Astro, Eleventy, a hand-rolled generator, exported WordPress), a folder of HTML files, or a list of live URLs. Exit status is 0 when no problems are found and 1 when any are, so it drops straight into a build pipeline as a release gate.

## Example output

```
PageyMcPageface audit: 3 pages, 15 problems

Titles (4):
  - /: title is 19 chars (want 50-60): Short | Bad - Title
  - /: pipe or separator dash in title: Short | Bad - Title

Descriptions (2):
  - /: description is 10 chars (want 140-160): Too short.
  - /about/: no meta description

Missing pages (1):
  - /: links to missing page /gone/

Orphans (1):
  - /lonely/: no inbound internal links (orphaned page)
```

## Using it as an agent skill

`SKILL.md` is the skill: the rulebook, when to run it, the six-step audit workflow (get the pages, exclude non-pages, run, read worst-first, fix at the source, re-run and report), and how each check works. Drop the folder into Claude Code, Codex, Cursor, or any agent that reads a SKILL.md, and ask for a site audit.

## Limits, stated plainly

- The audit reads HTML as served or saved. It does not render JavaScript; audit the post-render or built output of a JS-driven site.
- It checks the pages it is given. In URL mode it does not crawl, so an incomplete URL list gives incomplete link and orphan results.
- It judges pages against each other and against the rulebook. It does not fetch search-engine data, and it cannot say which page *should* rank — only which pages are tripping over each other.

## What's inside

- `SKILL.md` — rulebook, workflow, interpretation guide
- `scripts/page_audit.py` — the complete audit as a single stdlib-only Python script
- `LISTING.md` — marketplace listing copy
- `pagey-mcpageface-doodle.webp` — the mascot, because every serious audit tool deserves one
