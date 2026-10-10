# -*- coding: utf-8 -*-
"""Fill missing DOIs + repair bad ones / wrong journal metadata.

Priority chain (each rule = a real lesson):
  1) arXiv records  -> 10.48550/arXiv.<id> (standard DOI, always exists)
  2) CrossRef query.bibliographic title match; accept if word-set Jaccard >= 0.75;
     on 429 back off 8/16/24 s. Also corrects journal / journal_abbrev on hit.
  3) PMC page <meta name="citation_doi"> (authoritative when title truncated or
     preprint DOI wrong)
  4) strip pseudo-DOIs: trailing '.s001' (supplementary material);
     reject 10.2139/ssrn.* (preprint DOI - use the formal journal DOI instead)

Usage:
  python elm_fix_dois.py [--dir WORKDIR]
"""
import argparse, json, os, re, ssl, time, urllib.parse, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "ELM-literature-agent/1.0 (mailto:research@example.com)"}

STOP = set("the a an of for and in on with to from by via using use based study novel new its it this that is are at as".split())


def words(s):
    return set(w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 2)


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def fetch(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=H)
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 8 * (i + 1)
                print("  429 rate-limited, backoff", wait, "s")
                time.sleep(wait)
                continue
            print("  HTTP", e.code, str(e)[:60])
            time.sleep(3 * (i + 1))
        except Exception as e:
            print("  retry", i + 1, str(e)[:60])
            time.sleep(3 * (i + 1))
    return None


def crossref_lookup(title):
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": "3"})
    raw = fetch("https://api.crossref.org/works?" + q)
    if not raw:
        return None
    try:
        items = json.loads(raw.decode("utf-8"))["message"]["items"]
    except Exception:
        return None
    tw = words(title)
    best = None
    for it in items:
        t = " ".join(it.get("title") or [])
        s = jaccard(tw, words(t))
        if best is None or s > best[0]:
            best = (s, it)
    if best and best[0] >= 0.75:
        return best[1]
    return None


def clean_doi(d):
    if not d:
        return d
    d = d.strip().rstrip(".")
    if d.endswith(".s001"):          # supplementary-material DOI
        d = d[:-5]
    return d


def is_bad_doi(d):
    return bool(d) and (d.lower().startswith("10.2139/ssrn") or d.lower().endswith(".s001"))


def pmc_doi(pmcid):
    raw = fetch(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/")
    if not raw:
        return None
    html = raw.decode("utf-8", "ignore")
    m = re.search(r'<meta[^>]+name="citation_doi"[^>]+content="([^"]+)"', html)
    if not m:
        m = re.search(r'<meta[^>]+content="([^"]+)"[^>]+name="citation_doi"', html)
    return clean_doi(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    args = ap.parse_args()
    db_path = os.path.join(args.dir, "literature_database.json")
    db = json.load(open(db_path, encoding="utf-8"))

    for r in db:
        doi = r.get("doi")

        # rule 4: pseudo-DOIs
        if is_bad_doi(doi):
            print("drop pseudo-DOI:", doi, "|", r["title"][:70])
            r["doi"] = doi = None

        # rule 1: arXiv standard DOI
        if not doi and r.get("source") == "arXiv":
            r["doi"] = "10.48550/arXiv." + r.get("id", "")
            print("arXiv DOI ->", r["doi"])
            continue

        if doi:
            continue

        # rule 2: CrossRef title match
        it = crossref_lookup(r["title"])
        if it:
            d = clean_doi((it.get("DOI") or "").lower())
            if d and not is_bad_doi(d):
                r["doi"] = d
                ja = (it.get("container-title") or [""])
                if ja and ja[0]:
                    r["journal"] = ja[0]
                    r["journal_abbrev"] = (it.get("short-container-title") or ja)[0][:30]
                print("CROSSREF ->", d, "|", (r.get("journal") or "")[:40])
                continue

        # rule 3: PMC meta
        if r.get("pmcid"):
            d = pmc_doi(r["pmcid"])
            if d:
                r["doi"] = d
                print("PMC meta ->", d, "|", r["title"][:60])
                continue

        print("STILL MISSING:", r["title"][:90])

    json.dump(db, open(db_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    miss = sum(1 for r in db if not r.get("doi"))
    print(f"done. missing DOI: {miss} / {len(db)}")
    if miss:
        print("keep the original English titles in the checklist for manual retrieval - never invent a DOI.")


if __name__ == "__main__":
    main()
