#!/usr/bin/env python3
"""Fixture tests for PageyMcPageface.

Two fixture sites live under fixtures/:

  clean/   passes every check, old and new, exit 0
  broken/  violates each new check on purpose, exit 1, and the report must
           name every expected finding

Run: python3 tests/run_tests.py
Exit 0 when every assertion holds, 1 otherwise. Standard library only.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "page_audit.py")
CLEAN = os.path.join(HERE, "fixtures", "clean")
BROKEN = os.path.join(HERE, "fixtures", "broken")

failures = []


def run(target, *extra):
    return subprocess.run([sys.executable, SCRIPT, target, *extra],
                          capture_output=True, text=True)


def expect(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


# --- clean fixture: nothing may fire -------------------------------------
r = run(CLEAN)
expect(r.returncode == 0, f"clean fixture exits 0 (got {r.returncode})")
expect("No problems found" in r.stdout, "clean fixture reports no problems")

r = run(CLEAN, "--json")
data = json.loads(r.stdout)
site = data["site"]
expect(site["robots_txt"] is True, "clean fixture: robots.txt detected")
expect(site["llms_txt"] is True, "clean fixture: llms.txt detected")
expect(site["sitemap"] is True and site["sitemap_urls"] == 2,
       "clean fixture: sitemap detected with 2 URLs")
expect(site["indexnow_key_file"] is True,
       "clean fixture: IndexNow key file detected")

# --- broken fixture: every new check must fire ---------------------------
r = run(BROKEN)
out = r.stdout
expect(r.returncode == 1, f"broken fixture exits 1 (got {r.returncode})")
expect("Structured data" in out and "no JSON-LD structured data block" in out,
       "fires: page with no JSON-LD block")
expect("is not valid JSON" in out,
       "fires: JSON-LD block that is not valid JSON")
expect("Canonical" in out and "no canonical link" in out,
       "fires: page with no canonical link")
expect("no og:title meta tag" in out and "no og:description meta tag" in out,
       "fires: missing og:title and og:description")
expect("Images" in out and "no alt attribute" in out,
       "fires: image with no alt attribute")
expect("sitemap lists /ghost/, which is not in the site tree" in out,
       "fires: sitemap entry pointing at a page that does not exist")
expect("/bad-json/: built page is not listed in the sitemap" in out,
       "fires: built page missing from the sitemap")
expect("robots.txt is missing from the site root" in out,
       "fires: missing robots.txt")
expect("llms.txt is missing from the site root" in out,
       "fires: missing llms.txt")

r = run(BROKEN, "--json")
site = json.loads(r.stdout)["site"]
expect(site["indexnow_key_file"] is False,
       "broken fixture: no IndexNow key file detected (detection only, not a problem)")
expect(not any(p["section"] == "IndexNow" for p in json.loads(r.stdout)["problems"]),
       "IndexNow absence is never reported as a problem")

print()
if failures:
    print(f"{len(failures)} assertion(s) failed")
    sys.exit(1)
print("All assertions passed.")
