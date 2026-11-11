# PageyMcPageface — Agensi listing copy

**Product image:** `pagey-mcpageface-doodle.webp` (full-color mascot)

---

## Product title

PageyMcPageface — Whole-Site Page Hygiene Audit for Any Static Site

## One-line pitch

Every page on your site, checked against one rulebook: titles, descriptions, headings, dead links, orphaned pages, pages saying the same thing twice, and the machine-readable layer (structured data, canonicals, sitemap, llms.txt) that search and AI answer engines read first.

## Full description

The people voted, the name stuck, and the audit is deadly serious.

Sites rarely lose search traffic through one big failure. They leak it through a hundred small ones: a title padded with pipes until it clips, the same description pasted onto twelve pages, a good page that nothing anywhere links to, two pages saying the same thing in the same words until a search engine treats them as one. Each leak is small. Together they are the difference between a site that gets found and a site that gets skipped.

PageyMcPageface is an agent skill that audits **every page on a static site** against a fixed rulebook and reports each violation with the page, the rule, and the evidence:

- **Titles** measured at 50–60 characters, **meta descriptions** at 140–160 — long enough to say something, short enough to survive a results page uncut
- **Separators banned** in titles and descriptions: no pipes, no dashes standing in for words (hyphens inside a word are fine)
- **No duplicates**: no two pages may share a title, a description, or an H1
- **Exactly one H1 per page** — never zero, never three
- **No internal links to missing pages**
- **No orphaned pages**: every page must be reachable by links from other pages, or it may as well not exist
- **No repeated phrasing**: any two pages sharing more than 15% of their six-word phrases get flagged, and no sentence of ten words or more may appear on two pages
- **Structured data that parses**: every page carries at least one JSON-LD block, and every block is actually parsed as JSON, so a trailing comma cannot silently void your schema
- **A canonical link on every page**, and **og:title plus og:description** on every page
- **Alt text on every image**: every `<img>` carries an `alt` attribute
- **A sitemap that matches the tree**: sitemap.xml exists or is named in robots.txt, every entry resolves to a real page or file, and every built page is listed
- **Discovery files in place**: robots.txt and llms.txt at the root; an IndexNow key file is detected and reported (detection only, nothing is ever submitted)
- **Optional forbidden-terms check**: hand it a former brand name or a competitor's and it sweeps every page for them

That machine-readable layer is the surface search engines and AI answer engines (AEO, AIO, GEO) read first. Pagey verifies it is present and sound; it does not promise placement in any engine's answers, and no honest tool can. And it is fast by measurement, not by adjective: the full audit, every check switched on, ran against the author's own 101-page site in about 1.1 seconds.

It runs anywhere an agent runs. Point it at a build output folder (Hugo, Jekyll, Astro, Eleventy, a hand-rolled generator, exported WordPress), a folder of HTML files, or a list of live URLs. It reads the rendered HTML, ignores your nav and footer when judging phrasing, and exits nonzero when it finds problems, so it drops straight into a build pipeline as a release gate.

Every threshold is a flag. If your house style allows 65-character titles, set it once and the audit enforces your rules, not ours.

### What you get

- `SKILL.md` — the skill itself: the rulebook, when to run it, the six-step audit workflow, and full instructions your agent follows, including "fix at the source, never in the built output" and how to report results
- `scripts/page_audit.py` — the complete audit as a single Python script, standard library only, nothing to install, with human-readable or JSON output
- `tests/` — fixture sites (one clean, one deliberately broken) and a test runner, so every check in the rulebook is proven, not just claimed

### Requirements

Python 3.9+. Works with Claude Code, Codex, Cursor, and any agent that can read a SKILL.md and run a script. No API keys, no accounts, no network calls in directory mode — your site's files never leave your machine.

## What's inside

- `SKILL.md` — rulebook, workflow, interpretation guide
- `scripts/page_audit.py` — the audit script (stdlib-only Python, ~530 lines)
- `tests/` — fixture sites and the test runner
- `README.md` — quick start and example output
- `pagey-mcpageface-doodle.webp` — the mascot, because every serious audit tool deserves one

## Suggested price

**$24** — mid-band for a single-purpose skill: cheap enough to be an impulse buy next to one hour of SEO consulting, priced like a tool rather than a toy because it gates releases, not just reports once.
