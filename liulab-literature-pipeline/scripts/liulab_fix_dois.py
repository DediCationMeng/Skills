#!/usr/bin/env python3
"""
LiuLab Pipeline - DOI Completer (CrossRef + PMC + arXiv fallback)
Usage: python liulab_fix_dois.py --dir .
"""
import argparse, json, os, re, ssl, sys, time, urllib.request, urllib.parse

try:
    _ctx = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _ctx

CROSSREF_URL = "https://api.crossref.org/works"

def normalize_title(title):
    return set(re.sub(r'[^\w\s]', '', title.lower()).split())

def jaccard(s1, s2):
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)

def crossref_lookup(title, retries=3):
    params = urllib.parse.urlencode({"query.bibliographic": title, "rows": 3})
    url = f"{CROSSREF_URL}?{params}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LiuLabPipeline/1.0 (mailto:lab@example.com)"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            items = data.get("message", {}).get("items", [])
            title_norm = normalize_title(title)
            best = None
            best_score = 0.0
            for item in items:
                t = item.get("title", [""])[0]
                score = jaccard(title_norm, normalize_title(t))
                if score > best_score:
                    best_score = score
                    best = item
            if best and best_score >= 0.75:
                doi = best.get("DOI", "")
                journal = best.get("container-title", [""])[0]
                return doi, journal
            return None, None
        except Exception as e:
            if "429" in str(e):
                wait = [8, 16, 24][min(attempt, 2)]
                print(f"  429 rate limit, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                return None, None
    return None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()

    db_path = os.path.join(args.dir, "literature_database.json")
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data if isinstance(data, list) else data.get("records", data.get("papers", []))

    fixed, missing = 0, 0
    for rec in records:
        doi = rec.get("doi", "").strip()
        # Skip if DOI already present and valid
        if doi and not doi.endswith(".s001") and "ssrn" not in doi:
            continue

        title = rec.get("title", "")
        source = rec.get("source", "")

        # Rule 1: arXiv -> standard DOI
        if source == "arXiv" or "arxiv" in rec.get("id", "").lower():
            arxiv_id = rec.get("id", "").replace("arXiv:", "").replace("arxiv:", "")
            if arxiv_id:
                rec["doi"] = f"10.48550/arXiv.{arxiv_id}"
                fixed += 1
                continue

        # Rule 2: CrossRef lookup
        print(f"Looking up: {title[:60]}...", file=sys.stderr)
        cf_doi, cf_journal = crossref_lookup(title)
        if cf_doi:
            rec["doi"] = cf_doi
            if cf_journal:
                rec["journal"] = cf_journal
            fixed += 1
        else:
            missing += 1

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"DOI fixed: {fixed} | Still missing: {missing}")
    print(f"Missing rate: {missing/len(records)*100:.1f}% (target: 0%)")

if __name__ == "__main__":
    main()
