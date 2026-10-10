# -*- coding: utf-8 -*-
"""Consolidate raw/epmc_raw.json + raw/arxiv_raw.json (+ optional extra_web.json)
into literature_database.json (deduped, sorted by date).

Usage:
  python elm_build_db.py [--dir WORKDIR] [--merge]

--merge: merge into existing literature_database.json instead of rebuilding it
         (needed when running year-by-year for retrospective mode).

WARNING: never put non-JSON-serializable helper fields (e.g. Python set) into
record dicts - it truncates the file on json.dump (real incident).
"""
import argparse, json, os, re


def clean_title(t):
    return " ".join(re.sub(r"<[^>]+>", "", t or "").split())


def epmc_record(it, topic):
    ji = it.get("journalInfo") or {}
    journal = (ji.get("journal") or {}).get("title", "")
    auths = (it.get("authorList") or {}).get("author", [])
    names = [a.get("fullName", "") for a in auths]
    pdf_url = None
    for u in (it.get("fullTextUrlList") or {}).get("fullTextUrl", []):
        if u.get("documentStyle") == "pdf" and u.get("availability") in ("Open access", "Open access available", "Free"):
            pdf_url = u.get("url")
            break
        if not pdf_url and u.get("documentStyle") == "pdf":
            pdf_url = u.get("url")
    return {
        "source": "EuropePMC",
        "id": it.get("id"),
        "doi": it.get("doi"),
        "pmid": it.get("pmid"),
        "pmcid": it.get("pmcid"),
        "title": clean_title(it.get("title")),
        "journal": journal or (ji.get("journal", {}) or {}).get("medlineAbbreviation", "") or "Preprint",
        "journal_abbrev": (ji.get("journal", {}) or {}).get("medlineAbbreviation", "") or (journal[:30] if journal else "Preprint"),
        "date": it.get("firstPublicationDate"),
        "authors": names,
        "corresponding_author": names[-1] if names else None,  # biomed heuristic: last author
        "abstract": " ".join(re.sub(r"<[^>]+>", " ", it.get("abstractText") or "").split()),
        "pubtypes": (it.get("pubTypeList") or {}).get("pubType", []),
        "is_oa": it.get("isOpenAccess") == "Y",
        "pdf_url": pdf_url,
        "pdf_downloaded": False,
        "pdf_file": None,
        "pdf_manual": False,
        "topics": [topic],
    }


def arxiv_record(it, topic):
    return {
        "source": "arXiv",
        "id": it["id"].split("/abs/")[-1],
        "doi": None,
        "title": clean_title(it.get("title")),
        "journal": "arXiv preprint",
        "journal_abbrev": "arXiv",
        "date": (it.get("published") or "")[:10],
        "authors": it.get("authors") or [],
        "corresponding_author": (it.get("authors") or [None])[-1],
        "abstract": " ".join((it.get("summary") or "").split()),
        "pubtypes": ["Preprint"],
        "is_oa": True,
        "pdf_url": "https://arxiv.org/pdf/" + it["id"].split("/abs/")[-1],
        "pdf_downloaded": False,
        "pdf_file": None,
        "pdf_manual": False,
        "topics": [topic],
    }


def upsert(records, rec):
    key = (rec.get("doi") or rec.get("title", "")).lower().replace(" ", "")
    if key in records:
        old = records[key]
        for t in rec.get("topics", []):
            if t not in old["topics"]:
                old["topics"].append(t)
        # keep whichever side has more metadata
        for f in ("doi", "pmcid", "abstract", "pdf_url", "corresponding_author"):
            if not old.get(f) and rec.get(f):
                old[f] = rec[f]
    else:
        records[key] = rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()

    base = args.dir
    records = {}
    if args.merge and os.path.exists(os.path.join(base, "literature_database.json")):
        for r in json.load(open(os.path.join(base, "literature_database.json"), encoding="utf-8")):
            upsert(records, r)

    epmc = json.load(open(os.path.join(base, "raw", "epmc_raw.json"), encoding="utf-8"))
    for topic, items in epmc.items():
        for it in items:
            upsert(records, epmc_record(it, topic))

    arxiv_path = os.path.join(base, "raw", "arxiv_raw.json")
    if os.path.exists(arxiv_path):
        for topic, items in json.load(open(arxiv_path, encoding="utf-8")).items():
            for it in items:
                upsert(records, arxiv_record(it, topic))

    # optional manually-found records (source: "Web")
    extra = os.path.join(base, "extra_web.json")
    if os.path.exists(extra):
        for m in json.load(open(extra, encoding="utf-8")):
            m.setdefault("pdf_downloaded", False)
            m.setdefault("pdf_file", None)
            m.setdefault("pdf_manual", False)
            upsert(records, m)

    lst = sorted(records.values(), key=lambda r: r.get("date") or "")
    out = os.path.join(base, "literature_database.json")
    json.dump(lst, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("total unique:", len(lst))
    print("missing DOI:", sum(1 for r in lst if not r.get("doi")))
    for r in lst:
        print(r.get("date"), "|", (r.get("journal_abbrev") or "?")[:22], "|", r["title"][:95])


if __name__ == "__main__":
    main()
