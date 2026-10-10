# -*- coding: utf-8 -*-
"""Match manually downloaded PDFs (e.g. user's Downloads folder) with the
literature DB and COPY them into 01_PDF/ with normalized names.

Matching priority: DOI exact > title word-overlap > filename word-overlap (>= 0.6).
Default is dry-run report. --apply actually copies.

SAFETY: only copies (never moves/deletes) from personal folders.

Usage:
  python elm_import_pdfs.py --downloads "C:/Users/xxx/Downloads" --since 2026-10-09 [--dir WORKDIR] [--apply]
Requires: pypdf
"""
import argparse, datetime, json, os, re, shutil

try:
    from pypdf import PdfReader
except ImportError:
    raise SystemExit("pip install pypdf")

DOI_RE = re.compile(r'10\.\d{4,9}/[^\s"\'<>,;]+')
STOP = set("the a an of for and in on with to from by via using use based study novel new its it this that is are at as".split())


def words(s):
    return set(w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 2)


def overlap(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--since", required=True, help="YYYY-MM-DD, only ingest PDFs modified on/after this date")
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    base = args.dir
    pdf_dir = os.path.join(base, "01_PDF")
    os.makedirs(pdf_dir, exist_ok=True)
    db_path = os.path.join(base, "literature_database.json")
    db = json.load(open(db_path, encoding="utf-8"))

    # index db OUTSIDE record dicts (helper fields must never be serialized)
    db_words = [words(r["title"]) for r in db]
    db_dois = [(r.get("doi") or "").lower().rstrip(".") for r in db]

    cutoff = datetime.datetime.strptime(args.since, "%Y-%m-%d").timestamp()
    cands = []
    for fn in os.listdir(args.downloads):
        if not fn.lower().endswith(".pdf"):
            continue
        p = os.path.join(args.downloads, fn)
        if os.path.getmtime(p) < cutoff:
            continue
        cands.append((fn, p))
    print("candidate PDFs (since", args.since, "):", len(cands))

    results = []
    for fn, p in sorted(cands):
        doi_found, title_guess, first_text = None, None, ""
        try:
            rd = PdfReader(p)
            meta = rd.metadata
            if meta and meta.title and len(meta.title) > 15:
                title_guess = meta.title
            txt = ""
            for pg in rd.pages[:2]:
                txt += (pg.extract_text() or "")[:4000]
            first_text = txt
            for m in DOI_RE.findall(txt):
                m = m.lower().rstrip(".")
                if "creativecommons" in m or "crossmark" in m:
                    continue
                doi_found = m
                break
        except Exception as e:
            print("READ-ERR", fn[:50], str(e)[:60])

        matched, score, how = None, 0.0, ""
        if doi_found:
            for idx, r in enumerate(db):
                d = db_dois[idx]
                if d and (doi_found == d or doi_found.startswith(d) or d.startswith(doi_found)):
                    matched, how, score = r, "doi", 1.0
                    break
        if not matched:
            cands_txt = [title_guess or "", " ".join(first_text.split())[:300]]
            for idx, r in enumerate(db):
                for ct in cands_txt:
                    s = overlap(words(ct), db_words[idx])
                    if s > score:
                        score, matched, how = s, r, "title"
            for idx, r in enumerate(db):
                s = overlap(words(fn.replace(".pdf", "")), db_words[idx])
                if s > score:
                    score, matched, how = s, r, "filename"
            if score < 0.6:
                matched, how = None, "nomatch"

        if matched:
            print(f"OK  [{how}:{score:.2f}] {fn[:58]}")
            print(f"     -> {matched.get('normalized_name') or matched['title'][:70]}")
        else:
            print(f"??  [NO-MATCH(doi={doi_found})] {fn[:58]}")
            if title_guess:
                print("     meta-title:", title_guess[:80])
        results.append((fn, p, matched, how, score))

    ok = [x for x in results if x[2]]
    print(f"\nmatched: {len(ok)} / {len(results)}")

    if args.apply:
        for fn, p, rec, how, score in ok:
            rec["pdf_manual"] = True
            if rec.get("pdf_downloaded") and rec.get("pdf_file") and os.path.exists(os.path.join(pdf_dir, rec["pdf_file"])):
                continue
            name = rec.get("normalized_name") or re.sub(r"\s+", "_", rec["title"])[:80]
            dst_name = re.sub(r'[<>:"/\\|?*]', "_", name) + ".pdf"
            dst = os.path.join(pdf_dir, dst_name)
            if not os.path.exists(dst):
                shutil.copy2(p, dst)   # COPY, never move
            rec["pdf_file"] = dst_name
            rec["pdf_downloaded"] = True
        json.dump(db, open(db_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("applied: copied to 01_PDF/, DB updated")
        print("DB records still without PDF:", sum(1 for r in db if not r.get("pdf_downloaded")))


if __name__ == "__main__":
    main()
