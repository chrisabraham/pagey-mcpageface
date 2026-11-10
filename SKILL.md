---
name: PageyMcPageface
description: Whole-site page hygiene audit for static sites. Checks every page's title and meta description length and characters, duplicate titles/descriptions/H1s, pages with zero or multiple H1s, internal links to missing pages, orphaned pages with no inbound links, and repeated boilerplate phrasing across pages. Use when a user asks for an SEO audit, a site quality check, a pre-launch or post-migration review, or why pages are not ranking or indexing.
---

# PageyMcPageface — whole-site page hygiene audit

A site rarely loses search traffic through one big failure. It leaks through
a hundred small ones: titles clipped or padded with separators, the same
description pasted on twelve pages, a page nothing links to, two pages
saying the same thing in the same words. PageyMcPageface audits **every
page on a site against one rulebook** and reports each violation with the
page, the rule, and the evidence, so the fixes are mechanical.

It works on any static site: a build output folder (Hugo, Jekyll, Astro,
Eleventy, a hand-rolled generator, exported WordPress), a folder of HTML
files, or a list of live page URLs.

## The rulebook

| Rule | Default | Why |
|---|---|---|
| Title length | 50–60 characters | Long enough to say something specific, short enough to survive a results page uncut |
| Meta description length | 140–160 characters | Fills the snippet without truncation |
| Separators banned in titles and descriptions | No `\|`, no em/en dashes, no free-standing hyphens (hyphens inside a word, as in *back-of-the-book*, are fine) | Separators are filler that eats the character budget and reads as boilerplate |
| Titles, descriptions, and H1 text unique across the site | No duplicates | Duplicates force search engines to guess which page a query belongs to |
| Exactly one H1 per page | 1 | Zero leaves the page topic unstated; two or more splits it |
| No internal links to missing pages | Zero broken internal links | Every dead internal link wastes crawl and strands visitors |
| No orphaned pages | Every page (except the home page) has at least one inbound internal link | A page nothing links to is a page crawlers and visitors rarely find |
| Phrasing overlap between any two pages | At most 15% shared six-word phrases, measured against the smaller page | Near-duplicate pages compete with each other and get treated as duplicates |
| Repeated sentences | No sentence of 10+ words may appear on more than one page | Verbatim repetition is the clearest near-duplicate signal there is |
| Forbidden terms (optional) | Your list | Catches a former brand name, a competitor's name, a partner's trademark, or any term a site has ruled off its own pages |

Thresholds are defaults from practice, not laws. Every one is a command-line
flag; a user with a different house style sets their own numbers once and
the audit enforces those.

## When to use this skill

- A user asks for an SEO audit, technical SEO check, or site review.
- Before a launch, redesign, or platform migration goes live, and again
  after, to compare.
- Rankings or impressions dropped and the cause is not obvious.
- A site has grown by accretion and nobody knows what is actually on it.
- As a release gate: run it in CI and fail the build on problems, the same
  way a linter gates code.

## The audit workflow

1. **Get the pages.** Prefer the built output directory over crawling: it
   is complete, fast, and exactly what will ship. Use URL mode when there
   is no local build, and pass every URL to be judged — link, orphan, and
   duplication checks only see the set they are given.
2. **Exclude non-pages.** Error pages, print views, and source fragments
   are not pages. Use `--exclude` for them (for example `--exclude '404.html'`)
   rather than letting them pollute the report. If the directory contains a
   generator's source files alongside its output, audit the output only.
3. **Run the script** (below). Add `--forbid "Term"` once per forbidden
   term if the site has brand rules.
4. **Read the report by section, worst first.** Missing pages and orphans
   are structural and outrank wording. Duplicates and repeated phrasing
   come next. Title and description lengths are the polish layer.
5. **Fix at the source, never in the output.** If pages are generated, fix
   the template or the source file and rebuild. Editing built HTML by hand
   is a fix that evaporates on the next build.
6. **Re-run until it exits 0**, or until every remaining problem is a
   deliberate exception you can name (an error page with a short title is
   the classic one). Report the final counts to the user: pages audited,
   problems found, problems fixed, exceptions kept and why.

## Running the script

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

# Machine-readable output for CI or a report file
python3 scripts/page_audit.py site/ --json > audit.json
```

Exit status is 0 when no problems are found and 1 when any are, so the
script drops straight into a build pipeline or a pre-push hook.

### Options

| Flag | Default | Meaning |
|---|---|---|
| `--title-min`, `--title-max` | 50, 60 | Allowed title length in characters |
| `--desc-min`, `--desc-max` | 140, 160 | Allowed meta description length |
| `--dup-threshold` | 0.15 | Max share of six-word phrases allowed between two pages |
| `--forbid TERM` | none | Forbidden term; repeat for several |
| `--exclude GLOB` | none | Skip matching paths in directory mode; repeat for several |
| `--json` | off | Emit the report as JSON |

## How the checks work

- **Titles and descriptions** are read from the rendered HTML (`<title>`
  and `<meta name="description">`), measured in characters, and scanned
  with the separator pattern: a pipe, an em or en dash, or a hyphen that is
  not inside a word.
- **H1 count** counts `<h1>` elements; the first H1's text feeds the
  duplicate-H1 check.
- **Links** are collected from every `<a href>`. Fragments, `mailto:`,
  `tel:`, and external hosts are ignored. Targets are canonicalized, so
  `/about`, `/about/`, and `/about/index.html` are the same page. A target
  that resolves to no audited page and no file on disk is a missing page.
  Links to assets (stylesheets, images, PDFs) are never flagged.
- **Orphans** are pages, other than the home page, with zero inbound links
  from other audited pages. Self-links do not count.
- **Repeated phrasing** compares body copy only: headers, nav, footers,
  sidebars, scripts, styles, and code blocks are excluded, so a shared menu
  never triggers it. Two measures are reported: the share of six-word
  phrases two pages hold in common, and any sentence of ten or more words
  appearing verbatim on more than one page.
- **Forbidden terms** are matched case-insensitively against the page's
  full visible text, title, and description.

## Limits, stated plainly

- The audit reads HTML as served or saved. It does not render JavaScript;
  audit the post-render or built output of a JS-driven site.
- It checks the pages it is given. In URL mode it does not crawl, so an
  incomplete URL list gives incomplete link and orphan results.
- It judges pages against each other and against the rulebook. It does not
  fetch search-engine data, and it cannot say which page *should* rank —
  only which pages are tripping over each other.
