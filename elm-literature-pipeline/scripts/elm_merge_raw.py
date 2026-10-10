# -*- coding: utf-8 -*-
"""Upsert SELECTED topics from raw/epmc_raw.json into literature_database_all.json.

Unlike elm_build_db.py (full rebuild), this preserves manual fixes already in the
database (e.g. reclassified pubtypes, Web-added records) and merges new raw topics.

Usage:
  python elm_merge_raw.py --dir WORKDIR --topics FUNGAL YEAST LIVINGFORMS
Then: python elm_filter_journals.py --dir WORKDIR --stage final
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elm_build_db import epmc_record


def upsert(records, rec):
    key = (rec.get("doi") or rec.get("title", "")).lower().replace(" ", "")
    if key in records:
        old = records[key]
        for t in rec.get("topics", []):
            if t not in old["topics"]:
                old["topics"].append(t)
        for f in ("doi", "pmcid", "abstract", "pdf_url", "corresponding_author"):
            if not old.get(f) and rec.get(f):
                old[f] = rec[f]
    else:
        records[key] = rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--topics", nargs="+", required=True)
    args = ap.parse_args()

    raw = json.load(open(os.path.join(args.dir, "raw", "epmc_raw.json"), encoding="utf-8"))
    all_path = os.path.join(args.dir, "literature_database_all.json")
    db = json.load(open(all_path, encoding="utf-8"))

    records = {}
    for r in db:
        upsert(records, r)

    before = len(records)
    added = 0
    for topic in args.topics:
        for it in raw.get(topic, []):
            key_before = set(records.keys())
            upsert(records, epmc_record(it, topic))
            if set(records.keys()) - key_before:
                added += 1
    out = sorted(records.values(), key=lambda r: r.get("date") or "")
    json.dump(out, open(all_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"all-db: {before} -> {len(out)} (new records: {added})")


if __name__ == "__main__":
    main()
