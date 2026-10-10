# -*- coding: utf-8 -*-
"""Fetch specific papers by DOI from EuropePMC (with CrossRef fallback) and MERGE
into literature_database_all.json (used for Web-found 补漏 records).

Usage:
  python elm_fetch_by_doi.py --dir WORKDIR --dois 10.x/a 10.x/b ...
Then re-run: python elm_filter_journals.py --dir WORKDIR --stage final
"""
import argparse, json, os, ssl, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elm_build_db import epmc_record  # reuse native record builder

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}


def fetch_json(url, tries=3):
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=45, context=ctx).read().decode("utf-8"))
        except Exception as e:
            print("  retry", i + 1, str(e)[:60]); time.sleep(3 * (i + 1))
    return None


def crossref_record(doi):
    d = fetch_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if not d:
        return None
    m = d["message"]
    au = [(a.get("given", "") + " " + a.get("family", "")).strip() for a in m.get("author", [])]
    parts = (m.get("published", {}).get("date-parts") or [[None]])[0]
    date = "-".join(f"{p:02d}" for p in parts) if parts and parts[0] else None
    jt = " ".join(m.get("container-title") or []) or "Unknown"
    ja = " ".join(m.get("short-container-title") or []) or jt[:30]
    return {
        "source": "Web", "id": doi, "doi": doi.lower(), "pmid": None, "pmcid": None,
        "title": " ".join(m.get("title") or []), "journal": jt, "journal_abbrev": ja,
        "date": date, "authors": au, "corresponding_author": au[-1] if au else None,
        "abstract": "", "pubtypes": ["Review"] if "review" in jt.lower() else ["Journal Article"],
        "is_oa": False, "pdf_url": None,
        "pdf_downloaded": False, "pdf_file": None, "pdf_manual": False,
        "topics": ["Web补漏"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--dois", nargs="+", required=True)
    args = ap.parse_args()

    all_path = os.path.join(args.dir, "literature_database_all.json")
    db = json.load(open(all_path, encoding="utf-8"))
    have = {(r.get("doi") or "").lower() for r in db}

    for doi in args.dois:
        if doi.lower() in have:
            print("already in db:", doi); continue
        rec = None
        d = fetch_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" +
                       urllib.parse.urlencode({"query": f'DOI:"{doi}"', "format": "json",
                                               "pageSize": "1", "resultType": "core"}))
        res = (d or {}).get("resultList", {}).get("result", [])
        if res:
            rec = epmc_record(res[0], "Web补漏")
            rec["source"] = "Web"
        if not rec:
            rec = crossref_record(doi)
        if not rec:
            print("FAILED:", doi); continue
        rec["doi"] = (rec.get("doi") or doi).lower()
        db.append(rec)
        have.add(rec["doi"])
        print("added:", rec["doi"], "|", (rec.get("journal_abbrev") or "")[:22], "|",
              rec["title"][:70], "| pubtypes:", rec.get("pubtypes"))
        time.sleep(1)

    json.dump(db, open(all_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("all-db now:", len(db))


if __name__ == "__main__":
    main()
